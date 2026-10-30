---
title: "The Loss Function That Stops a Swarm Piling onto One Target"
date: 2026-10-11 12:00:00 -0300
author: paolo
layout: post
permalink: /2026/10/11/the-loss-function-that-stops-a-swarm-piling-onto-one-target/
math: true
categories:
  - en-US
tags:
  - machine-learning
  - robotics
  - swarms
  - embedded-systems
  - optimization
  - python
---

I ran into a good swarm-control interview question in a short Anduril video.
The setup is compact: a salvo is coming in, a group of autonomous
interceptors has to divide the threats between itself, and the ground link is
jammed. There is no central controller. Each interceptor runs a local neural
network, exchanges short messages with its neighbours, and outputs a
probability that it should engage each threat.

The obvious local policy is a bad one. If every interceptor selects the
closest or easiest target, several of them can pile onto the same missile
while the rest of the salvo goes through. The question asks which loss
function should train the network to avoid that failure.

This post works through the four choices, then builds a small numerical test.
The test is deliberately tiny. I can compare gradient descent with an
exhaustive search, run the same assignment through 200,000 simulated
engagements, and quantize the learned logits to int8. That gives me three
separate checks on the answer before talking about a flight computer.

The complete script is here:

```text
res/swarm_loss_demo.py
```

## The four proposed objectives

Let \(p_{ij}\) be the probability that interceptor \(i\) engages threat
\(j\), and let \(k_{ij}\) be the probability that the interceptor kills that
threat if it engages.

The video gives four choices.

Option A maximizes expected kills but subtracts a penalty when the total
allocation to one threat exceeds one:

$$
\max\; \mathbb{E}[\text{destroyed}]
- \lambda \sum_j \max\left(0, \sum_i p_{ij}-1\right).
$$

Option B tries to make neighbouring interceptors agree:

$$
\min\; \sum_{(i,k)\in\mathrm{links}} \lVert p_i-p_k\rVert^2.
$$

Option C maximizes the probability that every threat is killed by at least
one interceptor:

$$
\max\; \sum_j \left[1-\prod_i(1-p_{ij}k_{ij})\right].
$$

Option D adds the kill probabilities of all interceptor-threat pairs:

$$
\max\; \sum_i\sum_j p_{ij}k_{ij}.
$$

The answer is C. The product is the important part.

## Why the product is there

For one interceptor-threat pair, \(p_{ij}k_{ij}\) is the probability of both
choosing the target and killing it. Its complement,
\(1-p_{ij}k_{ij}\), is the probability that interceptor \(i\) does not kill
threat \(j\).

Assuming those events are conditionally independent across interceptors, the
probability that every interceptor fails against threat \(j\) is

$$
P(\text{threat }j\text{ survives}) = \prod_i(1-p_{ij}k_{ij}).
$$

Take the complement and I get the chance that at least one interceptor kills
it:

$$
P(\text{threat }j\text{ is killed})
=1-\prod_i(1-p_{ij}k_{ij}).
$$

Adding that quantity over threats gives the expected number of distinct
threats destroyed. A threat counts once even if three interceptors hit it.
That is exactly what the mission cares about.

The expression is presented as something to maximize. A training program
normally minimizes a loss, so I use the expected number of survivors:

$$
\mathcal{L}_{\mathrm{survive}}
=\sum_j w_j\prod_i(1-p_{ij}k_{ij}).
$$

The optional \(w_j\) gives a high-priority threat more weight. I set every
weight to one in the experiment below.

There are two assumptions hiding in that compact expression. The kill model
\(k_{ij}\) has to be calibrated well enough to mean something, and the
product assumes conditionally independent failures for a given threat.
Common-mode failures break that assumption. A real system would need a richer
joint model if, for example, two interceptors can fail together because they
share the same sensor error or countermeasure vulnerability.

## Why the other three answers miss the mission

Option A looks reasonable because it explicitly punishes doubling up. The
problem is that redundancy is not always waste. Two independent weapons with
a kill probability of 0.6 give a combined probability of
\(1-(1-0.6)^2=0.84\). A fixed penalty can suppress useful redundancy, and its
behaviour depends on the hand-tuned \(\lambda\). If the expected-destroyed
term is already computed correctly, the penalty is not needed to express the
mission objective.

Option B is a communication regularizer, not an allocation objective.
Neighbours can reach perfect consensus by all choosing the same target. The
loss contains no kill probability and no reward for covering another threat.
Agreement can help a distributed algorithm, but agreement alone does not
tell the swarm what a good plan is.

