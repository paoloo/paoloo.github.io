#!/usr/bin/env python3
"""Validate tiny VLM-style robot action proposals without hardware."""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ACTIONS = {"stop", "move_forward", "turn_left", "turn_right", "inspect"}
SCENES = [
    {"name": "clear_workbench_left", "front_distance_m": 0.9, "target_side": "left", "proposal": {"action": "turn_left", "reason": "workbench visible on the left"}},
    {"name": "obstacle_front", "front_distance_m": 0.22, "target_side": "front", "proposal": {"action": "move_forward", "reason": "target appears ahead"}},
    {"name": "invalid_action", "front_distance_m": 0.8, "target_side": "right", "proposal": {"action": "approach_target", "reason": "move closer to target"}},
    {"name": "low_battery", "front_distance_m": 1.2, "target_side": "right", "battery": 12, "proposal": {"action": "turn_right", "reason": "target is on the right"}},
]


def validate(scene):
    action = scene["proposal"].get("action")
    if action not in ACTIONS:
        return "rejected", f"invalid action: {action}"
    if scene.get("battery", 70) < 15 and action != "stop":
        return "rejected", "battery too low for movement"
    if scene["front_distance_m"] < 0.35 and action == "move_forward":
        return "rejected", "obstacle too close"
    return "accepted", "action inside bounds"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--plot", type=Path, default=Path("uploads/2026/03/vlm-robot-operator.png"))
    p.add_argument("--json", type=Path, default=Path("/tmp/vlm-robot-operator.json"))
    args = p.parse_args()
    results = []
    for s in SCENES:
        status, reason = validate(s)
        results.append({**s, "status": status, "validation_reason": reason})
    counts = {"accepted": sum(r["status"] == "accepted" for r in results), "rejected": sum(r["status"] == "rejected" for r in results)}
    args.plot.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 4, figsize=(12, 3))
    for ax, r in zip(axes, results):
        ax.set_title(f"{r['name']}\n{r['status']}")
        ax.set_xlim(-1, 1)
        ax.set_ylim(0, 1.5)
        ax.scatter([0], [0], marker="^", s=120, label="robot")
        if r["target_side"] == "left":
            target = (-0.7, 1.0)
        elif r["target_side"] == "right":
            target = (0.7, 1.0)
        else:
            target = (0.0, r["front_distance_m"])
        ax.scatter([target[0]], [target[1]], s=90, label="target")
        ax.add_patch(plt.Circle((0, r["front_distance_m"]), 0.08, color="tab:red", alpha=0.35))
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(args.plot, dpi=160)
    plt.close(fig)
    out = {"counts": counts, "results": results}
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
