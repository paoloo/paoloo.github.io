---
title: "Finding Radio Pulses in a Waterfall Plot"
date: 2026-05-23 12:00:00 -0300
author: paolo
layout: post
permalink: /2026/05/23/finding-radio-pulses-in-a-waterfall-plot/
math: true
categories:
  - en-US
tags:
  - python
  - astronomy
  - radio
  - signal-processing
---

A radio transient usually starts as a two-dimensional array: frequency on one axis, time on the other, power in each pixel. Radio astronomers call this a dynamic spectrum or waterfall plot.

An FRB or pulsar pulse does not arrive at every frequency at once. Free electrons along the line of sight delay low frequencies more than high frequencies. In a waterfall, the pulse is a curve. The first detection task is to find the dispersion measure that straightens that curve and concentrates its energy in time.

I tested the complete chain with synthetic data. I generated noise, injected a dispersed pulse, dedispersed it over a grid of trial DMs and recovered it with a simple S/N statistic.

## The data model

I represented the waterfall as

$$
W(f_i,t_j) \in \mathbb{R}^{N_f \times N_t}
$$

where each row is one frequency channel and each column is one time sample.

I used the following dimensions and sampling:

```python
import numpy as np

rng = np.random.default_rng(23)

n_freq = 192
n_time = 2048
dt_ms = 0.5

frequencies_mhz = np.linspace(1200.0, 1500.0, n_freq)
waterfall = rng.normal(0.0, 1.0, size=(n_freq, n_time))
```

The noise has zero mean and unit standard deviation. Real telescope data needs bandpass normalization, RFI masking and calibration first, but unit Gaussian noise gives us a controlled starting point.

## Cold-plasma delay

The differential arrival time relative to a reference frequency is

$$
\Delta t_{\rm ms} = k_{\rm DM}\,\mathrm{DM}
\left(\nu^{-2} - \nu_{\rm ref}^{-2}\right)
$$

when frequency is in MHz and

$$
k_{\rm DM} \approx 4.148808 \times 10^6
\;\mathrm{ms\,MHz^2\,pc^{-1}\,cm^3}.
$$

In Python:

```python
K_DM_MS = 4.148808e6


def dispersion_delay_ms(dm, frequencies_mhz, reference_mhz=None):
    if reference_mhz is None:
        reference_mhz = np.max(frequencies_mhz)

    return (
        K_DM_MS
        * dm
        * (frequencies_mhz ** -2 - reference_mhz ** -2)
    )
```

The highest channel is the reference, so its delay is zero. Lower frequencies have positive delays.

## Inject a pulse

For the injection I chose a true DM and an arrival time at the top of the band:

```python
true_dm = 320.0
arrival_sample = 600
pulse_width_ms = 3.0
pulse_snr_scale = 1.4
```

I added a Gaussian pulse to every channel and shifted it by the dispersive delay:

```python
def inject_dispersed_pulse(
    data,
    frequencies_mhz,
    dm,
    arrival_sample,
    width_ms,
    dt_ms,
    amplitude,
):
    output = data.copy()
    delays_ms = dispersion_delay_ms(dm, frequencies_mhz)
    width_samples = width_ms / dt_ms
    sample_axis = np.arange(output.shape[1])

    for channel, delay_ms in enumerate(delays_ms):
        center = arrival_sample + delay_ms / dt_ms
        profile = amplitude * np.exp(
            -0.5 * ((sample_axis - center) / width_samples) ** 2
        )
        output[channel] += profile

    return output


waterfall = inject_dispersed_pulse(
    waterfall,
    frequencies_mhz,
    dm=true_dm,
    arrival_sample=arrival_sample,
    width_ms=pulse_width_ms,
    dt_ms=dt_ms,
    amplitude=pulse_snr_scale,
)
```

The amplitude in each channel is only 1.4 times the noise standard deviation. No single pixel is convincing. Detection comes from combining the same event across many channels.

## The injected waterfall

```python
import matplotlib.pyplot as plt

time_ms = np.arange(n_time) * dt_ms

fig, ax = plt.subplots(figsize=(10, 5))
image = ax.imshow(
    waterfall,
    origin="lower",
    aspect="auto",
    extent=[time_ms[0], time_ms[-1],
            frequencies_mhz[0], frequencies_mhz[-1]],
    cmap="viridis",
    vmin=-2,
    vmax=4,
)
ax.set_xlabel("time (ms)")
ax.set_ylabel("frequency (MHz)")
ax.set_title("Synthetic dispersed radio pulse")
fig.colorbar(image, ax=ax, label="normalized power")
fig.tight_layout()
fig.savefig("dispersed-waterfall.png", dpi=150)
```

The resulting image showed a faint sweep from high frequency at early time to low frequency at later time.

## Incoherent dedispersion

To test one DM, shift every channel earlier by its expected delay and sum over frequency.

```python
def dedisperse(data, frequencies_mhz, dm, dt_ms):
    delays_ms = dispersion_delay_ms(dm, frequencies_mhz)
    delays_samples = np.rint(delays_ms / dt_ms).astype(int)

    aligned = np.zeros_like(data)

    for channel, shift in enumerate(delays_samples):
        if shift == 0:
            aligned[channel] = data[channel]
        elif shift < data.shape[1]:
            aligned[channel, :-shift] = data[channel, shift:]

    return aligned
```

This was incoherent dedispersion: I shifted detected power rather than correcting the phase of complex voltages. Integer shifts also left sub-sample and intra-channel smearing.

