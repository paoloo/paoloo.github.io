---
title: "A Retrieval System Over the Technosignature Literature"
date: 2026-08-21 12:00:00 -0300
author: paolo
layout: post
permalink: /2026/08/21/a-rag-over-the-technosignature-literature/
categories:
  - en-US
tags:
  - seti
  - rag
  - nlp
  - astronomy
  - python
---

SETI has a literature problem that looks nothing like a signal-processing
problem. There are thousands of papers scattered across decades of radio,
optical, and infrared technosignature work, filed under inconsistent
terminology, split between full text, abstract-only records, and bare
metadata depending on what NASA ADS could recover. Answering something as
plain as "what drift-rate limits have been used for narrowband searches at
the Green Bank Telescope" means either remembering the right paper or
reading through a pile of PDFs by hand.

That is the problem [technosig-rag](https://github.com/paoloo/technosig-rag)
is built to solve. It is a local, evidence-first retrieval-augmented
generation system over the ADS technosignature corpus: it collects the
papers, recovers accessible PDFs, parses and chunks them, embeds and stores
the chunks in a vector database, and answers research questions with inline
citations back to the source records.

## Where the corpus comes from

Everything starts from one ADS query:

```text
abs:(technosignature OR "technological signature" OR "extraterrestrial intelligence")
OR title:(technosignature OR SETI)
OR keyword:(technosignature OR SETI)
```

The deployed snapshot holds 2,477 ADS records and 47,120 searchable chunks.
Of those records, 838 have a recovered PDF, 676 have full-text access, 1,485
are represented only by an abstract, and 316 are metadata only, meaning the
record is discoverable by title and bibliographic fields but contributes no
body text to retrieval. Keeping that access level attached to every chunk
matters: an abstract-only record can support a claim the abstract actually
makes, but it cannot support a detail that would only appear in the full
paper. The generation prompt is written to respect that distinction rather
than silently treating every chunk as equally informative.

## How the pipeline fits together

The project is split into restartable stages, each one a directory with a
single job:

```text
retrieval   -> query ADS, download the best available paper copy
parsing     -> convert PDFs and abstracts into normalized markdown
extraction  -> tag facilities, technosignature types, methods, data products
chunking    -> citation-aware passages with stable identifiers
embedding   -> vectors, cached so rebuilds do not repeat work
storage     -> write the corpus into LanceDB
indexing    -> build the vector and full-text indexes
query       -> hybrid retrieval, rerank, generate a cited answer
```

State is persisted after every batch. An interrupted collection or indexing
run resumes where it left off instead of starting over, which matters a lot
when a run touches thousands of PDFs and external APIs that occasionally
time out.

The extraction stage is worth a closer look, because it is the part that
turns free text into structured retrieval metadata without an LLM call. It
is a set of plain regular expressions grouped by category:

```python
PATTERNS = {
 "facilities": {
  "ATA": _p(r"Allen Telescope Array", r"ATA"), "FAST": _p(r"FAST", r"Five-hundred-meter Aperture Spherical Telescope"),
  "GBT": _p(r"Green Bank Telescope", r"GBT"), "MeerKAT": _p(r"MeerKAT"), "VLA": _p(r"Very Large Array", r"VLA"),
  ...
 },
 "technosignatures": {
  "narrowband radio": _p(r"narrow[ -]?band", r"continuous wave"), "broadband pulses": _p(r"broadband pulse", r"impulsive signal"),
  "optical laser": _p(r"optical SETI", r"laser pulse", r"laser emission"), "waste heat": _p(r"waste heat", r"Dyson sphere"),
  ...
 },
 "signal_features": {"Doppler drift": _p(r"Doppler drift", r"drift rate"), "SNR": _p(r"signal[ -]?to[ -]?noise", r"SNR"), ...},
 "methods": {"turboSETI": _p(r"turboSETI"), "setigen": _p(r"setigen"), "BLIMPY": _p(r"BLIMPY"), ...},
 "data_products": {"filterbank": _p(r"filterbank", r"SIGPROC"), "dynamic spectrum": _p(r"dynamic spectr", r"waterfall"), ...},
}

def extract_tags(text: str) -> dict[str, list[str]]:
    return {group: [name for name, pattern in values.items() if pattern.search(text)] for group, values in PATTERNS.items()}
```

Every chunk gets tagged with the facilities, technosignature types, signal
features, methods, and data products it mentions, at chunking time, cheaply
and deterministically. That gives the retriever a `facility=ATA` filter for
free, without asking a model to classify anything.

## Retrieval: hybrid search, not just embeddings

The retrieval step does not rely on vector similarity alone. It runs a dense
semantic search and a lexical full-text search over the same LanceDB table,
then fuses the two rankings with reciprocal rank fusion before reranking and
enforcing per-paper diversity:

```python
def hybrid_search(query: str, k: int | None = None, facility: str | None = None, access_level: str | None = None,
                  rerank_results: bool = True) -> list[dict]:
    k = k or settings.top_k; table = get_table(); fetch_k = max(k*5, settings.rerank_fetch_limit)
    dense = table.search(embed_query(query), vector_column_name="vector").limit(fetch_k)
    lexical = table.search(query, query_type="fts").limit(fetch_k)
    ...
    scores, rows = {}, {}
    for result_list in (dense.to_list(), lexical.to_list()):
        for rank, row in enumerate(result_list):
            cid = row["chunk_id"]; scores[cid] = scores.get(cid, 0.0) + 1.0/(_RRF_K+rank+1); rows[cid] = row
    pool = [rows[cid] for cid in sorted(scores, key=scores.get, reverse=True)[:settings.rerank_pool_size]]
    ranked = rerank(query, pool, min(len(pool), k*2)) if settings.rerank_enabled and rerank_results else pool
    output, per_paper = [], {}
    for row in ranked:
        count = per_paper.get(row["source_id"], 0)
        if count >= settings.per_paper_limit: continue
        row["retrieval_score"] = scores.get(row["chunk_id"], 0.0); output.append(row); per_paper[row["source_id"]] = count+1
        if len(output) >= k: break
    return output
```

The dense search catches paraphrase and terminology drift, "technosignature"
versus "biosignature-adjacent artifact" versus whatever a given author called
it that decade. The lexical search catches exact terms that embeddings tend
to blur, like instrument names, bibcodes, or a specific method acronym. RRF
combines both rankings without needing to tune a weighting coefficient
between them. The per-paper limit stops one heavily-chunked paper from
dominating the answer with five near-duplicate passages, which is a real
failure mode once a corpus has papers of very different lengths.

Three models do the retrieval and generation work in the deployed service,
each for one job: `nomic-embed-text` for query embeddings, a dedicated
`Qwen3-Reranker-0.6B` cross-encoder for reranking, and `qwen2.5:14b-instruct`
for answer generation and citation auditing. Splitting reranking out to a
small dedicated model instead of asking the 14B generator to also score
passages cut warm search latency to roughly 0.3 to 0.9 seconds and avoids
loading an 18 GB generative runtime just to rank text.

## Generation: cited, and audited against its own citations

The part I spent the most iteration on is the generation prompt, because a
RAG system over scientific literature has a specific way of failing: it
answers fluently and cites confidently while quietly saying something the
retrieved evidence does not actually support. The system prompt tries to
close that gap directly:

```text
Use only supplied ADS-indexed evidence. Cite every material claim inline as
[ADS:bibcode]. Respect each excerpt's access level: an abstract-only record
cannot support details absent from that abstract. Separate author-stated
findings from your inference. Reconcile disagreements by comparing data,
instrument, frequency range, method, sample, and time period.
```

Every answer goes through a second pass before it is returned: the draft is
audited sentence by sentence against the same excerpts, and any technical
claim without a directly supporting citation in that same sentence is
deleted or downgraded to "the retrieved evidence does not establish this."
A citation living in a neighboring sentence does not count. That audit step
is a second call to the same model, not a separate verifier, but it works
because auditing a fixed draft against fixed evidence is a much narrower
task than composing the answer in the first place.

Gap questions, "what is missing," "what has not been studied," get an even
stricter contract. The system explicitly refuses to treat an absence in an
abstract as evidence that a method or result does not exist anywhere in the
literature, requires every surviving gap candidate to carry a gap type,
supporting evidence, counterevidence, and a confidence label, and runs its
own audit pass that deletes any candidate whose support amounts to "this
paper does not mention X." It is fine, and stated as a fine outcome, for the
system to conclude that no defensible gap is established by the retrieved
excerpts.

## What you can actually ask it

The MCP server exposes five tools, and the shape of them says a lot about
what the system is for:

```text
search_literature            retrieve excerpts and provenance, no synthesis
search_multimodal_literature retrieve text and visually relevant PDF pages
answer_research_question     retrieve and answer with ADS citations
answer_with_visual_retrieval answer from jointly reranked text and page images
explain_rf_data               relate an RF data product to relevant literature
corpus_status                 ingestion counts and processing stages
```

Some concrete questions I use it for:

```text
What observing strategies have been used for ATA technosignature searches?
What drift-rate and SNR thresholds are typical for narrowband CW searches?
What data products result from a turboSETI hit-search pipeline, and what
  are their formats?
Given this candidate description [from another RF pipeline], what published
  work is most relevant to interpreting it?
Where are the gaps in optical SETI coverage relative to radio SETI?
```

That last category, gap questions, is where the stricter contract matters
most, and it is also where a plain RAG setup would be most likely to
hallucinate a confident-sounding "no one has studied X" from a handful of
abstracts that simply did not mention it.

The `explain_rf_data` tool is the one aimed outward rather than at a human
question. It takes a description of an RF data product, generated by
another tool or pipeline, and asks the corpus what published methods and
caveats apply to interpreting it. That is meant to sit next to an actual
signal-processing pipeline as a literature-grounding step, not replace one.

## The multimodal branch

The stable branch is text only. A separate `multimodal` branch adds a
sidecar visual index: rendered PDF pages, embedded with `Qwen3-VL-Embedding-2B`
and jointly reranked against text with `Qwen3-VL-Reranker-2B`, so a query
like "find waterfall plots showing drifting narrowband signals" can retrieve
an actual page image, not just the caption text near it. It runs as a
second container on a separate port, mounts the original text database
read-only, and writes nothing back to it, so rolling back to text-only is
just stopping the second container.

The pilot covered 100 PDFs and 1,594 pages: 111 seconds to render, 359
seconds to embed, 11 seconds to store and index, zero errors. A mixed
10-result query measured 22.7 seconds cold and 8.2 seconds warm on a single
observation. The answer generator still only reads extracted page text, so
the interface is explicit that a returned page image should be inspected
directly before relying on a visual-only detail like a plot shape or a
faint feature. I have not merged this branch into `main` yet. It needs
evaluation against a fixed institutional question set before I trust it as
the default path, not just a working pilot.

## Why this is worth having

None of this replaces reading papers. What it replaces is the search step
that comes before reading papers: given a specific technical question,
which five to ten papers, and which passages inside them, are actually worth
opening. For a corpus this size, spanning facility reports, method papers,
and null-result surveys with inconsistent terminology, that step is where
most of the human time goes.

The design choice I would defend most is treating access level as a
first-class constraint on the answer rather than as corpus metadata that
gets discarded after retrieval. A system that cannot tell you it only saw an
abstract is a system that will eventually state a full-paper-level detail it
never actually retrieved. Keeping that boundary visible in every cited
excerpt, and auditing every generated sentence against it, is what makes me
trust an answer enough to use it as a starting point for a literature
search rather than as a replacement for one.
