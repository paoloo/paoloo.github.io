#!/usr/bin/env python3
"""Anomaly scoring over synthetic SETI-like waterfalls."""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.ensemble import IsolationForest


def noise(rng, nf=128, nt=256):
    return rng.normal(0, 1, (nf, nt)).astype(np.float32)


def drifting_tone(w, start=40, drift=0.12, amp=6.0):
    out = w.copy()
    for t in range(out.shape[1]):
        f = int(round(start + drift * t))
        if 0 <= f < out.shape[0]:
            out[f, t] += amp
    return out


def broadband_burst(w, center=140, width=5, amp=3.5):
    out = w.copy()
    t = np.arange(out.shape[1])
    profile = amp * np.exp(-0.5 * ((t - center) / width) ** 2)
    out += profile[None, :]
    return out


def features(w):
    spectrum = w.mean(axis=1)
    ts = w.mean(axis=0)
    return np.array([
        w.max(),
        np.percentile(w, 99.9),
        spectrum.max(),
        ts.max(),
        np.std(spectrum),
        np.std(ts),
    ])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--plot", type=Path, default=Path("uploads/2026/03/technosignature-anomaly.png"))
    p.add_argument("--json", type=Path, default=Path("/tmp/technosignature-anomaly.json"))
    args = p.parse_args()
    rng = np.random.default_rng(19)
    train = np.array([features(noise(rng)) for _ in range(800)])
    model = IsolationForest(contamination=0.03, random_state=19).fit(train)
    examples = {
        "plain_noise": noise(rng),
        "drifting_narrowband": drifting_tone(noise(rng)),
        "broadband_burst": broadband_burst(noise(rng)),
    }
    scores = {k: float(-model.score_samples([features(v)])[0]) for k, v in examples.items()}
    ranked = sorted(scores, key=scores.get, reverse=True)

    args.plot.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    for ax, name in zip(axes, examples):
        ax.imshow(examples[name], aspect="auto", origin="lower", cmap="viridis", vmin=-2, vmax=6)
        ax.set_title(f"{name}\nscore={scores[name]:.3f}")
        ax.set_xlabel("time")
    axes[0].set_ylabel("frequency")
    fig.tight_layout()
    fig.savefig(args.plot, dpi=160)
    plt.close(fig)

    out = {"scores": scores, "ranked": ranked}
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
