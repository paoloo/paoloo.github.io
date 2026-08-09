---
title: "Watching Solar X-Ray Patterns with MOMENT-1 in Real Time"
date: 2026-08-09 12:00:00 -0300
author: paolo
layout: post
permalink: /2026/08/09/real-time-solar-x-ray-patterns-with-moment-1/
categories:
  - en-US
tags:
  - astronomy
  - machine-learning
  - time-series
  - solar-physics
  - space-weather
  - python
---

I wanted a real-time astronomy example that would not go quiet as soon as an observing run ended. Solar X-ray flux is a good fit. NOAA's geostationary satellites measure it continuously, the public feed updates about once per minute, and the signal has an immediate physical interpretation through the familiar A, B, C, M, and X flare classes.

The experiment in this post polls that feed, keeps a rolling time series, and passes the updated window through MOMENT-1 on every tick. The model does not predict a flare class. It turns the window into a 768-value embedding, a compact numerical description of its pattern. The script then compares that embedding with the one produced at startup and reports how far the pattern has moved.

The full path is:

```text
NOAA GOES X-ray flux
    -> select the 0.1-0.8 nm channel
    -> log10(flux)
    -> [1, 512] float32 tensor
    -> MOMENT-1 ONNX
    -> 768-dimensional embedding
    -> cosine drift + GOES class + JSONL log
```

This is a small monitoring experiment, not a trained solar-flare detector. That distinction matters because the final `pattern` value combines a general-purpose embedding with hand-written thresholds. It is still useful: the code shows how to connect a real scientific stream to a time-series foundation model without hiding the mechanics.

## Model and data source

