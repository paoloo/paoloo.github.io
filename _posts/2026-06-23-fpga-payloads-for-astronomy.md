---
title: "A Software Model for an FPGA Astronomy Payload"
date: 2026-06-23 12:00:00 -0300
author: paolo
layout: post
permalink: /2026/06/23/software-model-for-an-fpga-astronomy-payload/
categories:
  - en-US
tags:
  - fpga
  - astronomy
  - cubesat
  - signal-processing
  - python
---

A CubeSat payload can observe more than it can downlink. That one constraint changes how I think about data processing. The first scientific decision may happen before the data reaches the main flight computer.

That is why I like modeling FPGA payloads in software first. Writing HDL too early is a good way to build the wrong thing faster. A small Python model lets me decide what the payload keeps, what it rejects, and how much data it can save before I start thinking about fixed-point arithmetic and streaming interfaces.

For this post I modeled a tiny radio astronomy payload:

```text
complex ADC samples
    |
FFT channelizer
    |
power detector
    |
RFI mask
    |
event trigger
    |
summary + triggered snippets
    |
downlink
```

The script is in:

```text
res/fpga_payload_pipeline_demo.py
```

I ran it with:

```bash
MPLCONFIGDIR=/tmp/mplconfig \
conda run -n exohunter python res/fpga_payload_pipeline_demo.py \
  --plot uploads/2026/06/fpga-payload-pipeline.png \
  --json /tmp/fpga-payload-pipeline.json
```

No FPGA board was needed for this pass. This is the data-path sketch I would want before writing hardware.

## The simulated payload input

I simulated `0.262144` seconds of complex samples at `2 MHz`, giving `524,288` IQ samples. The signal contains three things:

- complex Gaussian noise;
- two persistent narrowband RFI tones;
- one short weak event near `115 kHz`.

The synthetic input starts with complex noise:

```python
def complex_noise(rng, n):
    return (
        rng.normal(0.0, 1.0, n).astype(np.float32)
        + 1j * rng.normal(0.0, 1.0, n).astype(np.float32)
    ) / np.sqrt(2.0)
```

Then I injected two persistent tones:

```python
add_tone(samples, sample_rate_hz, -310_000.0, amp=3.2)
add_tone(samples, sample_rate_hz,  420_000.0, amp=2.4)
```

And one short event:

```python
add_burst(
    samples,
    sample_rate_hz,
    freq_hz=115_000.0,
    center_s=0.142,
    width_s=0.0045,
    amp=1.35,
)
```

The event is not supposed to dominate the whole observation. The payload has to remove the obvious RFI and still trigger on the short event.

## Channelizing like an FPGA block

The software channelizer uses `1024`-point FFT frames:

```python
def channelize(samples, nfft):
    usable = samples[: samples.size // nfft * nfft]
    frames = usable.reshape(-1, nfft)
    window = np.hanning(nfft).astype(np.float32)
    spectra = np.fft.fftshift(np.fft.fft(frames * window, axis=1), axes=1)
    return (np.abs(spectra) ** 2).astype(np.float32)
```

With a `2 MHz` sample rate and `nfft = 1024`, each frame covers:

```text
1024 / 2,000,000 = 0.512 ms
```

The resulting power matrix has:

```text
512 time frames x 1024 frequency channels
```

In Python this is a batch operation. In hardware, this becomes a streaming FFT plus a power detector. The important design property is that each frame has a fixed size and a fixed latency. That is the FPGA-friendly part.

## Masking RFI before downlink

The two injected RFI tones are persistent in time. I masked channels whose median power is too far from the band median:

```python
def robust_snr(series):
    median = np.median(series)
    mad = np.median(np.abs(series - median))
    sigma = 1.4826 * mad
    if sigma == 0:
        return np.zeros_like(series)
    return (series - median) / sigma


def rfi_mask(power, sigma_cut=8.0):
    band_median = np.median(power, axis=0)
    score = robust_snr(band_median)
    return np.abs(score) < sigma_cut, score
```

In this run, the mask removed `9` of `1024` channels. That sounds small, but those channels contained the bright persistent tones. Removing them before the trigger stops the event detector from confusing "always loud" with "interesting now."

<figure class="wp-block-image"><img src="{{ site.baseurl }}/uploads/2026/06/fpga-payload-pipeline.png" alt="Software model of an FPGA radio astronomy payload showing raw channelized power, masked power, and trigger score" /><figcaption>The software payload model. The top panel shows the raw channelized power with two persistent RFI tones and one short event. The middle panel masks the persistent RFI channels. The bottom panel shows the event trigger crossing threshold near the injected event.</figcaption></figure>

## The event trigger

After masking RFI, I collapsed the remaining channels into a time series and computed a robust S/N:

```python
masked = power.copy()
masked[:, ~mask] = 0.0

time_series = masked[:, mask].mean(axis=1)
trigger_score = robust_snr(time_series)
trigger_frames = np.flatnonzero(trigger_score > 8.0)
```

