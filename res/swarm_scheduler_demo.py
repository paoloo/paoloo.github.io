#!/usr/bin/env python3
"""Greedy vs exhaustive small swarm scheduler."""

import argparse
import itertools
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


VEHICLES = {
    "uav-1": {"start": np.array([0.0, 0.0]), "battery_min": 38},
    "uav-2": {"start": np.array([0.0, 0.0]), "battery_min": 34},
    "uav-3": {"start": np.array([0.0, 0.0]), "battery_min": 30},
}

TASKS = [
    {"name": "antenna", "xy": np.array([1200.0, 200.0]), "reward": 20, "service": 4},
    {"name": "roof", "xy": np.array([700.0, 900.0]), "reward": 16, "service": 5},
    {"name": "solar", "xy": np.array([-500.0, 1100.0]), "reward": 18, "service": 6},
    {"name": "tower", "xy": np.array([-1000.0, -300.0]), "reward": 14, "service": 4},
    {"name": "gate", "xy": np.array([500.0, -900.0]), "reward": 10, "service": 3},
    {"name": "dish", "xy": np.array([1500.0, -700.0]), "reward": 22, "service": 7},
]


def travel(a, b, speed=180.0):
    return float(np.linalg.norm(a - b) / speed)


def route_cost(vehicle, route):
    pos = VEHICLES[vehicle]["start"]
    cost = 0.0
    for task in route:
        cost += travel(pos, task["xy"]) + task["service"]
        pos = task["xy"]
    return cost


def reward(route):
    return sum(t["reward"] for t in route)


def greedy():
    remaining = TASKS[:]
    routes = {v: [] for v in VEHICLES}
    while True:
        best = None
        for v in VEHICLES:
            for task in remaining:
                trial = routes[v] + [task]
                cost = route_cost(v, trial)
                if cost <= VEHICLES[v]["battery_min"]:
                    score = task["reward"] / max(cost - route_cost(v, routes[v]), 1e-6)
                    if best is None or score > best[0]:
                        best = (score, v, task)
        if best is None:
            break
        _, v, task = best
        routes[v].append(task)
        remaining.remove(task)
    return routes


def exhaustive():
    best_routes = None
    best_reward = -1
    choices = list(VEHICLES) + ["skip"]
    for assign in itertools.product(choices, repeat=len(TASKS)):
        routes = {v: [] for v in VEHICLES}
        for task, dest in zip(TASKS, assign):
            if dest != "skip":
                routes[dest].append(task)
        feasible = all(route_cost(v, routes[v]) <= VEHICLES[v]["battery_min"] for v in VEHICLES)
        if not feasible:
            continue
        total = sum(reward(r) for r in routes.values())
        if total > best_reward:
            best_reward = total
            best_routes = {v: routes[v][:] for v in VEHICLES}
    return best_routes


def summarize(routes):
    return {
        "reward": sum(reward(r) for r in routes.values()),
        "tasks": sum(len(r) for r in routes.values()),
        "routes": {v: [t["name"] for t in r] for v, r in routes.items()},
        "cost_min": {v: route_cost(v, r) for v, r in routes.items()},
    }


def plot(routes, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.scatter([0], [0], marker="*", s=180, label="base")
    for task in TASKS:
        ax.scatter([task["xy"][0]], [task["xy"][1]], s=40)
        ax.text(task["xy"][0] + 30, task["xy"][1] + 30, task["name"])
    for v, route in routes.items():
        pts = [VEHICLES[v]["start"]] + [t["xy"] for t in route]
        pts = np.array(pts)
        ax.plot(pts[:, 0], pts[:, 1], marker="o", label=v)
    ax.set_title("Optimal small swarm task assignment")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.axis("equal")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--plot", type=Path, default=Path("uploads/2026/06/swarm-scheduler.png"))
    p.add_argument("--json", type=Path, default=Path("/tmp/swarm-scheduler.json"))
    args = p.parse_args()
    g = greedy()
    o = exhaustive()
    out = {"greedy": summarize(g), "optimal": summarize(o)}
    out["greedy_fraction_of_optimal"] = out["greedy"]["reward"] / out["optimal"]["reward"]
    plot(o, args.plot)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