The model file is [`light-curve/moment1-base`](https://huggingface.co/light-curve/moment1-base), an ONNX export of the MOMENT-1 base model. The file used by the script is [`moment1-base.onnx`](https://huggingface.co/light-curve/moment1-base/resolve/main/moment1-base.onnx), about 355 MB. The underlying model family is described in [MOMENT: A Family of Open Time-series Foundation Models](https://arxiv.org/abs/2402.03885), published at ICML 2024.

The live data comes from the [NOAA Space Weather Prediction Center](https://www.swpc.noaa.gov/). The script reads the public [GOES primary-satellite six-hour X-ray JSON feed](https://services.swpc.noaa.gov/json/goes/primary/xrays-6-hour.json). Each record includes a UTC timestamp, energy band, observed flux, corrected flux, satellite identifier, and contamination information.

The feed contains two X-ray channels. I use `0.1-0.8nm`, also called the 1-8 Angstrom or long channel, because this is the band used for the standard GOES flare classification. The script consumes the electron-corrected `flux` field in watts per square metre.

## Loading the model once

The model should not be downloaded or initialized inside the polling loop. `download_model()` first accepts an explicitly supplied local file. If none is given, `hf_hub_download()` fetches the ONNX weights and lets the Hugging Face client cache them:

```python
MODEL_REPO = "light-curve/moment1-base"
MODEL_FILE = "moment1-base.onnx"

def download_model(local_path=None):
    if local_path:
        if Path(local_path).exists():
            return local_path
        raise FileNotFoundError(f"model not found at {local_path}")

    from huggingface_hub import hf_hub_download
    return hf_hub_download(repo_id=MODEL_REPO, filename=MODEL_FILE)
```

ONNX Runtime then opens one CPU inference session and discovers the input tensor name from the model itself:

```python
def make_session(model_path):
    import onnxruntime as ort
    session = ort.InferenceSession(
        model_path,
        providers=["CPUExecutionProvider"],
    )
    return session, session.get_inputs()[0].name
```

Keeping that session alive is what makes repeated inference practical. Every minute the script changes only the input tensor.

## Turning the JSON feed into a time series

`fetch_xray()` uses a persistent `requests.Session`, checks the HTTP status, and decodes the response as JSON. `extract_series()` does the scientific filtering:

```python
def extract_series(records, band="0.1-0.8nm"):
    points = []
    for record in records:
        if record.get("energy") != band:
            continue

        flux = record.get("flux")
        timestamp = record.get("time_tag")
        if flux is None or timestamp is None:
            continue
        if flux <= 0 or not np.isfinite(flux):
            continue

        points.append((timestamp, float(flux)))

    points.sort(key=lambda item: item[0])
    return points
```

The positivity test is needed because the next step takes a base-10 logarithm. A zero or negative measurement would not have a finite logarithm. Sorting by `time_tag` also means inference does not depend on the order in which the server happened to serialize the records.

The polling loop keeps two related structures. `buffer` holds the ordered `(timestamp, flux)` pairs used for inference, while `seen_tags` prevents the same minute from being appended again when two consecutive requests contain overlapping six-hour windows.

```python
for timestamp, flux in points:
    if timestamp not in seen_tags:
        seen_tags.add(timestamp)
        buffer.append((timestamp, flux))
```

On startup, one request supplies roughly six hours of history, or about 360 one-minute values. After that, the buffer grows one new point at a time. The script retains at most 1,024 points, although the model uses only the newest 512.

## Building the 512-point model input

Raw solar X-ray flux spans several orders of magnitude. `to_tensor()` applies `log10`, takes the most recent 512 values, and left-pads shorter sequences with `NaN`:

```python
def to_tensor(fluxes):
    values = np.asarray(fluxes[-512:], dtype=np.float32)
    values = np.log10(values)

    missing = 512 - values.size
    if missing > 0:
        padding = np.full(missing, np.nan, dtype=np.float32)
        values = np.concatenate([padding, values])

    return values.reshape(1, 512).astype(np.float32)
```

The final shape is always `[1, 512]`: one time series in the batch and 512 positions in the context. MOMENT treats `NaN` positions as missing or padded values and performs its normalization internally.

The first inference normally contains about 360 measurements and 152 padding positions. If the process keeps running, the buffer reaches 512 real samples after another two and a half hours. At that point the tensor represents about 8.5 hours of one-minute observations.

MOMENT does not receive timestamps here. It sees the values in observation order and assumes equal spacing. That assumption is reasonable for a clean one-minute feed, but gaps are not reconstructed. If several samples are missing, adjacent tensor positions no longer represent exactly one minute apart.

## From a window to an embedding

The ONNX call is short:

```python
def embed(session, input_name, tensor):
    output = session.run(["mean"], {input_name: tensor})
    return output[0][0].astype(np.float32)
```

The model also has per-patch sequence output, but this script requests only `mean`. The result has shape `[768]`. It is not a probability vector and its Euclidean norm is not a confidence score. It is a location in the representation space learned by the model.

The first embedding becomes a fixed baseline. Later ticks use cosine similarity to compare the direction of the current vector with that baseline:

```python
def cosine(a, b):
    denominator = (np.linalg.norm(a) + 1e-12) * (np.linalg.norm(b) + 1e-12)
    return float(np.dot(a, b) / denominator)

drift = 1.0 - cosine(current_embedding, baseline_embedding)
```

Identical directions produce a drift near zero. As the embedding rotates away from its starting direction, drift increases. The small `1e-12` terms protect the division if a vector norm is extremely small.

There is a subtlety during startup: while the buffer grows from roughly 360 to 512 measurements, the amount of `NaN` padding changes. Some drift can therefore come from the changing window occupancy, not from a solar event. A production monitor would calibrate this effect, use a rolling baseline, and determine thresholds from labeled historical data.

## GOES classes and the pattern label

The GOES letter is calculated directly from the latest physical flux. The class boundaries are powers of ten:

| Class | 0.1-0.8 nm flux (W/m<sup>2</sup>) |
|---|---:|
| A | below `1e-7` |
| B | `1e-7` to below `1e-6` |
| C | `1e-6` to below `1e-5` |
| M | `1e-5` to below `1e-4` |
| X | `1e-4` and above |

The number after the letter expresses the position within that decade. A flux of `7.43e-7 W/m^2`, for example, becomes `B7.4`.

The human-readable pattern is a heuristic layered on top:

```python
if drift >= anomaly_threshold:
    pattern = "PATTERN CHANGE"
elif latest_flux >= 1e-5:
    pattern = "FLARING (M/X)"
elif latest_flux >= 1e-6:
    pattern = "ELEVATED (C)"
else:
    pattern = "quiet"
```

The default anomaly threshold is `0.05`. It is an engineering choice for the demo, not a physically calibrated decision boundary. Notice also the order: a large embedding drift takes precedence over the flux-based flare label. The GOES class remains visible in its own column, so no physical measurement is lost.

## The live run

The runtime dependencies are small apart from the model file itself:

```bash
pip install onnxruntime huggingface_hub numpy requests
```

I ran the stream from the project's virtual environment and stopped it after three output rows:

```text
$ . .venv/bin/activate && cd neo && python stream.py
[model] fetching MOMENT-1 ONNX (light-curve/moment1-base/moment1-base.onnx) ...
[model] ready: /Users/paolo/.cache/huggingface/hub/models--light-curve--moment1-base/snapshots/dc30dcc72b62fa716923f2d9e07bf5ca15fe2cf8/moment1-base.onnx

[model]   light-curve/moment1-base/moment1-base.onnx
[input]   context : [batch, 512] float32  (log10 flux; NaN-padded)
[output]  mean    : [batch, 768] float32  (pattern embedding)
[stream]  https://services.swpc.noaa.gov/json/goes/primary/xrays-6-hour.json
[band]    0.1-0.8nm  (1-8 Angstrom, GOES flare-classification channel)
[cadence] ~1 min native, polling every 60s
[log]     neo_out/stream.jsonl
Ctrl+C to stop.

time(UTC)               flux(W/m^2)   GOES  n_pts  emb_norm   drift pattern
----------------------------------------------------------------------------------------
2026-08-09T19:20:00Z       7.43e-07   B7.4    358    7.2311  0.0000 quiet
2026-08-09T19:21:00Z       7.73e-07   B7.7    359    7.2305  0.0001 quiet
2026-08-09T19:22:00Z       7.29e-07   B7.3    360    7.2225  0.0004 quiet
^C
[stop] signal received, finishing tick ...
```

The first row establishes the baseline, so its drift is exactly zero. Two subsequent observations change the embedding only slightly, from `0.0001` to `0.0004`, well below the `0.05` threshold. The X-ray flux remains in the B range, and the script labels all three windows `quiet`.

The `n_pts` column grows from 358 to 360 because the polling loop appends one previously unseen timestamp per minute. At 360 points the model input still contains 152 leading `NaN` values. `emb_norm` moves from `7.2311` to `7.2225`, but that small change should not be read as falling confidence. It is only the length of the embedding vector.

## Logging and stopping cleanly

Each tick is appended as one JSON object to `neo_out/stream.jsonl`. The record keeps the physical measurement and enough model metadata to interpret it later:

```json
{
  "tick": 3,
  "time_tag": "2026-08-09T19:22:00Z",
  "flux": 7.29e-07,
  "goes_class": "B7.3",
  "n_points": 360,
  "n_new": 1,
  "embedding_norm": 7.2225,
  "drift": 0.0004,
  "pattern": "quiet",
  "model": "light-curve/moment1-base/moment1-base.onnx",
  "input_shape": [1, 512],
  "output_shape": [1, 768]
}
```

The values above illustrate the schema; the file stores the unrounded floating-point values produced during inference.

`SIGINT` and `SIGTERM` handlers set a shared `running` flag to false instead of terminating the interpreter in the middle of a request or write. Pressing `Ctrl+C` therefore produces the `[stop]` line and lets the current tick finish. This is a small detail, but it matters in a long-running monitor because a half-written final JSON line makes downstream parsing harder.

For unattended tests, `--max-ticks` provides a deterministic stop. Other useful options are:

```bash
# poll every 30 seconds and stop after 20 ticks
python stream.py --interval 30 --max-ticks 20 --out neo_out

# avoid a model download by supplying a local ONNX file
python stream.py --model-path /path/to/moment1-base.onnx

# change the experimental cosine-drift threshold
python stream.py --anomaly-threshold 0.02
```

## What this experiment does and does not show

The useful result is modest. A live, public scientific measurement can be turned into a model-ready tensor, embedded once per minute on a CPU, compared with a baseline, printed for a human operator, and recorded for later analysis. The terminal output shows the full loop working on real B-class solar background data.

It does not show that `0.05` is the right anomaly threshold, that embedding drift predicts flares, or that MOMENT outperforms a simpler detector. Before trusting it as a detector, I would replay labeled historical GOES intervals, calibrate the threshold on a validation split, and compare it with flux derivatives, rolling z-scores, and change-point detectors.

For now, the code solves the streaming and recording problem while keeping the raw flux and official GOES class beside every embedding result. A later evaluation can therefore be checked against the measurement that produced it.