Option D makes the local/global mistake. It counts successful interceptor
engagements instead of distinct threats. If five interceptors have their best
individual odds against the same easy target, the objective is happy to send
all five there. Five successful hits still remove one threat.

## What the model would look like

The number of interceptors, threats, and radio links changes from scene to
scene. I would use a small graph neural network with shared weights rather
than one large network tied to a fixed formation.

Each interceptor would run the same three-part policy:

```text
local state + visible threat tracks
                |
             encoder
                |
    fixed-size neighbour messages
                |
      1 or 2 message-passing rounds
                |
     one logit per feasible threat
                |
    mask infeasible pairs + softmax
                |
        target probabilities p_ij
```

The local state can include position, velocity, energy, weapon availability,
track quality, relative target geometry, estimated time to intercept, and
the pairwise kill estimate \(k_{ij}\). Relative and normalized quantities are
more useful than memorizing map coordinates.

If an interceptor may select at most one threat, the decoder also produces a
"do nothing" logit. A row-wise softmax then enforces the capacity constraint:

$$
p_{ij}=\frac{\exp(z_{ij}/\tau)}
{\exp(z_{i0}/\tau)+\sum_{\ell\in\mathcal F_i}\exp(z_{i\ell}/\tau)}.
$$

Here \(\mathcal F_i\) is the feasible target set and \(z_{i0}\) is the
no-engagement choice. Impossible intercepts are masked before the softmax.
That matters because a learned penalty is not a dependable way to enforce a
no-fire zone, minimum separation, or physical reachability.

I would train the network offline in a simulator. Each batch would randomize
the salvo geometry, swarm size, sensor noise, track error, kill probabilities,
mesh topology, packet loss, latency, jamming, and component failures. The GNN
produces \(p_{ij}\), the simulator supplies \(k_{ij}\), and backpropagation
minimizes the survival loss. Expert allocations from a conventional solver
can be used for imitation pretraining, but they are not strictly required
because the loss is differentiable.

Long engagements add another complication. An assignment now changes the
geometry and weapon inventory available later. For that case I would first
train on single decision frames, then fine-tune on simulated rollouts with a
cumulative version of the same mission cost. The short-horizon model remains
a useful baseline and a much easier thing to audit.

## A small proof by computation

I wanted a test where the wrong objective fails visibly. The script uses five
interceptors and five threats. Every interceptor has its highest individual
kill probability against threat 0:

```python
KILL = np.array([
    [0.95, 0.80, 0.15, 0.10, 0.10],
    [0.94, 0.78, 0.20, 0.10, 0.10],
    [0.93, 0.15, 0.76, 0.10, 0.10],
    [0.92, 0.10, 0.10, 0.74, 0.20],
    [0.91, 0.10, 0.10, 0.20, 0.72],
])
```

The hard version of option D takes `argmax` on every row. It produces
`[0, 0, 0, 0, 0]`: all five interceptors attack threat 0. The probability of
killing that one target is almost one, but the expected number of distinct
threats destroyed is still only `0.999998488`.

For the training check, I made the assignment logits themselves trainable.
This is not the full GNN. It isolates the loss from the architecture so I can
check the calculus without wondering whether the network was too small. A
softmax turns each row of logits into target probabilities and gradient
descent minimizes expected survivors.

The derivative with respect to one assignment probability is simple. If

$$
S_j=\prod_i(1-p_{ij}k_{ij}),
$$

then

$$
\frac{\partial\mathcal L}{\partial p_{aj}}
=-k_{aj}\frac{S_j}{1-p_{aj}k_{aj}}.
$$

The script passes that derivative through the softmax Jacobian and updates
the logits. The training temperature gradually falls from 1.2 to 0.18 so the
soft probabilities approach the hard `argmax` decision used at inference.

I ran it with:

```bash
MPLCONFIGDIR=/tmp/mplconfig \
/Users/paolo/Workspace/CONDA/envs/core/bin/python \
  res/swarm_loss_demo.py \
  --plot uploads/2026/10/swarm-threat-loss.png \
  --json /tmp/swarm-threat-loss.json
```

The learned assignment was:

```text
[1, 0, 2, 3, 4]
```

Interceptor 0 takes its second-best target, leaving interceptor 1 on threat 0.
The other three spread across threats 2, 3, and 4. The expected number of
distinct kills rises from about `1.000` to `3.960`.

