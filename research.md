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

## Radio transients and signal processing

Radio transients connect astrophysics to real-time systems. My interests include dedispersion, matched filtering, beamforming, pulse classification and the preservation of raw voltage data for high-time-resolution analysis.

This work combines classical DSP with machine learning. I normally start from a physical signal model, build a measurable baseline, and only then add a learned component where it solves a specific limitation.

## Autonomous spacecraft and flight software

My aerospace work focuses on CubeSat development, onboard autonomy and software that remains understandable under strict power, memory, timing and reliability constraints. I am finishing a master's in aerospace engineering focused on machine-learning-based CubeSat design and LLM-based satellite and ground-station orchestration.

I work across the spacecraft and ground segments rather than treating them as separate systems. This includes flight software, telemetry and telecommand paths, tracking-station software, radio and antenna control, pass scheduling, telemetry processing and the operational tooling needed to follow a spacecraft from contact planning to data delivery.

### Agentic CubeSat and ground-station operations

One of my main research directions is the agentic orchestration of tracking and telemetry stations. I am investigating systems where constrained agents coordinate station availability, pass prediction, radio configuration, antenna tracking, telemetry reception, decoding and operational handoffs across one or more ground stations.

I also work on agentic CubeSat management. In this model, agents assist with spacecraft health assessment, telemetry interpretation, anomaly triage, resource planning, payload scheduling and ground-contact preparation. The goal is not unconstrained autonomous command. The architecture keeps permissions, operational limits, verification and human authorization explicit.

Model Context Protocol (MCP) servers act as controlled interfaces between agents, ground-station services and spacecraft operations. They expose narrowly scoped tools for telemetry access, command preparation, station control and mission data while preserving schemas, authorization boundaries, audit trails and the distinction between proposing an action and executing it.

### CubeSat security and FPGA payloads

Security is part of the spacecraft architecture, not an external layer added after integration. My interests include threat modeling for CubeSats and their ground infrastructure, command authentication, replay protection, secure boot and firmware updates, key management, payload isolation, radio-link security and the protection of telemetry and mission data pipelines.

I am also interested in FPGA-based payloads and hardware/software co-design for small spacecraft. FPGAs provide a useful path for deterministic, low-latency processing close to the instrument, including digital signal processing, filtering, compression, feature extraction and event detection before data reaches the flight computer or downlink. This work connects payload design to timing, power, thermal and fault-containment constraints.

Topics I am exploring include:

- deterministic scheduling for constrained flight computers
- onboard inference and TinyML under power budgets
- fault-tolerant software architecture
- CubeSat tracking, telemetry and telecommand systems
- multi-station pass scheduling and telemetry orchestration
- agentic spacecraft health, payload and resource management
- MCP-based interfaces between agents, spacecraft and ground stations
- LLM integration with explicit tools, constraints and verification
- CubeSat, payload and ground-segment security
- FPGA payloads and onboard signal processing
- hardware-in-the-loop measurement of timing, power and thermal behavior

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
