---
title: "A Debate Swarm on a 270M Model"
date: 2026-07-16 12:00:00 -0300
author: paolo
layout: post
permalink: /2026/07/16/a-debate-swarm-on-a-270m-model/
categories:
  - en-US
tags:
  - machine-learning
  - llm
  - fine-tuning
  - apple-silicon
  - agents
  - python
---

A single language model asked to weigh a decision gives you one answer, and it is usually the averaged, cautious, everyone-is-a-little-right answer. You get more signal by making several models argue: give each one a fixed, biased role, let them analyze the same decision independently, then reconcile the conclusions without smoothing the disagreement away. That pattern is normally run on a big model behind an API. This post puts the whole thing on a 270M model that runs offline on a Mac, and the trick that makes it work is to stop asking the small model to be smart and start asking it to be reliable at four narrow moves.

## The swarm, in four moves

The pipeline has four jobs. An orchestrator reads the decision and invents three to five expert roles whose interests genuinely conflict, not complement: the one who only cares about money, the one who only cares about the user, the one who only cares about technical risk. The experts then analyze the decision in parallel, each pushed to argue its own angle to the limit and forbidden from being balanced. A devil's advocate reads all of the opinions and attacks whatever they agree on, looking for the shared assumption nobody checked. Finally a merge step reconciles everything into a verdict, keeping the conflicts visible instead of averaging them into mush.

None of these four moves needs a genius. Each one needs a specific shape. The orchestrator has to emit a clean JSON array of roles. An expert has to produce a verdict, two or three arguments, and one risk. The merge has to hit its sections and refuse to average. On a 32B model you get that shape for free from a paragraph of instructions. On a 270M model you do not, and that gap is the whole problem to solve.

## Why a tiny model can do the narrow version

The reason this is even plausible is that format adherence, not reasoning, is most of the battle here. A 270M instruct model already has opinions about pricing and hiring and technical debt. What it lacks is the discipline to always return valid role JSON, to always structure an expert opinion the same way, to write a merge that names conflicts instead of hedging. Out of the box it does these things maybe half the time. Fine-tuning on examples of exactly these moves pushes that reliability up to where a downstream pipeline can actually depend on it.

So the target is not a cleverer model. It is a model that does the four moves in the right shape every time, cheaply, on the local machine, with no network. That is a narrow, well-specified task, which is exactly the regime where a small fine-tuned model earns its place.

## Synthetic data by running the swarm against a teacher

The training data is generated, not written. I take a strong teacher model and run the real swarm against it on a spread of decision topics: SaaS pricing changes, remote-work policies, build-versus-buy calls, product sunsets, security trade-offs. For each topic the teacher plays orchestrator, then every expert, then the devil's advocate, then the merge. Every one of those turns is recorded as a training example: the exact system and user prompt the student will see at run time, paired with the teacher's answer as the target.

The teacher here was a large reasoning model served locally. One practical note that saved the whole run: its thinking mode was eating the entire token budget before it emitted any content, so a simple role-planning call took fifteen seconds and sometimes returned nothing at all. Turning thinking off dropped that to six seconds and produced clean, complete JSON. For imitation data you want the answer, not the scratch work.

The examples that come out are good. The roles genuinely conflict, a CFO against a head of HR against a facilities lead against an IT engineer on the same office-lease question, and the merges name the trade-offs instead of splitting the difference. That quality is what the student copies.

```python
# one topic -> up to seven training examples (orchestrator, experts, devil, merge)
roles = ask_json(ORCHESTRATOR_SYSTEM, orchestrator_user(task))     # strict JSON array
opinions = [ {"role": r["name"],
              "opinion": ask(EXPERT_SYSTEM.format(**r), expert_user(task))}
             for r in roles ]
devil = ask(DEVIL_SYSTEM, devil_user(task, opinions))
merge = ask(MERGE_SYSTEM, merge_user(task, opinions + [{"role": "Devil's advocate",
                                                        "opinion": devil}]))
```

## The fine-tune, and the memory wall I hit

The base is `google/gemma-3-270m-it`. I train a LoRA adapter over the attention and MLP projections, which is 7.6M trainable parameters, about 2.75% of the model. The loss is completion-only: the long system and user prompts are masked out, so the model is supervised on producing the moves, not on echoing the instructions back.

