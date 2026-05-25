---
title: "Fast Radio Bursts"
date: 2026-05-25 12:00:00 -0300
author: paolo
layout: post
permalink: /2026/05/25/fast-radio-bursts/
categories:
  - en-US
tags:
  - astronomy
  - radio
  - machine-learning
  - frb
---

Fast Radio Bursts are short radio pulses, usually lasting from microseconds to milliseconds, and they are absurdly energetic. Most of them are extragalactic. That part is not just a guess: their dispersion measures are too large to be explained by the Milky Way alone.

That is what makes FRBs so useful. They are not only interesting transient sources. They also work as probes of the plasma between galaxies.

## The observational signature

The defining measurement is **DM**, or dispersion measure. It is the integrated electron density along the line of sight. For an FRB, the observed DM can be written as:

$$
\text{DM}_{\text{obs}} =
\text{DM}_{\text{MW}} +
\text{DM}_{\text{IGM}} +
\frac{\text{DM}_{\text{host}}}{1+z}
$$

The Milky Way contribution can be estimated with Galactic electron-density models. The excess points to material outside the Galaxy.

The IGM component grows roughly with redshift:

$$
\text{DM}_{\text{IGM}} \approx 855 z\quad [\text{pc cm}^{-3}]
$$

This is why localized FRBs are useful for cosmology. If you know the host galaxy and redshift, the burst becomes a measurement of the ionized matter between us and the source.

## One-offs and repeaters

FRBs are usually grouped by observed behavior:

| Type | Description |
|---|---|
| One-off | Detected once, which is still most of the population |
| Repeater | Multiple bursts from the same source |
| Periodic repeater | Activity modulated on a longer period |

The line between one-off and repeater is not always physical. Sometimes it is just observing time. If you do not stare at a source long enough, a repeater can look like a one-off.

## Progenitors

The strongest current model is the magnetar model: neutron stars with magnetic fields above about `10^14` G.

The big clue came from FRB 20200428, which was seen together with an X-ray burst from the Galactic magnetar SGR 1935+2154. That does not mean every FRB comes from the same mechanism, but it made magnetars a real physical anchor for the field.

The proposed mechanisms usually involve crust rearrangement, magnetic reconnection or coherent emission from a compact region. Other ideas still exist, including neutron-star mergers, accretion-related instabilities and more exotic models.

## Scattering and time structure

Dispersion is not the only thing that happens to the pulse. Turbulent plasma also scatters it, widening the pulse in time:

$$
\tau_{\text{scat}} \propto \text{DM}^2 f^{-4}
$$

That hurts low-frequency observations because the pulse can become smeared enough to be hard to detect.

The really interesting part is the fine time structure. FRB 170827 showed microstructure around 30 microseconds after coherent dedispersion. A time scale that short implies an emitting region of order 10 km, which is neutron-star scale.

Some bursts also show multiple peaks. FRB 181017 had three peaks separated by about 1 ms. One possible explanation is gravitational lensing by compact objects, although phase-coherence tests did not confirm that for this case.

## Real-time detection is hard

Finding FRBs is a signal-processing problem with a nasty false-positive problem.

A search pipeline has to scan many trial DMs, often `10^4` to `10^5` possibilities per data block. It also has to search different pulse widths. In real time, the decision window can be very small. The ATA frbnn-style problem, for example, works on blocks around 130 ms.

The main enemy is RFI, terrestrial radio-frequency interference. It can be bright, weird and frequent. A pipeline can generate huge numbers of candidates per day if it only uses signal-to-noise thresholds.

Classic tools such as HEIMDALL search for single pulses on GPU by:

- dedispersing over a grid of DMs
- convolving with boxcar windows of different widths
- clustering candidates by DM and width
- applying quality filters before classification

That still leaves a classification problem. Machine learning is now a normal part of FRB pipelines because it can learn the difference between real dispersed bursts and many RFI morphologies.

Useful features include modulation index, power in known RFI bands, normality tests on the spectrum, pixel statistics above noise thresholds and checks on the baseline before and after the event. CNNs and ResNets can also work directly on time-frequency images.

## Voltage capture

If the system detects a burst in real time, it can trigger a voltage dump before the raw buffer is overwritten. That matters because voltage data preserves phase and amplitude, so coherent dedispersion becomes possible.

Coherent dedispersion removes intra-channel dispersion much better than incoherent methods. For some pipelines this changes the useful time resolution from hundreds of microseconds to around 10 microseconds. That is the difference between seeing a blurred transient and studying its real temporal structure.

## Why FRBs matter

FRBs are useful because they sit at the intersection of compact-object physics, radio signal processing and cosmology.

They can help measure the missing baryons in the diffuse intergalactic medium. With enough localized events, they can contribute to estimates of `H_0`. Their rotation measures can probe magnetic fields across cosmological distances.

For me, the most interesting part is the pipeline side: real-time radio astronomy is where DSP, GPUs, machine learning and messy physical signals all collide.