<figure class="wp-block-image"><img src="{{ site.baseurl }}/uploads/2026/10/swarm-threat-loss.png" alt="Training curve for the threat survival loss and comparison of distinct threats destroyed by independent, trained, and exhaustive assignments" /><figcaption>The differentiable survival loss falls during training. The hard assignment learned from it reaches the same expected number of distinct kills as exhaustive search on this small case.</figcaption></figure>

The full result was:

```json
{
  "per_interceptor_assignment_zero_based": [0, 0, 0, 0, 0],
  "trained_assignment_zero_based": [1, 0, 2, 3, 4],
  "exhaustive_assignment_zero_based": [1, 0, 2, 3, 4],
  "int8_assignment_zero_based": [1, 0, 2, 3, 4],
  "expected_destroyed": {
    "per-interceptor": 0.999998488,
    "trained threat loss": 3.96,
    "exhaustive optimum": 3.96
  },
  "training_loss": {
    "start": 3.318586439955509,
    "end": 1.0400000005600245
  },
  "monte_carlo": {
    "mean_destroyed": 3.959565,
    "standard_error": 0.0019876040367045027,
    "trials": 200000
  },
  "trained_matches_exhaustive_score": true,
  "int8_preserves_assignment": true
}
```

There are three checks in those numbers. Exhaustive search tries all
\(5^5=3125\) hard assignments and finds the same one as gradient descent.
The analytic expectation of `3.96` agrees with the Monte Carlo estimate of
`3.959565` within its sampling error. Finally, symmetric int8 quantization of
the logits leaves every `argmax` unchanged in this case.

This does not prove that gradient descent will always find a global optimum,
nor that quantization is harmless for every scene. It proves something
narrower and useful: the implementation of the loss, its gradient, and its
probabilistic interpretation agree on a case where the interceptor-level
objective fails badly.

## Fitting it into a real-time embedded system

Training belongs on a workstation. The flight computer only needs the frozen
forward pass, a short message exchange, and a deterministic decision step.
I would set explicit limits for the maximum candidate threats, maximum mesh
degree, feature width, and number of message-passing rounds. Inputs can be
padded and masked to those limits so memory allocation and loop counts do not
change at runtime.

The embedded model should be shallow, use fixed-size messages, and avoid
global attention. One or two local graph rounds put a hard bound on both
radio traffic and inference time. Shared weights also mean that every
interceptor stores one small model rather than a formation-specific network.

Quantization is worth doing, but the small check above is only a smoke test.
The real workflow is quantization-aware training or a carefully calibrated
post-training conversion, followed by the entire validation suite using the
exact integer kernels on the target processor. Near-tied logits deserve
special attention because one least-significant-bit change can flip a target
choice.

The real-time contract is larger than neural-network latency:

```text
sensor/track update
feature preparation
neighbour message exchange
GNN inference
conflict resolution
safety filter
command handoff
```

Worst-case time for that whole chain must fit the decision deadline. An
average benchmark on a quiet processor is not enough. The test has to include
cache effects, competing tasks, delayed packets, and the largest allowed
graph.

I would also keep hard constraints outside the learned policy. Reachability,
no-fire zones, minimum separation, stale tracks, actuator state, and weapon
availability belong in masks and a small deterministic safety supervisor.
If inference misses its deadline or the mesh disappears, the system needs a
known fallback, such as holding the last valid assignment for a bounded time
or reverting to a conservative local policy.

I would not update weights online in the basic design. Frozen weights are
easier to time, regression-test, version, and audit. Logged operational data
can improve the simulator and train the next version offline, but that new
model should go through the same scenario tests and hardware-in-the-loop
campaign before it reaches an interceptor.

## What the loss solves, and what it does not

The threat-level loss fixes one precise mistake: counting interceptor success
instead of mission success. It gives the learner a reason to spread effort
when another covered threat has diminishing value, while still allowing
redundancy when a second shot materially improves the kill probability.

It does not provide calibrated \(k_{ij}\), solve correlated failures, guarantee
that distributed messages arrive, enforce safety rules, or prove that a
particular neural network meets a deadline. Those remain separate engineering
problems.

That separation is what I like about this question. The correct equation is
not merely a clever product. It draws the system boundary cleanly: the model
proposes a distributed allocation, the loss measures the mission outcome,
the simulator supplies uncertainty, and deterministic embedded code keeps the
result feasible and safe.
