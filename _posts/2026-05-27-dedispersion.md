---
title: "Dedispersion"
date: 2026-05-27 12:00:00 -0300
author: paolo
layout: post
permalink: /2026/05/27/dedispersion/
categories:
  - en-US
tags:
  - astronomy
  - radio
  - signal-processing
  - frb
---

Radio pulses do not travel through space unchanged. When they cross ionized plasma, lower frequencies arrive later than higher frequencies. For pulsars and FRBs, this effect can smear a sharp pulse into something much wider and sometimes undetectable.

**Dedispersion** is the process of undoing that delay.

## Cold plasma dispersion

In a cold plasma, the refractive index depends on frequency:

$$
n(\nu) =
\sqrt{1 - \left(\frac{\nu_p}{\nu}\right)^2}
\approx
1 - \frac{\nu_p^2}{2\nu^2}
$$

The group delay relative to vacuum is:

$$
\Delta t(\nu) =
\frac{e^2}{2\pi m_e c}
\frac{\text{DM}}{\nu^2}
=
\frac{k_{\text{DM}}\text{DM}}{\nu^2}
$$

Here DM is the dispersion measure, the integrated electron density along the path. A useful constant is:

$$
k_{\text{DM}} \approx
4150.377\ \text{MHz}^2\ \text{pc}^{-1}\ \text{cm}^3\ \text{s}
$$

The delay between two observing frequencies is:

$$
\Delta t_{12} =
k_{\text{DM}}\text{DM}
\left(
\frac{1}{\nu_1^2} -
\frac{1}{\nu_2^2}
\right)
$$

That is the sweep you see in a dynamic spectrum: high frequencies first, low frequencies later.

## Incoherent dedispersion

The simplest method is incoherent dedispersion. You split the signal into frequency channels, shift each channel by the expected delay for a trial DM, and sum:

$$
S(t) =
\sum_i x_i(t + \Delta t(\nu_i))
$$

This is cheap and parallelizes well. That is why it is common in real-time search pipelines.

The cost is time resolution. Each frequency channel still has residual dispersion inside the channel bandwidth:

$$
\delta t =
\frac{2k_{\text{DM}}\text{DM}\Delta\nu_{\text{ch}}}{\nu^3}
$$

So incoherent dedispersion can find bursts, but it cannot always recover the true pulse shape.

## Coherent dedispersion

Coherent dedispersion works before power detection, on the complex voltage signal. In the frequency domain, it applies the inverse transfer function of the dispersive plasma:

$$
\tilde{x}_{\text{dedisp}}(\nu) =
\tilde{x}(\nu)H(\nu)
$$

with a phase correction like:

$$
H(\nu) =
e^{+i\pi k_{\text{DM}}\text{DM}\nu^2/\nu_0^3}
$$

The advantage is that it can recover the temporal structure down to the sampling limit. The disadvantage is that it is more expensive and needs complex voltage data, not only detected power.

This is why voltage capture matters in FRB systems. If the pipeline can trigger quickly enough, it can save the raw buffer and later apply coherent dedispersion to study microstructure.

## DM trials

For a known pulsar, you usually know the DM. For an unknown FRB, you do not. So the pipeline has to search a grid of trial DMs:

$$
N_{\text{DM}} \sim
\frac{\text{DM}_{\text{max}} - \text{DM}_{\text{min}}}
{\delta\text{DM}}
$$

The DM step has to be small enough that a real pulse is not smeared too much:

$$
\delta\text{DM}
\leq
\frac{\delta t_{\text{sample}}}
{2k_{\text{DM}}\Delta\nu/\nu^3}
$$

For a wide-band radio system, this can mean thousands or tens of thousands of trial DMs for every block of data. That is why GPU acceleration is so common in single-pulse search.

## Galactic electron models

To decide whether a burst is likely Galactic or extragalactic, you need an estimate of the Milky Way DM contribution along the line of sight.

Two common models are:

- **NE2001**, which models the Galaxy with spiral arms, thin and thick disks and clumps
- **YMW16**, a newer model built from a larger pulsar sample

If the observed DM is much larger than the predicted Galactic contribution, the excess is evidence for an extragalactic source. That is one of the core ideas behind FRB detection.

Dedispersion looks like a small technical correction at first, but it is the thing that turns a smeared radio sweep into a pulse you can detect, classify and study.
