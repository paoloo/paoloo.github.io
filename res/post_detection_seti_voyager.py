#!/usr/bin/env python3
"""Extract a post-detection candidate record from the Voyager 1 BL HDF5 file."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import hdf5plugin  # noqa: F401 - registers HDF5 compression filters
import h5py
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from astropy.time import Time


SOURCE_URL = "http://blpd0.ssl.berkeley.edu/Voyager_data/Voyager1.single_coarse.fine_res.h5"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def robust_sigma(values: np.ndarray) -> tuple[float, float]:
    median = float(np.nanmedian(values))
    mad = float(np.nanmedian(np.abs(values - median)))
    return median, 1.4826 * mad


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "h5",
        type=Path,
        help="Path to Voyager1.single_coarse.fine_res.h5",
    )
    parser.add_argument(
        "--plot",
        type=Path,
        default=Path("uploads/2026/06/voyager1-post-detection-candidate.png"),
    )
    parser.add_argument(
        "--json",
        type=Path,
        default=Path("/tmp/voyager1-post-detection-candidate.json"),
    )
    parser.add_argument("--f-start", type=float, default=8419.296)
    parser.add_argument("--f-stop", type=float, default=8419.298)
    parser.add_argument("--half-width", type=int, default=160)
    args = parser.parse_args()

    with h5py.File(args.h5, "r") as f:
        data = np.squeeze(f["data"][...])
        attrs = dict(f["data"].attrs)

    if data.ndim != 2:
        raise ValueError(f"expected a 2-D time/frequency array, got {data.shape}")

    # Breakthrough Listen HDF5 files commonly store data as time x frequency.
    n_integrations, n_channels = data.shape

    fch1_mhz = float(attrs["fch1"])
    foff_mhz = float(attrs["foff"])
    tsamp_s = float(attrs["tsamp"])
    tstart_mjd = float(attrs["tstart"])
    source_name = attrs["source_name"]
    rawdatafile = attrs["rawdatafile"]

    freq_axis_all_mhz = fch1_mhz + np.arange(n_channels) * foff_mhz
    search = (
        (freq_axis_all_mhz >= min(args.f_start, args.f_stop))
        & (freq_axis_all_mhz <= max(args.f_start, args.f_stop))
    )
    search_ch = np.arange(n_channels)[search]
    if len(search_ch) == 0:
        raise ValueError("frequency search window contains no channels")

    sub = data[:, search]
    peak_rel = np.nanargmax(sub, axis=1)
    peak_ch = search_ch[peak_rel]
    peak_val = data[np.arange(n_integrations), peak_ch]
    peak_freq_mhz = fch1_mhz + peak_ch * foff_mhz
    time_s = np.arange(n_integrations) * tsamp_s
    drift_hz_s = float(np.polyfit(time_s, peak_freq_mhz * 1e6, 1)[0])

    median, sigma = robust_sigma(data)
    snr_like = (peak_val - median) / sigma
    candidate_channel = int(np.median(peak_ch))
    candidate_freq_mhz = float(fch1_mhz + candidate_channel * foff_mhz)

    lo = max(0, candidate_channel - args.half_width)
    hi = min(n_channels, candidate_channel + args.half_width + 1)
    cut = data[:, lo:hi]
    freq_axis_mhz = fch1_mhz + np.arange(lo, hi) * foff_mhz
    freq_offset_khz = (freq_axis_mhz - candidate_freq_mhz) * 1e3
    if freq_offset_khz[0] > freq_offset_khz[-1]:
        freq_offset_khz = freq_offset_khz[::-1]
        cut = cut[:, ::-1]
    time_axis_s = time_s

    args.plot.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 4.8))
    image = ax.imshow(
        np.log10(np.maximum(cut, 1.0)),
        aspect="auto",
        origin="lower",
        extent=[
            freq_offset_khz[0],
            freq_offset_khz[-1],
            time_axis_s[0],
            time_axis_s[-1] + tsamp_s,
        ],
        cmap="viridis",
    )
    ax.axvline(0.0, color="white", lw=0.8, alpha=0.7)
    ax.set_xlabel("frequency offset from peak (kHz)")
    ax.set_ylabel("time since start (s)")
    ax.set_title("Voyager 1 narrowband signal candidate cutout")
    fig.colorbar(image, ax=ax, label="log10 power")
    fig.tight_layout()
    fig.savefig(args.plot, dpi=160)
    plt.close(fig)

    candidate = {
        "candidate_id": "voyager1-57650-0001",
        "source_url": SOURCE_URL,
        "source_name": source_name,
        "rawdatafile": rawdatafile,
        "timestamp_mjd": tstart_mjd,
        "timestamp_utc": Time(tstart_mjd, format="mjd").isot,
        "n_integrations": n_integrations,
        "n_channels": n_channels,
        "tsamp_s": tsamp_s,
        "fch1_mhz": fch1_mhz,
        "foff_hz": foff_mhz * 1e6,
        "search_f_start_mhz": args.f_start,
        "search_f_stop_mhz": args.f_stop,
        "frequency_hz": candidate_freq_mhz * 1e6,
        "peak_channel": candidate_channel,
        "peak_channel_min": int(np.min(peak_ch)),
        "peak_channel_max": int(np.max(peak_ch)),
        "drift_hz_s": drift_hz_s,
        "global_median": median,
        "robust_sigma": sigma,
        "snr_like_min": float(np.min(snr_like)),
        "snr_like_max": float(np.max(snr_like)),
        "sha256": sha256_file(args.h5),
        "plot": str(args.plot),
        "status": "known_transmitter",
    }

    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(candidate, indent=2) + "\n")
    print(json.dumps(candidate, indent=2))


if __name__ == "__main__":
    main()
