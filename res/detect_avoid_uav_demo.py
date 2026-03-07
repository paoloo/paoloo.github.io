#!/usr/bin/env python3
"""Small detect-and-avoid simulation for UAV encounters."""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def rotate(v, degrees):
    a = np.deg2rad(degrees)
    r = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
    return r @ v


def cpa(own_xy, own_v, intr_xy, intr_v):
    r = intr_xy - own_xy
    v = intr_v - own_v
    vv = float(np.dot(v, v))
    if vv == 0:
        return 0.0, float(np.linalg.norm(r))
    t = max(0.0, -float(np.dot(r, v)) / vv)
    d = float(np.linalg.norm(r + v * t))
    return t, d


def run(sensor):
    own_xy = np.array([0.0, 0.0])
    own_v = np.array([28.0, 0.0])
    intr_xy = np.array([2200.0, -420.0])
    intr_v = np.array([-38.0, 8.0])
    dt = 1.0
    detected = None
    avoided = None
    distances = []
    t_cpas = []
    d_cpas = []
    bearing_history = []

    for step in range(95):
        t = step * dt
        dist = float(np.linalg.norm(intr_xy - own_xy))
        distances.append(dist)
        tc, dc = cpa(own_xy, own_v, intr_xy, intr_v)
        t_cpas.append(tc)
        d_cpas.append(dc)

        visible = False
        if sensor == "adsb":
            visible = True
        elif sensor == "camera":
            bearing = np.arctan2(*(intr_xy - own_xy)[::-1])
            visible = dist < 950 and abs(bearing) < np.deg2rad(40)
            if visible:
                bearing_history.append(bearing)
        elif sensor == "fused":
            bearing = np.arctan2(*(intr_xy - own_xy)[::-1])
            visible = True or (dist < 950 and abs(bearing) < np.deg2rad(40))

        if visible and detected is None:
            detected = t
        if visible and avoided is None and 0 < tc < 55 and dc < 180:
            own_v = rotate(own_v, 28)
            avoided = t

        own_xy = own_xy + own_v * dt
        intr_xy = intr_xy + intr_v * dt

    return {
        "sensor": sensor,
        "detected_s": detected,
        "avoided_s": avoided,
        "min_distance_m": float(np.min(distances)),
        "min_predicted_cpa_m": float(np.min(d_cpas)),
        "distances": distances,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--plot", type=Path, default=Path("uploads/2026/03/uav-detect-avoid.png"))
    p.add_argument("--json", type=Path, default=Path("/tmp/uav-detect-avoid.json"))
    args = p.parse_args()

    runs = [run(s) for s in ("adsb", "camera", "fused")]
    args.plot.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 4.8))
    for r in runs:
        ax.plot(r["distances"], label=f"{r['sensor']} min={r['min_distance_m']:.0f} m")
        if r["avoided_s"] is not None:
            ax.axvline(r["avoided_s"], lw=0.8, alpha=0.5)
    ax.axhline(120, color="tab:red", ls="--", label="120 m separation")
    ax.set_xlabel("time (s)")
    ax.set_ylabel("ownship-intruder distance (m)")
    ax.set_title("Detect-and-avoid timing changes closest approach")
    ax.legend()
    fig.tight_layout()
    fig.savefig(args.plot, dpi=160)
    plt.close(fig)

    summary = {r["sensor"]: {k: v for k, v in r.items() if k != "distances"} for r in runs}
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
