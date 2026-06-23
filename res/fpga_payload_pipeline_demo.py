#!/usr/bin/env python3
"""Software model of a small FPGA-style radio astronomy payload pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def complex_noise(rng: np.random.Generator, n: int) -> np.ndarray:
    return (
        rng.normal(0.0, 1.0, n).astype(np.float32)
        + 1j * rng.normal(0.0, 1.0, n).astype(np.float32)
    ) / np.sqrt(2.0)


def add_tone(samples: np.ndarray, sample_rate_hz: float, freq_hz: float, amp: float) -> None:
    t = np.arange(samples.size, dtype=np.float64) / sample_rate_hz
    samples += amp * np.exp(2j * np.pi * freq_hz * t).astype(np.complex64)


def add_burst(
    samples: np.ndarray,
    sample_rate_hz: float,
    freq_hz: float,
    center_s: float,
    width_s: float,
    amp: float,
) -> None:
    t = np.arange(samples.size, dtype=np.float64) / sample_rate_hz
    envelope = np.exp(-0.5 * ((t - center_s) / width_s) ** 2)
    samples += (amp * envelope * np.exp(2j * np.pi * freq_hz * t)).astype(np.complex64)


def channelize(samples: np.ndarray, nfft: int) -> np.ndarray:
    usable = samples[: samples.size // nfft * nfft]
    frames = usable.reshape(-1, nfft)
    window = np.hanning(nfft).astype(np.float32)
    spectra = np.fft.fftshift(np.fft.fft(frames * window, axis=1), axes=1)
    return (np.abs(spectra) ** 2).astype(np.float32)


def robust_snr(series: np.ndarray) -> np.ndarray:
    median = np.median(series)
    mad = np.median(np.abs(series - median))
    sigma = 1.4826 * mad
    if sigma == 0:
        return np.zeros_like(series)
    return (series - median) / sigma


def rfi_mask(power: np.ndarray, sigma_cut: float = 8.0) -> tuple[np.ndarray, np.ndarray]:
    band_median = np.median(power, axis=0)
    score = robust_snr(band_median)
    return np.abs(score) < sigma_cut, score


def quantize_uint12(power: np.ndarray) -> np.ndarray:
    scale = np.percentile(power, 99.5)
    if scale <= 0:
        scale = 1.0
    normalized = np.clip(power / scale, 0.0, 1.0)
    return np.rint(normalized * 4095).astype(np.uint16)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plot", type=Path, default=Path("uploads/2026/06/fpga-payload-pipeline.png"))
    parser.add_argument("--json", type=Path, default=Path("/tmp/fpga-payload-pipeline.json"))
    parser.add_argument("--sample-rate", type=float, default=2_000_000.0)
    parser.add_argument("--seconds", type=float, default=0.262144)
    parser.add_argument("--nfft", type=int, default=1024)
    parser.add_argument("--seed", type=int, default=23)
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    n_samples = int(args.sample_rate * args.seconds)
    samples = complex_noise(rng, n_samples)

    # Persistent RFI tones plus a short event that is meant to trigger the payload.
    add_tone(samples, args.sample_rate, -310_000.0, amp=3.2)
    add_tone(samples, args.sample_rate, 420_000.0, amp=2.4)
    add_burst(samples, args.sample_rate, 115_000.0, center_s=0.142, width_s=0.0045, amp=1.35)

    power = channelize(samples, args.nfft)
    n_frames, n_channels = power.shape
    dt_s = args.nfft / args.sample_rate
    freq_axis_khz = np.fft.fftshift(np.fft.fftfreq(args.nfft, d=1 / args.sample_rate)) / 1e3
    time_axis_ms = np.arange(n_frames) * dt_s * 1e3

    mask, rfi_score = rfi_mask(power)
    masked = power.copy()
    masked[:, ~mask] = 0.0
    time_series = masked[:, mask].mean(axis=1)
    trigger_score = robust_snr(time_series)
    trigger_threshold = 8.0
    trigger_frames = np.flatnonzero(trigger_score > trigger_threshold)

    quantized = quantize_uint12(masked)
    raw_bytes = samples.nbytes
    full_power_bytes = quantized.nbytes
    summary_bytes = int(n_frames * 4 + n_channels * 2)
    snippet_half_width = 16
    snippet_frames = set()
    for frame in trigger_frames:
        lo = max(0, frame - snippet_half_width)
        hi = min(n_frames, frame + snippet_half_width + 1)
        snippet_frames.update(range(lo, hi))
    snippet_frames = sorted(snippet_frames)
    snippet_bytes = int(len(snippet_frames) * n_channels * 2)
    downlink_bytes = summary_bytes + snippet_bytes

    result = {
        "sample_rate_hz": args.sample_rate,
        "duration_s": args.seconds,
        "n_samples": n_samples,
        "nfft": args.nfft,
        "n_frames": n_frames,
        "n_channels": n_channels,
        "frame_time_ms": dt_s * 1e3,
        "rfi_channels_flagged": int(np.count_nonzero(~mask)),
        "rfi_channels_kept": int(np.count_nonzero(mask)),
        "trigger_threshold": trigger_threshold,
        "trigger_frames": [int(x) for x in trigger_frames],
        "trigger_count": int(trigger_frames.size),
        "max_trigger_score": float(np.max(trigger_score)),
        "peak_trigger_time_ms": float(time_axis_ms[int(np.argmax(trigger_score))]),
        "raw_iq_bytes": int(raw_bytes),
        "full_power_uint12_stored_as_uint16_bytes": int(full_power_bytes),
        "summary_plus_trigger_snippets_bytes": int(downlink_bytes),
        "reduction_vs_raw_iq": float(raw_bytes / downlink_bytes),
        "reduction_vs_full_power": float(full_power_bytes / downlink_bytes),
    }

    args.plot.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=False)

    im0 = axes[0].imshow(
        10 * np.log10(np.maximum(power, 1e-6)),
        aspect="auto",
        origin="lower",
        extent=[freq_axis_khz[0], freq_axis_khz[-1], time_axis_ms[0], time_axis_ms[-1]],
        cmap="viridis",
    )
    axes[0].set_ylabel("time (ms)")
    axes[0].set_title("Raw channelized power")
    fig.colorbar(im0, ax=axes[0], label="dB")

    im1 = axes[1].imshow(
        10 * np.log10(np.maximum(masked, 1e-6)),
        aspect="auto",
        origin="lower",
        extent=[freq_axis_khz[0], freq_axis_khz[-1], time_axis_ms[0], time_axis_ms[-1]],
        cmap="viridis",
    )
    axes[1].set_ylabel("time (ms)")
    axes[1].set_title(f"After RFI mask ({np.count_nonzero(~mask)} channels removed)")
    fig.colorbar(im1, ax=axes[1], label="dB")

    axes[2].plot(time_axis_ms, trigger_score, lw=1.2)
    axes[2].axhline(trigger_threshold, color="tab:red", ls="--", lw=1.0, label="trigger threshold")
    if trigger_frames.size:
        axes[2].scatter(time_axis_ms[trigger_frames], trigger_score[trigger_frames], s=18, color="tab:red")
    axes[2].set_xlabel("time (ms)")
    axes[2].set_ylabel("robust S/N")
    axes[2].set_title("Onboard event trigger score")
    axes[2].legend(loc="upper right")

    fig.tight_layout()
    fig.savefig(args.plot, dpi=160)
    plt.close(fig)

    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
