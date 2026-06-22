#!/usr/bin/env python3
"""Validate and simulate LLM-drafted CubeSat flight rules."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ALLOWED_ACTIONS = {
    "enter_safe_mode",
    "disable_payload",
    "request_downlink",
    "defer_operation",
    "notify_operator",
}

ALLOWED_FIELDS = {
    "battery_soc",
    "temp_obc_c",
    "downlink_window",
    "payload_enabled",
}

ALLOWED_OPERATORS = {"<", ">", "<=", ">=", "==", "!="}

VALID_STATES = {
    "draft": {"schema_valid", "rejected"},
    "schema_valid": {"simulation_passed", "simulation_failed", "rejected"},
    "simulation_passed": {"ready_for_human_review"},
    "simulation_failed": {"rejected"},
    "ready_for_human_review": {"approved", "rejected"},
}


@dataclass(frozen=True)
class Telemetry:
    minute: int
    battery_soc: float
    temp_obc_c: float
    downlink_window: bool
    payload_enabled: bool


def transition(rule: dict, new_state: str, reason: str, events: list[dict]) -> None:
    old_state = rule["state"]
    if new_state not in VALID_STATES[old_state]:
        raise ValueError(f"invalid transition {old_state} -> {new_state}")
    rule["state"] = new_state
    events.append({
        "rule": rule["name"],
        "old_state": old_state,
        "new_state": new_state,
        "reason": reason,
    })


def validate_rule(rule: dict) -> tuple[bool, str]:
    required = {"name", "condition", "action", "requires_human_go", "rationale"}
    missing = sorted(required - set(rule))
    if missing:
        return False, f"missing required fields: {', '.join(missing)}"

    condition = rule["condition"]
    for field in ("field", "operator", "value"):
        if field not in condition:
            return False, f"condition missing {field}"

    if condition["field"] not in ALLOWED_FIELDS:
        return False, f"unknown telemetry field: {condition['field']}"
    if condition["operator"] not in ALLOWED_OPERATORS:
        return False, f"unsupported operator: {condition['operator']}"
    if rule["action"] not in ALLOWED_ACTIONS:
        return False, f"unknown action: {rule['action']}"
    if rule.get("requires_human_go") is not True:
        return False, "missing human authorization gate"

    if rule["action"] == "enter_safe_mode" and condition["field"] == "battery_soc":
        if condition["operator"] in {"<", "<="} and float(condition["value"]) < 15:
            return False, "safe-mode battery threshold is too late for this policy"

    return True, "schema and policy checks passed"


def eval_condition(rule: dict, sample: Telemetry) -> bool:
    condition = rule["condition"]
    value = getattr(sample, condition["field"])
    threshold = condition["value"]
    op = condition["operator"]

    if op == "<":
        return value < threshold
    if op == "<=":
        return value <= threshold
    if op == ">":
        return value > threshold
    if op == ">=":
        return value >= threshold
    if op == "==":
        return value == threshold
    if op == "!=":
        return value != threshold
    raise ValueError(op)


def simulate_rule(rule: dict, telemetry: list[Telemetry]) -> tuple[bool, str, int | None]:
    fire_minute = None
    for sample in telemetry:
        if eval_condition(rule, sample):
            fire_minute = sample.minute
            break

    if fire_minute is None:
        return False, "rule never fired during the anomaly", None

    # The anomaly crosses a soft safety boundary at 22 percent while payload is still on.
    if rule["action"] == "disable_payload" and fire_minute <= 30:
        return True, f"payload would be disabled at t={fire_minute} min", fire_minute
    if rule["action"] == "enter_safe_mode" and fire_minute <= 40:
        return True, f"safe mode would be requested at t={fire_minute} min", fire_minute
    if rule["action"] in {"notify_operator", "request_downlink", "defer_operation"}:
        return False, f"{rule['action']} does not reduce payload power", fire_minute

    return False, f"action {rule['action']} fired too late at t={fire_minute} min", fire_minute


def candidate_rules() -> list[dict]:
    return [
        {
            "name": "disable_payload_low_battery",
            "state": "draft",
            "condition": {"field": "battery_soc", "operator": "<", "value": 22},
            "action": "disable_payload",
            "requires_human_go": True,
            "rationale": "Payload load should be removed before battery state reaches safe-mode margin.",
        },
        {
            "name": "notify_operator_low_battery",
            "state": "draft",
            "condition": {"field": "battery_soc", "operator": "<", "value": 22},
            "action": "notify_operator",
            "requires_human_go": True,
            "rationale": "Notify the operator when the battery drops below the payload-off threshold.",
        },
        {
            "name": "turn_off_payload_low_battery",
            "state": "draft",
            "condition": {"field": "battery_soc", "operator": "<", "value": 20},
            "action": "turn_off_payload",
            "requires_human_go": True,
            "rationale": "Reduce load by turning off the payload.",
        },
        {
            "name": "disable_payload_without_go",
            "state": "draft",
            "condition": {"field": "battery_soc", "operator": "<", "value": 22},
            "action": "disable_payload",
            "requires_human_go": False,
            "rationale": "Disable the payload automatically on low battery.",
        },
    ]


def telemetry_series() -> list[Telemetry]:
    return [
        Telemetry(0, 31, 39, False, True),
        Telemetry(10, 27, 40, False, True),
        Telemetry(20, 23, 42, False, True),
        Telemetry(30, 20, 43, False, True),
        Telemetry(40, 17, 44, False, True),
        Telemetry(50, 14, 45, False, True),
    ]


def plot(telemetry: list[Telemetry], accepted_fire_minute: int | None, path: Path) -> None:
    minutes = [t.minute for t in telemetry]
    battery = [t.battery_soc for t in telemetry]
    temp = [t.temp_obc_c for t in telemetry]

    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax1 = plt.subplots(figsize=(9, 4.8))
    ax1.plot(minutes, battery, marker="o", label="battery state of charge")
    ax1.axhline(22, color="tab:orange", ls="--", lw=1.2, label="payload-off threshold")
    ax1.axhline(15, color="tab:red", ls="--", lw=1.2, label="safe-mode margin")
    if accepted_fire_minute is not None:
        ax1.axvline(accepted_fire_minute, color="tab:green", lw=1.4, label="accepted rule fires")
    ax1.set_xlabel("time since anomaly start (min)")
    ax1.set_ylabel("battery state of charge (%)")
    ax1.set_ylim(0, 35)

    ax2 = ax1.twinx()
    ax2.plot(minutes, temp, color="tab:purple", marker="s", alpha=0.7, label="OBC temperature")
    ax2.set_ylabel("OBC temperature (C)")
    ax2.set_ylim(35, 50)

    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc="upper right")
    ax1.set_title("Telemetry anomaly and accepted flight-rule trigger")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plot", type=Path, default=Path("uploads/2026/06/llm-flight-rule-validator.png"))
    parser.add_argument("--json", type=Path, default=Path("/tmp/llm-flight-rule-validator.json"))
    args = parser.parse_args()

    telemetry = telemetry_series()
    rules = candidate_rules()
    events: list[dict] = []
    accepted_fire_minute = None

    for rule in rules:
        ok, reason = validate_rule(rule)
        if not ok:
            transition(rule, "rejected", reason, events)
            continue

        transition(rule, "schema_valid", reason, events)
        sim_ok, sim_reason, fire_minute = simulate_rule(rule, telemetry)
        if sim_ok:
            transition(rule, "simulation_passed", sim_reason, events)
            transition(rule, "ready_for_human_review", "simulation passed; awaiting operator review", events)
            accepted_fire_minute = fire_minute
        else:
            transition(rule, "simulation_failed", sim_reason, events)
            transition(rule, "rejected", "simulation failed", events)

    summary = {
        "rules_tested": len(rules),
        "schema_passed": len({
            e["rule"]
            for e in events
            if e["new_state"] == "schema_valid"
        }),
        "simulation_passed": sum(1 for r in rules if r["state"] == "ready_for_human_review"),
        "ready_for_human_review": [r["name"] for r in rules if r["state"] == "ready_for_human_review"],
        "rejected": [r["name"] for r in rules if r["state"] == "rejected"],
        "accepted_fire_minute": accepted_fire_minute,
        "final_states": {r["name"]: r["state"] for r in rules},
        "events": events,
    }

    plot(telemetry, accepted_fire_minute, args.plot)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