The first training run died on an out-of-memory error, and the cause is worth knowing because it is specific to this model family. Gemma-3 has a 262k-token vocabulary. The logits tensor at the language-model head is batch times sequence-length times vocabulary, and at a batch of four with long merge examples that single tensor is several gigabytes before you count the backward pass. The model is tiny but its output layer is enormous. The fix is not exotic: batch size one, gradient accumulation to keep the effective batch reasonable, gradient checkpointing, and a shorter maximum sequence length. Peak memory drops back under the budget and the 270M model trains in minutes.

```python
lora = LoraConfig(r=32, lora_alpha=64, lora_dropout=0.05, task_type="CAUSAL_LM",
    target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"])
model = get_peft_model(model, lora)
model.gradient_checkpointing_enable(); model.enable_input_require_grads()
# bs=1, grad-accum=16: the 262k-vocab logits tensor, not the weights, sets peak memory
```

## Onto the Mac

Training happens on a GPU box; running happens on the laptop. I merge the adapter back into the base weights, pull the fp16 model over, and quantize it with MLX, the native runtime on Apple silicon. The quantized model serves every swarm call locally, so the orchestrator, the five experts, the devil's advocate, and the merge all run with no network at all.

My first instinct was to go straight to 4-bit, because the model is already tiny and the smaller file is nicer to carry around. That instinct cost me a day, and the reason is the next section.

## The part where it broke

The training numbers looked fine and the fp16 model behaved, so I quantized to 4-bit, ran the eval, and got a result that was barely better than the base model. That did not match what I had seen on the GPU. So I dumped the actual generations and read them, which is the step I should always do first and often skip.

They started correct and then fell apart. An expert opinion would open with a clean verdict and two good bullets, then repeat one sentence twenty times. A merge would name a real conflict, then loop the phrase "a 1-star is a 1-star" until it hit the token limit. Some outputs degenerated into runs of the same token in another script entirely. This is the classic failure mode of a small model under greedy decoding, and 4-bit quantization sharpens it: once the model is a little unsure, the highest-probability next token is whatever it just said, and with no randomness to break the tie it says it again, forever. My strict scorers then failed these outputs, so the real problem was hiding behind a mediocre number.

The first fix is a decoding fix, not a training fix. A repetition penalty over a short context window makes a just-repeated token cheaper to avoid, and a little sampling temperature gives the model an escape from the loop. That alone took the tuned model from 54% to 72% overall, because a lot of the failures were good answers strangled by a loop.

Then the orchestrator got worse, and it took me a while to see why. The orchestrator has to emit a JSON array where every object repeats the same three keys: name, focus, bias. A repetition penalty punishes repeated tokens. So the very mechanism that saved the prose was breaking the JSON, penalizing the second `"name"` and the third `"focus"` until the array collapsed into malformed junk after the first object. The moves do not want the same decoding. The free-text moves need the penalty on; the JSON move needs it off. So the penalty became per-move, and the orchestrator's pass rate jumped the moment I stopped fighting its own format.

That left 4-bit itself. Even with the decoding sorted, the orchestrator was landing valid JSON only about half the time, and reading the failures they were near-misses: a dropped quote, a missing brace, a key spelled slightly wrong. Structured output is exactly where quantization noise hurts most, because one wrong token off a sharp distribution invalidates the whole array. So I re-quantized the same fine-tuned model to 8-bit instead. It is still tiny, 304 MB on disk, nothing on a 24 GB machine. The orchestrator went from near-random to reliable, and the two moves that were already good became perfect. For this task the file-size saving of 4-bit was not worth the reliability it cost.

The last weak spot was the merge, stuck near a third even when the outputs looked right. Same lesson as before: read them. Every failing merge had a correct Agreement section and a correct Conflict section, and no Verdict. The verdict comes last, the merge is the longest move, and my token cap was cutting it off two sentences short. I raised the cap and the merge went to a perfect score. It was never a quality problem, it was a budget problem wearing a quality problem's clothes.

```bash
# 8-bit, not 4-bit: structured output is where quant noise costs the most
python -m mlx_lm convert --hf-path export/merged -q --q-bits 8 \
    --mlx-path export/gemma270-swarm-mlx-int8
python -m swarm.swarm --model mlx:export/gemma270-swarm-mlx-int8 \
    --task "Should we remove the free tier and go fully paid with a 14-day trial?"
```

## Measuring the lift

The claim is reliability, so the metric is reliability. For each held-out move I score whether the output has the required shape: the orchestrator returns a valid JSON array of three to five roles with distinct focuses, an expert has a verdict and at least two arguments and a risk, the merge has its agreement and conflict sections and a real verdict. I run the same held-out prompts through the base model and the fine-tuned model, both at 8-bit, both with the same per-move decoding, and compare the pass rates.

