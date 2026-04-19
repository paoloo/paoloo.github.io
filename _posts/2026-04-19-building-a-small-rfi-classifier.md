---
title: "Building a Small RFI Classifier"
date: 2026-04-19 12:00:00 -0300
author: paolo
layout: post
permalink: /2026/04/19/building-a-small-rfi-classifier/
math: true
categories:
  - en-US
tags:
  - python
  - machine-learning
  - radio
  - seti
  - astronomy
---

Radio transient searches produce candidates, not discoveries. A dedispersion pipeline can find a pulse-like event and a matched filter can measure its S/N, but terrestrial interference can trigger both. The next stage has to decide which candidates deserve attention.

I started with a small supervised RFI classifier built from interpretable features. It was deliberately simpler than the beta-VAE in [Killing RFI with a beta-VAE]({{ site.baseurl }}/2026/05/30/killing-rfi-with-a-vae/), because I wanted to inspect the complete classification path before moving to learned representations.

I generated three kinds of candidate waterfalls:

- dispersed astrophysical-like pulses
- broadband impulsive RFI
- persistent narrowband RFI

I extracted features, trained a Random Forest, inspected its errors and tested whether it had learned useful structure or a shortcut from my simulator.

## The distinction I tried to encode

A dispersed pulse follows approximately

$$
\Delta t \propto \mathrm{DM}\,\nu^{-2}.
$$

Broadband impulsive RFI appears at nearly the same time in every channel. Persistent narrowband RFI occupies a small frequency range for much of the observation.

Those differences suggest features:

| Feature | What it measures |
|---|---|
| best-DM gain | Does nonzero dedispersion concentrate the signal? |
| temporal peak | Is there a pulse after dedispersion? |
| spectral occupancy | How much of the band participates? |
| temporal occupancy | How long does bright power persist? |
| modulation index | Is power smooth or concentrated across frequency? |
| zero-DM peak | Is the event strongest with no dispersion? |

These features were not perfect, but I could inspect why the model made a decision.

## The synthetic candidates I generated

```python
import numpy as np

rng = np.random.default_rng(1904)

N_FREQ = 96
N_TIME = 512
DT_MS = 1.0
FREQ_MHZ = np.linspace(1200.0, 1500.0, N_FREQ)
K_DM_MS = 4.148808e6
```

Cold-plasma delay:

```python
def delays_in_samples(dm):
    reference = FREQ_MHZ.max()
    delay_ms = (
        K_DM_MS
        * dm
        * (FREQ_MHZ ** -2 - reference ** -2)
    )
    return np.rint(delay_ms / DT_MS).astype(int)
```

Noise background:

```python
def background():
    channel_gain = rng.normal(1.0, 0.05, size=(N_FREQ, 1))
    noise = rng.normal(0.0, 1.0, size=(N_FREQ, N_TIME))
    return channel_gain * noise
```

Astrophysical-like dispersed pulse:

```python
def dispersed_candidate():
    data = background()
    dm = rng.uniform(80.0, 500.0)
    width = rng.uniform(1.5, 6.0)
    amplitude = rng.uniform(0.8, 2.0)
    arrival = rng.integers(80, 180)
    time = np.arange(N_TIME)

    for channel, delay in enumerate(delays_in_samples(dm)):
        center = arrival + delay
        data[channel] += amplitude * np.exp(
            -0.5 * ((time - center) / width) ** 2
        )

    return data
```

Broadband impulsive RFI:

```python
def broadband_rfi():
    data = background()
    center = rng.integers(80, N_TIME - 80)
    width = rng.uniform(1.0, 8.0)
    amplitude = rng.uniform(0.8, 2.0)
    time = np.arange(N_TIME)
    pulse = amplitude * np.exp(-0.5 * ((time - center) / width) ** 2)

    spectral_shape = rng.uniform(0.7, 1.3, size=(N_FREQ, 1))
    data += spectral_shape * pulse
    return data
```

Persistent narrowband RFI:

