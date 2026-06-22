---
title: "Can an LLM Write a Flight Rule Without Becoming the Flight Rule?"
date: 2026-06-22 12:00:00 -0300
author: paolo
layout: post
permalink: /2026/06/22/can-an-llm-write-a-flight-rule/
categories:
  - en-US
tags:
  - llm
  - avionics
  - cubesat
  - safety
  - python
---

A flight rule is a compact piece of operational authority. It says what the team does when a condition occurs. That makes LLMs tempting: give the model telemetry, anomaly notes, and operator context, and ask it to draft a rule.

The boundary is the dangerous part. A model can write a proposed flight rule. It cannot become the flight rule.

I tested that boundary with a small local harness. No API call was needed. I treated four JSON objects as if they were candidate rules drafted by a model, then passed them through a schema checker, a policy checker, and a tiny simulator.

The script is in:

```text
res/llm_flight_rule_validator_demo.py
```

I ran it with:

```bash
MPLCONFIGDIR=/tmp/mplconfig \
conda run -n exohunter python res/llm_flight_rule_validator_demo.py \
  --plot uploads/2026/06/llm-flight-rule-validator.png \
  --json /tmp/llm-flight-rule-validator.json
```

The result was useful because three plausible-looking rules failed for different reasons.

## The anomaly

The simulated telemetry is a small CubeSat-like case: battery state of charge is falling, the payload is still enabled, there is no downlink window, and the onboard computer temperature is rising.

```text
minute  battery_soc  temp_obc_c  downlink_window  payload_enabled
0       31           39          false            true
10      27           40          false            true
20      23           42          false            true
30      20           43          false            true
40      17           44          false            true
50      14           45          false            true
```

The policy I used was simple: if the battery drops below `22%` while the payload is on, a good rule needs to reduce payload power before the spacecraft reaches the `15%` safe-mode margin.

That is not a full spacecraft power model. It is enough to test the difference between a rule that sounds reasonable and a rule that changes the outcome.

## The rule format

The candidate rule format is deliberately strict:

```json
{
  "name": "disable_payload_low_battery",
  "state": "draft",
  "condition": {
    "field": "battery_soc",
    "operator": "<",
    "value": 22
  },
  "action": "disable_payload",
  "requires_human_go": true,
  "rationale": "Payload load should be removed before battery state reaches safe-mode margin."
}
```

The allowed actions are fixed:

```python
ALLOWED_ACTIONS = {
    "enter_safe_mode",
    "disable_payload",
    "request_downlink",
    "defer_operation",
    "notify_operator",
}
```

This is the first boundary. The model can propose text, but the system accepts only known actions. `turn_off_payload` may be clear to a human, but it is not a valid command in this interface.

## Validation before simulation

The validator checks the rule shape, allowed telemetry fields, allowed operators, allowed actions, and the human authorization gate:

```python
def validate_rule(rule):
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

    return True, "schema and policy checks passed"
```

That catches two failure modes immediately:

```text
turn_off_payload_low_battery -> rejected
reason: unknown action: turn_off_payload

disable_payload_without_go -> rejected
reason: missing human authorization gate
```

Both are believable LLM mistakes. One uses a phrase that sounds right but is not part of the command vocabulary. The other quietly removes the operator gate.

## Simulation catches the subtler failure

One rule passed schema validation but still failed:

```json
{
  "name": "notify_operator_low_battery",
  "condition": {
    "field": "battery_soc",
    "operator": "<",
    "value": 22
  },
  "action": "notify_operator",
  "requires_human_go": true
}
```

It is syntactically valid. It has a human authorization gate. It fires at the right threshold. It still does not reduce payload power.

The simulator applies each candidate rule to the telemetry:

```python
def simulate_rule(rule, telemetry):
    fire_minute = None
    for sample in telemetry:
        if eval_condition(rule, sample):
            fire_minute = sample.minute
            break

    if fire_minute is None:
        return False, "rule never fired during the anomaly", None

    if rule["action"] == "disable_payload" and fire_minute <= 30:
        return True, f"payload would be disabled at t={fire_minute} min", fire_minute
    if rule["action"] in {"notify_operator", "request_downlink", "defer_operation"}:
        return False, f"{rule['action']} does not reduce payload power", fire_minute
```

The simulator rejected the notification rule:

```text
notify_operator_low_battery
schema_valid -> simulation_failed
reason: notify_operator does not reduce payload power
```

That is the kind of failure I care about. The rule is well-formed, but it does not solve the operational problem.

## The one rule that survived

Only one rule reached human review:

```json
{
  "name": "disable_payload_low_battery",
  "condition": {
    "field": "battery_soc",
    "operator": "<",
    "value": 22
  },
  "action": "disable_payload",
  "requires_human_go": true
}
```

It fires at `t = 30 min`, when battery state of charge has dropped to `20%`. That is after crossing the `22%` payload-off threshold but before the `15%` safe-mode margin.

<figure class="wp-block-image"><img src="{{ site.baseurl }}/uploads/2026/06/llm-flight-rule-validator.png" alt="Battery and temperature telemetry with an accepted flight-rule trigger at 30 minutes" /><figcaption>The accepted rule fires before the safe-mode margin. The notification-only rule also fires near this point, but it fails simulation because it does not reduce payload power.</figcaption></figure>

The reduced output from the run was:

```json
{
  "rules_tested": 4,
  "schema_passed": 2,
  "simulation_passed": 1,
  "ready_for_human_review": [
    "disable_payload_low_battery"
  ],
  "rejected": [
    "notify_operator_low_battery",
    "turn_off_payload_low_battery",
    "disable_payload_without_go"
  ],
  "accepted_fire_minute": 30
}
```

This is the outcome I wanted: the system rejected one invalid action, one missing authorization gate, and one valid-but-ineffective rule. It kept one rule as a proposal for human review.

## Draft is not active

I used a small state machine to keep authority explicit:

```python
VALID_STATES = {
    "draft": {"schema_valid", "rejected"},
    "schema_valid": {"simulation_passed", "simulation_failed", "rejected"},
    "simulation_passed": {"ready_for_human_review"},
    "simulation_failed": {"rejected"},
    "ready_for_human_review": {"approved", "rejected"},
}
```

That last state matters. `ready_for_human_review` is not `approved`. A model-drafted rule can pass schema validation and simulation and still remain inactive.

For spacecraft, UAVs, and ground stations, this is the boundary I would keep:

```text
LLM drafts
schema validates
simulator tests
operator reviews
configuration control publishes
flight software executes
```

The LLM is useful at turning messy context into a structured proposal. The validator and simulator are useful because they are boring and strict. The operator keeps authority.

## What this is not

This is not a flight-ready rule engine. It is not formal verification, and it is not a replacement for subsystem ownership, operations review, or configuration control.

It is a small test of the interface I would want around an LLM. The model can propose. The system can reject. Nothing becomes operational until a human process says so.

## Why this matters

LLMs are good at turning messy operational context into structured language. That is valuable in space systems, UAVs, labs, and ground stations. The mistake is letting that fluency blur the line between proposal and permission.

The useful part of this experiment was not that one rule survived. It was that the harness rejected three other rules for specific, auditable reasons. That is the pattern I would trust: not an LLM writing flight rules, but an LLM drafting candidates inside a system that can say no.