```
format reliability (held-out moves)      base 270M      fine-tuned 270M
  orchestrator (valid role JSON)             36%             82%
  expert (verdict + args + risk)             47%            100%
  devil (attacks the consensus)              32%            100%
  merge (sections, no averaging)             13%            100%
  overall                                    38%             98%
```

Three of the four moves are perfect on the held-out set, and the orchestrator sits at 82%, where its two failures are the genuine limit of a 270M model asked to emit a five-object JSON array in one shot. The base model, doing the same moves off the same prompts, lands under 40%. That gap, 38% to 98%, is the whole point: the base model has the opinions but not the discipline, and the fine-tune buys the discipline.

The substance of the arguments is still thinner than what a 32B model produces, and I am not pretending otherwise. In a real run the roles conflict as intended and the merge keeps the disagreement visible, but the reasoning inside each opinion is shallow and sometimes circles the same idea in different words. What moved is not the intelligence, it is the reliability: the small model stops dropping malformed JSON, stops forgetting the risk line, stops truncating the verdict. Once the shape is dependable, the rest of the swarm can be built on top of it without a network and without a bill.

## Running it

Once the 8-bit model is on disk, the whole thing is one command and no network. Point it at a decision and it prints the roles it invented, then each expert opinion, then the devil's advocate, then the final verdict.

```bash
python swarm.py --model mlx:export/gemma270-swarm-mlx-int8 \
    --task "Should we migrate our monolith to microservices this year?"
```

The task should be an actual decision with a tension in it, the kind of thing where reasonable people would pull in different directions: a pricing change, a build-versus-buy call, a hire, a feature to sunset, a security trade-off against a cost. Phrase it as a yes/no or a which-option question. It is not built for open-ended research prompts; it is built to take a decision and pull it apart from angles that disagree.

The model loads in a second or two and each move is a short generation, so a full five-expert run finishes in wall-clock time you would not mind waiting for on a laptop. Nothing leaves the machine. You can run it on a plane.

If you want the structured output rather than the printed transcript, have `analyze` return the roles, opinions, devil, and verdict and write them to JSON; that form is easier to drop into something else, like a note in your decision log or a comment on the ticket that started the argument.

## What it is good for, and what it is not

The honest use case is not replacing a frontier model for hard analysis. It is having a structured second opinion that runs on device, offline, for free, on decisions where you mostly want the conflicts surfaced rather than a brilliant essay.

It is good at the shape of the disagreement. It reliably tells you where the money argument and the trust argument collide, which risk only one role can see, and where everyone quietly agreed on something they should not have. For a lot of everyday decisions that map is most of the value, and having it on the local machine for free means you will actually run it, on the small calls you would never bother sending to an API.

It is not good at depth. The arguments inside each role are shallow, occasionally circular, and no substitute for a domain expert or a big model on a genuinely hard problem. It will not surface a fact it does not have, and it will sometimes state something with more confidence than it has earned, so read it as a prompt for your own thinking rather than an answer. If the decision is high-stakes or turns on specialized knowledge, this is the thing you run first to lay out the battlefield, not the thing you trust to call the winner.

The general lesson is the one I keep coming back to with small models: do not ask them to be smart, box the task down until being reliable is enough.

## Full code

