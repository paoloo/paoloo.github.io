---
title: "Roman Will Break Our Exoplanet Pipelines"
date: 2026-03-25 12:00:00 -0300
author: paolo
layout: post
permalink: /2026/03/25/roman-will-break-our-exoplanet-pipelines/
categories:
  - en-US
tags:
  - exoplanets
  - astronomy
  - machine-learning
  - python
---

The Nancy Grace Roman Space Telescope is usually discussed in terms of what it may find. I keep thinking about a less glamorous consequence: Roman-scale astronomy will stress the pipelines.

When a survey becomes large enough, the hard problem is not only detection. It is bookkeeping, false positives, cross-matching, vetting, provenance, and making sure the same event can be understood six months later.

I made a small transit-vetting simulation to keep that concrete.

The script is in:

```text
res/roman_pipeline_demo.py
```

I ran it with:

```bash
MPLCONFIGDIR=/tmp/mplconfig \
conda run -n exohunter python res/roman_pipeline_demo.py \
  --plot uploads/2026/03/roman-pipeline.png \
  --json /tmp/roman-pipeline.json
```

## A synthetic candidate

The light curve has stellar variability, white noise, and an injected transit:

```python
def light_curve(rng, period=7.3, depth=0.006, duration=0.18, n=6000):
    t = np.linspace(0, 60, n)
    flux = 1 + 0.002 * np.sin(2 * np.pi * t / 13.0)
    flux += rng.normal(0, 0.0015, n)
    phase = (t % period) / period
    mask = (phase < duration / period) | (phase > 1 - duration / period)
    flux[mask] -= depth
    return t, flux
```

This is not a Roman simulator. It is a small candidate object that lets the rest of the pipeline behave like a real pipeline.

## Detection is only the first row

I used a simple box score over trial periods:

```python
def score_period(t, f, period, duration=0.18):
    phase = (t % period) / period
    mask = phase < duration / period
    return float(np.mean(f[~mask]) - np.mean(f[mask]))
```

The injected period was `7.3 days`. The best grid period came back as:

```text
best period: 7.278969957081545 days
period error: 0.021030042918455116 days
box score: 0.00588619345173369
```

<figure class="wp-block-image"><img src="{{ site.baseurl }}/uploads/2026/03/roman-pipeline.png" alt="Synthetic exoplanet light curve and first-pass period search" /><figcaption>A small transit candidate and the first-pass period search. Finding the dip is only the beginning of the pipeline.</figcaption></figure>

The candidate record I would keep is not only the period:

```json
{
  "target_id": "synthetic-roman-00025",
  "injected_period_days": 7.3,
  "best_period_days": 7.278969957081545,
  "period_error_days": 0.021030042918455116,
  "best_box_score": 0.00588619345173369,
  "odd_even_delta": 0.00042,
  "centroid_shift_sigma": 0.7,
  "secondary_eclipse_score": 1.1,
  "status": "survived_first_vetting"
}
```

The vetting fields matter. A transit-like dip is not automatically a planet. It may be an eclipsing binary, a blend, an instrumental artifact, or a systematic that happens to fold nicely.

## Why Roman changes the scale

Small surveys let humans stay close to the data. Large surveys force discipline. Every threshold, version, cross-match, failed query, and rejected candidate becomes part of the result.

That is why I think Roman will break naive exoplanet pipelines in a productive way. It will push more of the work from clever notebooks into reproducible systems.

For students, this is the main lesson: finding the dip is the start. The astronomy starts when the candidate survives the pipeline and the pipeline can explain itself.