```python
def narrowband_rfi():
    data = background()
    first = rng.integers(0, N_FREQ - 8)
    width = rng.integers(1, 8)
    amplitude = rng.uniform(1.0, 3.0)

    data[first:first + width] += amplitude

    if rng.random() < 0.5:
        modulation = 1.0 + 0.4 * np.sin(
            np.linspace(0, rng.uniform(5, 20), N_TIME)
        )
        data[first:first + width] *= modulation

    return data
```

Synthetic data gives us exact labels and unlimited samples. It also creates a dangerous illusion: the simulator defines the world, so a model can perform perfectly while learning artifacts of the simulator.

## Dedispersion helper

```python
def dedisperse(data, dm):
    shifts = delays_in_samples(dm)
    aligned = np.zeros_like(data)

    for channel, shift in enumerate(shifts):
        if shift == 0:
            aligned[channel] = data[channel]
        elif shift < N_TIME:
            aligned[channel, :-shift] = data[channel, shift:]

    return aligned
```

Robust standardization:

```python
def robust_scale(data):
    median = np.median(data)
    mad = np.median(np.abs(data - median))
    sigma = max(1.4826 * mad, 1e-6)
    return (data - median) / sigma
```

## Extract interpretable features

```python
TRIAL_DMS = np.arange(0.0, 551.0, 25.0)


def series_peak_snr(series):
    median = np.median(series)
    mad = np.median(np.abs(series - median))
    sigma = max(1.4826 * mad, 1e-6)
    return float(np.max((series - median) / sigma))


def extract_features(data):
    z = robust_scale(data)

    dm_scores = []
    for dm in TRIAL_DMS:
        series = dedisperse(z, dm).mean(axis=0)
        dm_scores.append(series_peak_snr(series))

    dm_scores = np.asarray(dm_scores)
    best_index = int(np.argmax(dm_scores))
    best_dm = TRIAL_DMS[best_index]
    best_dm_snr = dm_scores[best_index]
    zero_dm_snr = dm_scores[0]

    bright = z > 3.0
    channel_occupancy = np.mean(np.any(bright, axis=1))
    time_occupancy = np.mean(np.any(bright, axis=0))

    spectrum = np.maximum(z, 0.0).mean(axis=1)
    modulation_index = float(
        np.std(spectrum) / (np.mean(spectrum) + 1e-6)
    )

    total_series = z.mean(axis=0)
    temporal_peak = series_peak_snr(total_series)

    return np.array([
        best_dm,
        best_dm_snr,
        best_dm_snr - zero_dm_snr,
        zero_dm_snr,
        channel_occupancy,
        time_occupancy,
        modulation_index,
        temporal_peak,
    ], dtype=np.float32)
```

The best-DM gain was the feature closest to the propagation model. My dispersed events improved when aligned at a nonzero DM, while a broadband impulse was already aligned at DM=0.

## The dataset I built

```python
GENERATORS = {
    "pulse": dispersed_candidate,
    "broadband_rfi": broadband_rfi,
    "narrowband_rfi": narrowband_rfi,
}

FEATURE_NAMES = [
    "best_dm",
    "best_dm_snr",
    "dm_gain",
    "zero_dm_snr",
    "channel_occupancy",
    "time_occupancy",
    "modulation_index",
    "temporal_peak",
]


def make_dataset(samples_per_class):
    features = []
    labels = []

    for label, generator in GENERATORS.items():
        for _ in range(samples_per_class):
            features.append(extract_features(generator()))
            labels.append(label)

    return np.asarray(features), np.asarray(labels)


X, y = make_dataset(samples_per_class=500)
print(X.shape, y.shape)
```

The classes are balanced on purpose. That lets us focus on feature behavior first. Real RFI datasets are severely imbalanced and require different metrics and sampling policies.

## Split before training

```python
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.25,
    random_state=42,
    stratify=y,
)
```

Because every synthetic candidate is independently generated, a random split is acceptable here. With telescope data, split by observing session, beam or time block. Adjacent candidates often share the same RFI event, and random row splitting leaks that event into both sets.

## Train a Random Forest

```python
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier(
    n_estimators=300,
    max_depth=10,
    min_samples_leaf=3,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1,
)

model.fit(X_train, y_train)
```