```python
#!/usr/bin/env python
"""A multi-angle analysis swarm running on a local fine-tuned Gemma-3-270M.

Orchestrator -> parallel independent experts -> devil's advocate -> non-averaging
merge, every call served by an 8-bit MLX model, fully offline on Apple silicon.

    python swarm.py --model mlx:export/gemma270-swarm-mlx-int8 \
        --task "Should we remove the free tier and go fully paid with a 14-day trial?"
"""
import argparse, json
from concurrent.futures import ThreadPoolExecutor
from mlx_lm import load, generate
from mlx_lm.sample_utils import make_sampler, make_logits_processors

ORCHESTRATOR_SYSTEM = """You are the orchestrator of an analytical swarm.
For the task, define 3-5 expert roles that will give maximally DIFFERENT and conflicting
views on the decision. The roles must conflict in their interests, not complement each other.
For each role give: name, focus (what it fixates on), bias (what it overrates).
Reply ONLY with a JSON array, no prose, no markdown fences:
[{"name": "...", "focus": "...", "bias": "..."}, ...]"""

EXPERT_SYSTEM = """You are an expert with the role: {name}.
Your focus: {focus}.
Your bias: {bias}. Do not fight it, it is your value to the analysis.
Analyze the decision STRICTLY from your position. Do not be balanced. Push your angle to the limit.
Give exactly:
- Verdict: for / against / conditional
- Arguments: 2-3 bullets from your angle specifically
- Risk: 1 risk most visible from your position that others will miss
Short and hard, no fluff."""

DEVIL_SYSTEM = """You are the devil's advocate. You are given the experts' opinions.
Your only job: attack their agreement. If they converged, find why they might ALL be wrong at
once: a shared assumption nobody checked, a scenario nobody wanted to consider.
Give exactly:
- Dangerous shared assumption
- Failure scenario where the agreement turns out fatally wrong
- One question the group carefully sidestepped
If they genuinely disagree, name the sharpest unresolved conflict."""

MERGE_SYSTEM = """You are the synthesizer. You are given expert opinions plus a devil's advocate.
Do NOT average them. Produce exactly:
1. Agreement: what they agreed on despite different positions.
2. Conflict: where they directly contradict; name it, say what each side costs.
3. Blind spots: a risk only one raised but that matters.
4. Verdict: for / against / conditional, and under what conditions it flips.
Write densely. Keep disagreement as information."""


class LocalModel:
    def __init__(self, path):
        self.model, self.tok = load(path)

    def chat(self, system, user, temperature=0.7, max_tokens=512, rep_penalty=1.3):
        # rep_penalty stops the small model looping on the free-text moves; set it to 1.0 for
        # the orchestrator, whose JSON keys are meant to repeat.
        prompt = self.tok.apply_chat_template(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            add_generation_prompt=True, tokenize=False)
        return generate(self.model, self.tok, prompt=prompt, max_tokens=max_tokens,
                        sampler=make_sampler(temp=temperature, top_p=0.95),
                        logits_processors=make_logits_processors(
                            repetition_penalty=rep_penalty, repetition_context_size=40),
                        verbose=False).strip()


def roles_from(raw):
    s, e = raw.find("["), raw.rfind("]") + 1
    try:
        arr = json.loads(raw[s:e])
        arr = [r for r in arr if {"name", "focus", "bias"} <= set(r)]
        return arr[:5] or None
    except Exception:
        return None


def analyze(m, task):
    for _ in range(3):
        # rep_penalty off here: the role JSON is supposed to repeat its keys
        roles = roles_from(m.chat(ORCHESTRATOR_SYSTEM, f"Task to analyze:\n{task}",
                                  0.7, 400, rep_penalty=1.0))
        if roles:
            break
    else:
        roles = [{"name": "The Money", "focus": "revenue, margin", "bias": "short-term financials"},
                 {"name": "The User", "focus": "trust, churn", "bias": "user goodwill"},
                 {"name": "The Builder", "focus": "technical risk", "bias": "engineering cost"}]
    for r in roles:
        print(f"  - {r['name']}: {r['focus']}")

    def run_expert(r):
        return {"role": r["name"],
                "opinion": m.chat(EXPERT_SYSTEM.format(**r), f"Decision to analyze:\n{task}", 0.7, 400)}
    with ThreadPoolExecutor(max_workers=len(roles)) as pool:
        opinions = list(pool.map(run_expert, roles))
    for o in opinions:
        print(f"\n[{o['role']}]\n{o['opinion']}")

    block = "\n\n".join(f"### {o['role']}\n{o['opinion']}" for o in opinions)
    devil = m.chat(DEVIL_SYSTEM, f"Decision:\n{task}\n\nSwarm opinions:\n{block}", 0.8, 400)
    print(f"\n[Devil's advocate]\n{devil}")

    allop = opinions + [{"role": "Devil's advocate", "opinion": devil}]
    block2 = "\n\n".join(f"### Expert: {o['role']}\n{o['opinion']}" for o in allop)
    # merge is the longest move and the verdict comes last: give it room or it gets cut off
    verdict = m.chat(MERGE_SYSTEM, f"Decision:\n{task}\n\nExpert opinions:\n{block2}", 0.4, 1400)
    print(f"\n=== FINAL VERDICT ===\n{verdict}")
    return verdict


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)   # mlx:/path/to/int8/model
    ap.add_argument("--task", required=True)
    args = ap.parse_args()
    path = args.model[4:] if args.model.startswith("mlx:") else args.model
    analyze(LocalModel(path), args.task)
```