I first applied the true DM:

```python
dedispersed = dedisperse(
    waterfall,
    frequencies_mhz,
    dm=true_dm,
    dt_ms=dt_ms,
)

time_series = dedispersed.mean(axis=0)
```

At the correct DM, the pulse energy lines up near `arrival_sample`. At the wrong DM, each channel peaks at a different time and the average stays weak.

## A robust S/N estimate

I used the median and MAD so the bright pulse did not strongly bias the noise estimate:

```python
def robust_snr(series):
    median = np.median(series)
    mad = np.median(np.abs(series - median))
    sigma = 1.4826 * mad

    if sigma == 0:
        return np.zeros_like(series)

    return (series - median) / sigma


snr_series = robust_snr(time_series)
peak_sample = int(np.argmax(snr_series))
peak_snr = float(snr_series[peak_sample])

print(f"peak sample: {peak_sample}")
print(f"peak time: {peak_sample * dt_ms:.1f} ms")
print(f"peak S/N: {peak_snr:.2f}")
```

The factor `1.4826` converts MAD to the standard deviation for Gaussian data.

## Search over unknown DM

For the unknown-DM case, I searched a grid:

```python
trial_dms = np.arange(0.0, 601.0, 5.0)
best_snr = []
best_sample = []

for dm in trial_dms:
    trial = dedisperse(waterfall, frequencies_mhz, dm, dt_ms)
    series = trial.mean(axis=0)
    score = robust_snr(series)

    best_snr.append(float(np.max(score)))
    best_sample.append(int(np.argmax(score)))

best_snr = np.asarray(best_snr)
best_sample = np.asarray(best_sample)

winner = int(np.argmax(best_snr))
recovered_dm = trial_dms[winner]

print(f"true DM: {true_dm:.1f}")
print(f"recovered DM: {recovered_dm:.1f}")
print(f"detection S/N: {best_snr[winner]:.2f}")
```

I plotted the search curve:

```python
fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(trial_dms, best_snr)
ax.axvline(true_dm, color="tab:red", linestyle="--", label="true DM")
ax.set_xlabel("trial DM (pc cm$^{-3}$)")
ax.set_ylabel("maximum S/N")
ax.set_title("DM search")
ax.legend()
fig.tight_layout()
fig.savefig("dm-search.png", dpi=150)
```

The curve peaked near the injected DM. The exact maximum moved slightly with the grid because delays were rounded to integer samples and noise changed the peak.

## Why the DM grid spacing matters

A coarse grid is fast but leaves residual smearing. A fine grid preserves S/N but costs more computation. The acceptable DM error is the error that keeps residual delay across the band below some fraction of the pulse width or sample interval.

For an error $\delta\mathrm{DM}$, residual sweep across the band is

$$
\delta t = k_{\rm DM}\,\delta\mathrm{DM}
\left(\nu_{\rm low}^{-2} - \nu_{\rm high}^{-2}\right).
$$

I calculated the grid spacing that produced one sample of residual delay:

```python
band_factor = (
    frequencies_mhz.min() ** -2
    - frequencies_mhz.max() ** -2
)

dm_step_one_sample = dt_ms / (K_DM_MS * band_factor)
print(f"DM step for one-sample residual: {dm_step_one_sample:.2f}")
```

Real pipelines use nonuniform DM plans because scattering, channel smearing and acceptable downsampling change with DM.

## Pulse width is also unknown

After dedispersion, search several boxcar widths. This connects directly to [Matched Filtering from Scratch]({{ site.baseurl }}/2026/05/28/matched-filtering-from-scratch/).

```python
def boxcar_snr(series, widths):
    candidates = []

    for width in widths:
        kernel = np.ones(width) / np.sqrt(width)
        filtered = np.convolve(series, kernel, mode="same")
        score = robust_snr(filtered)
        candidates.append((np.max(score), width, np.argmax(score)))

    return max(candidates, key=lambda item: item[0])


best = boxcar_snr(time_series, widths=[1, 2, 4, 8, 16, 32])
print(f"best S/N={best[0]:.2f}, width={best[1]}, sample={best[2]}")
```

The complete search space is now DM, arrival time and width. A production pipeline clusters nearby detections because one physical pulse triggers several neighboring trials.

## What happened after I added RFI

Inject a broadband impulse with zero dispersion:

```python
rfi_sample = 1400
waterfall[:, rfi_sample:rfi_sample + 2] += 3.0
```

That event had high S/N at DM=0 and leaked into low nonzero DMs. I also added a persistent narrowband carrier:

```python
waterfall[80:83, :] += 2.0
```

The detector then produced candidates that were not astrophysical. This was a useful reminder that dedispersion and matched filtering are detectors, not complete classifiers. My next stage needed morphology, multibeam information, known-frequency masks or a learned model.

## What is simplified here

This synthetic test left out several real effects:

- frequency-dependent bandpass and system temperature
- missing or flagged channels
- fractional-sample shifts
- intra-channel dispersion
- scattering tails
- frequency-dependent pulse spectra
- correlated and nonstationary noise
- multiple beams and polarization
- candidate clustering
- GPU acceleration

That is acceptable because every omitted effect can now be added to a working baseline and measured separately.

What I got from this test was more than a curved line becoming straight. The search behaved like a structured hypothesis test: for each DM and width, I checked whether the data contained a pulse consistent with cold-plasma propagation. Everything after that became a fight against false positives.
