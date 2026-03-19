---
title: "Looking for Technosignatures as an Anomaly Detection Problem"
date: 2026-03-19 12:00:00 -0300
author: paolo
layout: post
permalink: /2026/03/19/looking-for-technosignatures-as-anomaly-detection/
categories:
  - en-US
tags:
  - seti
  - astronomy
  - machine-learning
  - radio
  - python
---

SETI is usually described as a search for signals from other civilizations. In data terms, much of the work is less dramatic: reduce a huge number of radio events into a smaller list that deserves human and telescope time.

I modeled that as anomaly detection over synthetic waterfalls. The goal was not to detect aliens. The goal was to test a triage stage.

The script is in:

```text
res/technosignature_anomaly_demo.py
```

I ran it with:

```bash
MPLCONFIGDIR=/tmp/mplconfig \
conda run -n exohunter python res/technosignature_anomaly_demo.py \
  --plot uploads/2026/03/technosignature-anomaly.png \
  --json /tmp/technosignature-anomaly.json
```

## The waterfalls

I generated three kinds of examples:

```text
plain_noise
drifting_narrowband
broadband_burst
```

The narrowband example is the SETI-shaped one:

```python
def drifting_tone(w, start=40, drift=0.12, amp=6.0):
    out = w.copy()
    for t in range(out.shape[1]):
        f = int(round(start + drift * t))
        if 0 <= f < out.shape[0]:
            out[f, t] += amp
    return out
```

I trained an `IsolationForest` only on noise features. The features were intentionally simple: maximum power, high percentile power, spectrum peak, time-series peak, and a few spread measures.

```python
def features(w):
    spectrum = w.mean(axis=1)
    ts = w.mean(axis=0)
    return np.array([
        w.max(),
        np.percentile(w, 99.9),
        spectrum.max(),
        ts.max(),
        np.std(spectrum),
        np.std(ts),
    ])
```

## What the anomaly score did

The run produced:

```json
{
  "scores": {
    "plain_noise": 0.4868812757118387,
    "drifting_narrowband": 0.7147055316736491,
    "broadband_burst": 0.7383421547073113
  },
  "ranked": [
    "broadband_burst",
    "drifting_narrowband",
    "plain_noise"
  ]
}
```

<figure class="wp-block-image"><img src="{{ site.baseurl }}/uploads/2026/03/technosignature-anomaly.png" alt="Synthetic SETI-like waterfalls ranked by anomaly score" /><figcaption>The anomaly detector ranked both the broadband burst and drifting narrowband signal above plain noise. That is useful triage, not a discovery claim.</figcaption></figure>

The ranking makes sense. Both injected signals look unlike the noise training set. The broadband burst scored slightly higher than the drifting tone because these features are blunt and reward strong time-domain structure.

## Why this is still useful

An anomaly detector does not say "technosignature." It says "not like the background I learned." That is a much safer claim.

The next stage needs context:

```text
sky position
observing cadence
on/off-source status
known satellites and transmitters
receiver health
RFI masks
whether the event repeats
```

This connects directly to the Voyager post: a signal can be real, bright, narrowband, and still be a known transmitter. The anomaly score is a filter. The engineering system after the score decides whether the candidate survives.

## What this is not

This is not a SETI search pipeline and not a substitute for turboSETI, Doppler drift searches, multibeam checks, or re-observation. It is a small anomaly-ranking experiment.

The useful part is the discipline: the model reduces the pile, but every high-score event still needs metadata, provenance, and a rejection path.

