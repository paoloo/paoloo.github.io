#!/usr/bin/env python
"""LLM agent that plans the same schedule. Needs ANTHROPIC_API_KEY.

Reuses `passes` and `SLEW_GAP` from groundstation_schedule_demo.py. The LLM never
enforces the constraints -- the validator does, and feeds violations back.
"""
import json
from collections import defaultdict
from anthropic import Anthropic

SCHEDULE_TOOL = {
    "name": "submit_schedule",
    "description": "Submit the chosen set of contacts as a list of pass IDs. "
                   "No two chosen passes may overlap on the same station "
                   "(including a slew gap) or on the same satellite.",
    "input_schema": {
        "type": "object",
        "properties": {
            "pass_ids": {"type": "array", "items": {"type": "integer"},
                         "description": "IDs of the passes to schedule"},
        },
        "required": ["pass_ids"],
    },
}

PROMPT = (
    "You are scheduling ground-station contacts. Maximize total weighted "
    "contact time. Constraints: a station runs one contact at a time with a "
    "300-second slew gap between contacts; a satellite talks to one station at "
    "a time. Call submit_schedule with the pass IDs you choose. Here is the "
    "catalog of candidate passes (times in seconds from epoch):\n\n"
)


def check(passes, chosen, slew_gap=300):
    """Return a list of constraint violations for the chosen pass IDs."""
    violations = []
    by_station, by_sat = defaultdict(list), defaultdict(list)
    for i in chosen:
        p = passes[i]
        for j, (s, e) in by_station[p.station]:
            if not (p.end + slew_gap <= s or p.start >= e + slew_gap):
                violations.append(f"passes {i} and {j} overlap at station {p.station}")
        for j, (s, e) in by_sat[p.sat]:
            if not (p.end <= s or p.start >= e):
                violations.append(f"passes {i} and {j} overlap on satellite {p.sat}")
        by_station[p.station].append((i, (p.start, p.end)))
        by_sat[p.sat].append((i, (p.start, p.end)))
    return violations


def _tool_use(resp):
    return next(b for b in resp.content if b.type == "tool_use")


def llm_schedule(passes, max_rounds=4):
    client = Anthropic()
    catalog = [{"id": i, "sat": p.sat, "station": p.station,
                "start": round(p.start), "end": round(p.end),
                "weight": round(p.weight)} for i, p in enumerate(passes)]
    messages = [{"role": "user", "content": PROMPT + json.dumps(catalog)}]
    chosen = []
    for _ in range(max_rounds):
        resp = client.messages.create(
            model="claude-opus-4-8", max_tokens=8000,
            thinking={"type": "adaptive"},
            tools=[SCHEDULE_TOOL],
            tool_choice={"type": "tool", "name": "submit_schedule"},
            messages=messages)
        tu = _tool_use(resp)
        chosen = tu.input["pass_ids"]
        violations = check(passes, chosen)
        if not violations:
            return chosen
        messages.append({"role": "assistant", "content": resp.content})
        messages.append({"role": "user", "content": [{
            "type": "tool_result", "tool_use_id": tu.id,
            "content": "Infeasible. Fix these overlaps and resubmit:\n"
                       + "\n".join(violations)}]})
    return chosen


if __name__ == "__main__":
    from groundstation_schedule_demo import passes
    picked = llm_schedule(passes)
    weight = sum(passes[i].weight for i in picked)
    print(f"[agent] {len(picked)} contacts, weighted {weight:.0f}")