The trigger fired on `23` frames. The strongest trigger was:

```text
max trigger score: 43.00
peak trigger time: 141.312 ms
```

That matches the injected event at `142 ms` closely enough for this model. The small offset is expected because the trigger works on FFT frames, not continuous time.

The important check is that the payload did not trigger on the two persistent tones. It triggered on the short event I injected. That is the behavior I wanted before thinking about HDL.

## The downlink math

The most useful part of the experiment was not the detection. It was the accounting.

The raw complex samples were:

```text
524,288 complex64 samples = 8,388,608 bytes
```

The full channelized power product, modeled as 12-bit quantized power and stored as `uint16`, was:

```text
512 frames x 1024 channels x 2 bytes = 1,048,576 bytes
```

The `uint16` detail is only a storage convenience. NumPy does not have a native `uint12` type, so the script clips power to a 12-bit range and stores the result in a 16-bit array. On hardware, those 12-bit values would be packed more tightly.

The payload did not need to downlink all of that. In the model, it keeps a small summary plus full-resolution snippets around triggered frames:

```text
summary + trigger snippets = 116,736 bytes
```

That gives:

```text
reduction vs raw IQ: 71.86x
reduction vs full power waterfall: 8.98x
```

The reduced JSON output from the run is the part I would keep in a lab note:

```json
{
  "n_frames": 512,
  "n_channels": 1024,
  "rfi_channels_flagged": 9,
  "trigger_count": 23,
  "max_trigger_score": 43.002010345458984,
  "peak_trigger_time_ms": 141.31199999999998,
  "reduction_vs_raw_iq": 71.85964912280701,
  "reduction_vs_full_power": 8.982456140350877
}
```

Those numbers are why onboard processing matters. The FPGA is not doing astronomy by itself. It is buying the mission enough bandwidth to send the parts that deserve ground analysis.

## What this is not

This is not HDL. It is not a benchmark on a real FPGA board. It is not a flight payload, and it does not prove timing closure, radiation tolerance, thermal behavior, or flight readiness.

It is a software model of the data path. That is still useful. Before writing Verilog, VHDL, or HLS code, I want to know whether the pipeline logic is worth implementing: whether it masks the obvious RFI, keeps the event, and reduces the downlink volume by enough to matter.

## Why this maps to FPGA

The blocks in this model are repetitive and streaming:

```text
window
FFT
power
median/accumulator-like statistics
threshold
packetize snippets
```

That is a good fit for FPGA logic. The payload does not need a general-purpose scheduler to decide how to multiply every sample. It needs a deterministic stream of operations with bounded buffers.

A CPU can run the Python version easily in the lab. In orbit, the question is different: can the payload keep up with the sample stream while staying inside the power and thermal budget? A streaming hardware pipeline is attractive because each block consumes samples, produces samples or summaries, and does not need to store the whole observation.

## Fixed-point is where the real design starts

The Python model uses floating point because I wanted to see the data path first. The FPGA version would not be written that way.

The next decisions are fixed-point decisions:

- input bit width from the ADC;
- FFT internal growth;
- power accumulator width;
- scaling before thresholding;
- saturation behavior;
- packet format for snippets and summaries.

Overflow is not a theoretical problem here. A persistent RFI tone can push accumulators harder than the signal I care about. If the fixed-point scale is wrong, the payload can either clip the event or let RFI dominate the trigger.

That is another reason to model first. The software version tells me what ranges the hardware must survive.

## Security angle

An FPGA payload is also a security boundary. If it decides what gets stored or downlinked, it can affect the mission even without controlling attitude or power.

The questions I would ask before flight are concrete:

```text
Can the bitstream be updated?
Who can update it?
Is the bitstream authenticated?
Are JTAG and debug interfaces disabled or controlled?
Can telecommands change trigger thresholds?
Are threshold changes logged?
Can malformed payload packets affect the bus?
Is the payload isolated from command-critical software?
```

The threshold question matters. If a command can quietly raise the trigger threshold, the spacecraft may stop downlinking events. If it can lower the threshold too far, the payload may flood storage with junk. Payload security is mission assurance, not only computer security.

## What I would build next

This post stops at the software model. The next step is to split it into hardware-shaped blocks:

```text
sample stream input
window multiply
streaming FFT
power detector
channel statistics
RFI mask
event trigger
snippet buffer
packet output
```

Then I would replace the floating-point operations with fixed-point approximations and run the same test again. The pass condition is simple: the hardware-shaped model still needs to mask the two persistent RFI tones, trigger near `142 ms`, and preserve the same order-of-magnitude downlink reduction.

The main lesson is practical: for small spacecraft astronomy, onboard processing is not an optional polish step. It is part of the instrument. The first filter may need to live close to the sensor, and an FPGA is often the cleanest place to put it.
