---
layout: sidebar
title: Research
permalink: /research/
---

My research sits where machine learning, scientific computing, radio astronomy and space systems meet. I am interested in models that do more than perform well in a notebook: they must work with real instruments, incomplete data, limited compute and the operational constraints of scientific and aerospace systems.

## SETI and technosignatures

I work at the SETI Institute as an Intelligence Engineer, applying machine learning to radio and astrophysical data in the search for non-human technosignatures. My work includes candidate triage, radio-frequency interference mitigation, inference tooling and the data pipelines that connect telescope observations to scientific analysis.

I am particularly interested in:

- learned and statistical methods for RFI rejection
- narrowband and transient signal detection
- anomaly detection for large radio surveys
- reproducible candidate-ranking pipelines
- real-time inference close to the instrument
- methods that expose uncertainty instead of hiding it behind a score

## Data-driven astrophysics

I use public surveys and astronomical archives to study problems that combine physical models with machine learning. Current interests include exoplanet detection and vetting, asteroid taxonomy, photometric inference and cross-matching large catalogs such as Gaia and TESS.

The methodological side matters as much as the model. I spend a lot of time on catalog selection effects, label quality, uncertainty, domain shift and data leakage. A high validation score is not useful when the split does not represent the sky where the model will operate.

Related notes:

- [TAP for Astronomy Data]({{ site.baseurl }}/2026/05/20/tap-for-astronomy-data/)
- [Cross-matching Gaia and TESS with Python]({{ site.baseurl }}/2026/06/17/cross-matching-gaia-and-tess-with-python/)
- [Classifying Asteroids with CyberEther]({{ site.baseurl }}/2026/06/06/classifying-asteroids-with-cyberether/)
- [Training an Astronomy Model from Scratch]({{ site.baseurl }}/2026/06/07/training-an-astronomy-model-from-scratch/)

## Radio transients and signal processing

Radio transients connect astrophysics to real-time systems. My interests include dedispersion, matched filtering, beamforming, pulse classification and the preservation of raw voltage data for high-time-resolution analysis.

This work combines classical DSP with machine learning. I normally start from a physical signal model, build a measurable baseline, and only then add a learned component where it solves a specific limitation.

Related notes:

- [Fast Radio Bursts]({{ site.baseurl }}/2026/05/25/fast-radio-bursts/)
- [Dedispersion]({{ site.baseurl }}/2026/05/27/dedispersion/)
- [Matched Filtering from Scratch]({{ site.baseurl }}/2026/05/28/matched-filtering-from-scratch/)
- [Building a Small RFI Classifier]({{ site.baseurl }}/2026/04/19/building-a-small-rfi-classifier/)

## Autonomous spacecraft and flight software

My aerospace work focuses on small spacecraft, onboard autonomy and software that remains understandable under strict power, memory, timing and reliability constraints. I am finishing a master's in aerospace engineering focused on machine-learning-based CubeSat design and LLM-based satellite and ground-station orchestration.

Topics I am exploring include:

- deterministic scheduling for constrained flight computers
- onboard inference and TinyML under power budgets
- fault-tolerant software architecture
- autonomous mission planning and ground-station operations
- LLM integration with explicit tools, constraints and verification
- hardware-in-the-loop measurement of timing, power and thermal behavior

[Pulse](https://github.com/paoloo/pulse) is one result of this direction: a small deterministic scheduler for periodic tasks on resource-constrained microcontrollers.

## Biosignatures and exobiology

I also explore bioinformatics problems related to biosignals, biosignatures and exobiology. The common thread is detection under uncertainty: identifying weak structure in noisy scientific data while keeping the biological and instrumental assumptions visible.

This area is still exploratory in my work, but it connects naturally to my broader interest in computational methods for searching for life.

## Research approach

My usual workflow is empirical and systems-oriented:

1. Start from the physical or operational question.
2. Build the smallest reproducible baseline.
3. Measure data quality, uncertainty and failure modes.
4. Add machine learning only where it improves the baseline.
5. Test the complete path from raw data to deployment.
6. Keep code, parameters and provenance available for reproduction.

I am interested in collaborations that connect astronomy, machine learning, embedded systems and aerospace engineering. Code and experimental projects are available through my [GitHub profile](https://github.com/paoloo), while published work is listed on the [Publications]({{ site.baseurl }}/publications/) page.
