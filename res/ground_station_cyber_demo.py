#!/usr/bin/env python3
"""Ground-station command path validation demo."""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


PROPOSALS = [
    {"id": "rx-telemetry", "zone": "planning", "operation": "receive_telemetry", "commanding": False, "signed": False, "operator_go": False},
    {"id": "payload-downlink", "zone": "planning", "operation": "start_downlink", "commanding": True, "signed": True, "operator_go": True},
    {"id": "unsigned-uplink", "zone": "execution", "operation": "set_payload_mode", "commanding": True, "signed": False, "operator_go": True},
    {"id": "agent-direct-command", "zone": "planning", "operation": "raw_uplink", "commanding": True, "signed": True, "operator_go": False},
    {"id": "maintenance-lock", "zone": "execution", "operation": "start_downlink", "commanding": True, "signed": True, "operator_go": True, "maintenance_lock": True},
]


def validate(p):
    if p.get("maintenance_lock"):
        return "rejected", "station locked for maintenance"
    if p["operation"] == "raw_uplink":
        return "rejected", "raw uplink is not exposed to agents"
    if p["commanding"] and not p["signed"]:
        return "rejected", "commanding proposal is unsigned"
    if p["commanding"] and not p["operator_go"]:
        return "rejected", "missing operator authorization"
    if p["commanding"] and p["zone"] != "execution":
        return "needs_handoff", "valid command proposal must move through execution zone"
    return "accepted", "receive-only or authorized operation"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plot", type=Path, default=Path("uploads/2026/03/ground-station-cyber.png"))
    parser.add_argument("--json", type=Path, default=Path("/tmp/ground-station-cyber.json"))
    args = parser.parse_args()
    results = []
    for p in PROPOSALS:
        status, reason = validate(p)
        results.append({**p, "status": status, "reason": reason})
    counts = {s: sum(r["status"] == s for r in results) for s in ("accepted", "needs_handoff", "rejected")}
    args.plot.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.bar(counts.keys(), counts.values(), color=["tab:green", "tab:orange", "tab:red"])
    ax.set_ylabel("proposals")
    ax.set_title("Ground-station command-path validation")
    for i, (k, v) in enumerate(counts.items()):
        ax.text(i, v + 0.05, str(v), ha="center")
    fig.tight_layout()
    fig.savefig(args.plot, dpi=160)
    plt.close(fig)
    out = {"counts": counts, "results": results}
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
