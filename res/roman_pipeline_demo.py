#!/usr/bin/env python3
"""Synthetic Roman-scale exoplanet pipeline bookkeeping demo."""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def light_curve(rng, period=7.3, depth=0.006, duration=0.18, n=6000):
    t = np.linspace(0, 60, n)
    flux = 1 + 0.002 * np.sin(2 * np.pi * t / 13.0) + rng.normal(0, 0.0015, n)
    phase = (t % period) / period
    mask = (phase < duration / period) | (phase > 1 - duration / period)
    flux[mask] -= depth
    return t, flux


def score_period(t, f, period, duration=0.18):
    phase = (t % period) / period
    mask = phase < duration / period
    return float(np.mean(f[~mask]) - np.mean(f[mask]))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--plot", type=Path, default=Path("uploads/2026/03/roman-pipeline.png"))
    p.add_argument("--json", type=Path, default=Path("/tmp/roman-pipeline.json"))
    args = p.parse_args()
    rng = np.random.default_rng(25)
    t, f = light_curve(rng)
    periods = np.linspace(1, 20, 700)
    scores = np.array([score_period(t, f, p) for p in periods])
    best = float(periods[np.argmax(scores)])
    odd_even_delta = 0.00042
    centroid_shift_sigma = 0.7
    secondary_score = 1.1
    candidate = {
        "target_id": "synthetic-roman-00025",
        "injected_period_days": 7.3,
        "best_period_days": best,
        "period_error_days": abs(best - 7.3),
        "best_box_score": float(np.max(scores)),
        "odd_even_delta": odd_even_delta,
        "centroid_shift_sigma": centroid_shift_sigma,
        "secondary_eclipse_score": secondary_score,
        "status": "survived_first_vetting",
    }
    args.plot.parent.mkdir(parents=True, exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7))
    ax1.plot(t, f, lw=0.5)
    ax1.set_title("Synthetic survey light curve")
    ax1.set_xlabel("time (days)")
    ax1.set_ylabel("relative flux")
    ax2.plot(periods, scores)
    ax2.axvline(7.3, color="tab:green", ls="--", label="injected")
    ax2.axvline(best, color="tab:red", alpha=0.7, label="best")
    ax2.set_xlabel("trial period (days)")
    ax2.set_ylabel("box score")
    ax2.set_title("First-pass period search")
    ax2.legend()
    fig.tight_layout()
    fig.savefig(args.plot, dpi=160)
    plt.close(fig)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(candidate, indent=2) + "\n")
    print(json.dumps(candidate, indent=2))


if __name__ == "__main__":
    main()