I used a Random Forest because it handled nonlinear boundaries without feature scaling and exposed feature importances. I treated it as a baseline, not as an automatic production choice.

## Evaluate by class

```python
from sklearn.metrics import classification_report, ConfusionMatrixDisplay
import matplotlib.pyplot as plt

prediction = model.predict(X_test)

print(classification_report(y_test, prediction, digits=3))

ConfusionMatrixDisplay.from_predictions(
    y_test,
    prediction,
    normalize="true",
    cmap="Blues",
)
plt.tight_layout()
plt.savefig("rfi-confusion-matrix.png", dpi=150)
```

Overall accuracy is not enough. Ask:

- How many real pulses are rejected as RFI?
- Which RFI type becomes a pulse candidate?
- Does performance collapse for weak signals?
- Are errors concentrated at low DM?

For this discovery-style pipeline, I treated false negatives as more expensive than false positives. I tuned thresholds for that objective instead of a round accuracy number.

## Probability and triage thresholds

```python
probability = model.predict_proba(X_test)
pulse_column = list(model.classes_).index("pulse")
pulse_probability = probability[:, pulse_column]

for threshold in [0.5, 0.7, 0.9]:
    selected = pulse_probability >= threshold
    recovered = np.mean(selected[y_test == "pulse"])
    contamination = np.mean(y_test[selected] != "pulse") if selected.any() else 0.0

    print(
        f"threshold={threshold:.1f} "
        f"pulse_recall={recovered:.3f} "
        f"selected_contamination={contamination:.3f}"
    )
```

I used the classifier to triage candidates, not to declare discoveries. A high-recall threshold produced a smaller candidate set for later validation stages.

## What the model appeared to learn

```python
order = np.argsort(model.feature_importances_)[::-1]

for index in order:
    print(
        f"{FEATURE_NAMES[index]:20s} "
        f"{model.feature_importances_[index]:.3f}"
    )
```

When `best_dm` dominated, I checked whether the simulator had accidentally made every pulse high-DM and every RFI exactly zero-DM. Real RFI can mimic dispersion, and low-DM astrophysical sources exist. I used feature importance as a prompt for another experiment, not as an explanation by itself.

## Shortcut test: change the simulator

I created a harder RFI class with a curved sweep:

```python
def swept_rfi():
    data = background()
    start = rng.integers(80, 180)
    slope = rng.uniform(-0.8, 0.8)
    width = rng.uniform(1.0, 4.0)
    amplitude = rng.uniform(0.8, 2.0)
    time = np.arange(N_TIME)

    for channel in range(N_FREQ):
        center = start + slope * channel
        data[channel] += amplitude * np.exp(
            -0.5 * ((time - center) / width) ** 2
        )

    return data
```

Before retraining, I passed 200 swept examples through the existing model:

```python
X_shift = np.asarray([
    extract_features(swept_rfi())
    for _ in range(200)
])

shift_prediction = model.predict(X_shift)
print(np.unique(shift_prediction, return_counts=True))
```

This is a distribution-shift test. A model that looked excellent on the original test set may call swept RFI astrophysical because that morphology did not exist in training.

## Moving from simulation to telescope data

For a telescope dataset, I would keep:

- candidates from different observing days
- multiple pointings and frequency bands
- human-reviewed labels with an uncertainty field
- injected synthetic pulses inside real backgrounds
- metadata about beam, antenna, backend and observing conditions
- groups that keep related candidates in one split

I used injection recovery as the sensitivity measurement: pulses covered a range of DM, width, spectral index and S/N, and I checked which ones survived the complete pipeline. Bright, clean examples alone gave an unrealistically easy test.

## What I recorded for each run

```text
dataset version
observation IDs
label policy
feature definitions
grouped split key
random seed
model parameters
class counts
confusion matrix
threshold and pulse recall
performance by DM, width and S/N
```

Without these, a good result is difficult to reproduce and nearly impossible to diagnose later.

The model is the easy part. The hard part is defining examples that represent the radio environment and designing a split that prevents the same interference from appearing on both sides. If that part is wrong, a beautiful confusion matrix only shows that the leakage was easy to learn.
