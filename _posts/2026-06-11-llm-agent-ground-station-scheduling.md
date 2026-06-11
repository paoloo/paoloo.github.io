---
title: "An LLM Agent that Schedules a Ground Station"
date: 2026-06-11 12:00:00 -0300
author: paolo
layout: post
permalink: /2026/06/11/llm-agent-ground-station-scheduling/
categories:
  - en-US
tags:
  - machine-learning
  - llm
  - cubesat
  - python
---

A ground station can only talk to a satellite when the satellite is above the horizon. With several satellites and a few stations, deciding who gets which pass, for how long, and in what order is a constrained scheduling problem. This is the core of my master's work, so this post builds a small version of it: compute real passes, solve the schedule two ways that I can run and check here, and then wire up an LLM agent to plan the same problem.

The honest question is not "can an LLM schedule a satellite" but "where does it help, and where does it just add risk over a solver that already gives the optimum".

## The problem

I take twelve real low-Earth-orbit satellites (current TLEs from Celestrak, including the Brazilian SCD-1 and SCD-2) and two ground stations, Sao Paulo and Svalbard. Over a 24-hour window I compute every pass above 10 degrees elevation with `skyfield`.

```python
t, ev = sat.find_events(topos, t0, t1, altitude_degrees=10)
```

That gives 153 candidate passes. The constraints are simple and physical: a station runs one contact at a time, with a 5-minute slew-and-reconfigure gap between contacts, and a satellite can only talk to one station at a time. Each satellite has a downlink priority from 1 to 5, and the weight of a contact is its priority times its duration. The goal is to maximize total weighted contact time.

## Baseline one: the optimal solver

This is a weighted interval-scheduling problem with two no-overlap resources, and OR-Tools CP-SAT solves it exactly.

```python
for i, p in enumerate(passes):
    pres = model.NewBoolVar(f"p{i}")
    iv_station = model.NewOptionalIntervalVar(s, e - s + SLEW_GAP, e + SLEW_GAP, pres)
    iv_sat = model.NewOptionalIntervalVar(s, e - s, e, pres)
    by_station[p.station].append(iv_station)
    by_sat[p.sat].append(iv_sat)
for ivs in by_station.values(): model.AddNoOverlap(ivs)
for ivs in by_sat.values():     model.AddNoOverlap(ivs)
model.Maximize(sum(int(round(p.weight)) * present[i] for i, p in enumerate(passes)))
```

It returns a provably optimal schedule: 90 contacts, weighted objective 2245.

## Baseline two: greedy

The obvious heuristic is to sort passes by weight and take each one that still fits.

```python
for i in sorted(range(len(passes)), key=lambda i: passes[i].weight, reverse=True):
    if fits_station(p) and fits_sat(p):
        schedule.append(i)
```

Greedy gets 84 contacts, weighted 2207, which is 98.3% of the optimum. That is the useful baseline. Greedy is fast, simple, and almost always good, so any fancier method has to justify itself against "98% for ten lines of code".

<figure class="wp-block-image"><img src="{{ site.baseurl }}/uploads/2026/06/groundstation-schedule.png" alt="Gantt charts of the greedy and optimal ground-station schedules over 24 hours" /><figcaption>Greedy (top) and the optimal CP-SAT schedule (bottom). Svalbard fills up because every polar-orbiting satellite passes over it.</figcaption></figure>

The picture also shows the obvious geometry: Svalbard at 78 degrees north sees almost every polar LEO satellite, so it is the contended resource, while Sao Paulo is comparatively free.

## The agent

So why bring an LLM into a problem a solver already nails? Because the solver only optimizes what you can write as a linear objective. Real scheduling carries soft, fuzzy constraints that are painful to formalize: "prefer the German station for that customer's satellite", "this operator emailed that tomorrow's 06:00 pass matters more than usual", "avoid back-to-back passes on the dish that has been flaky". An LLM agent can take those in plain language alongside the structured pass list. The pattern in the recent literature (LLMSat, the Kerbal Space Program operator work, the multi-agent Earth-observation scheduler) is the same: the model proposes, a checker validates, the model revises.

The agent gets the pass catalog as JSON and one tool, `submit_schedule`. A validator checks the returned schedule against the hard constraints, and any violation is fed back so the model can fix it. I ran this with Gemini 3 Flash, but the loop is the same for any tool-calling model.

```python
def llm_schedule(passes, max_rounds=6):
    client = genai.Client(api_key=api_key())
    catalog = [{"id": i, "sat": p.sat, "station": p.station,
                "start": round(p.start), "end": round(p.end),
                "weight": round(p.weight)} for i, p in enumerate(passes)]
    contents = [types.Content(role="user",
                              parts=[types.Part(text=PROMPT + json.dumps(catalog))])]
    for _ in range(max_rounds):
        resp = client.models.generate_content(model=MODEL, contents=contents, config=config)
        fc = resp.candidates[0].content.parts[0].function_call
        chosen = [int(x) for x in fc.args["pass_ids"]]
        violations = check(passes, chosen)
        if not violations:
            return chosen                          # feasible
        contents.append(resp.candidates[0].content)
        contents.append(types.Content(role="user", parts=[types.Part.from_function_response(
            name="submit_schedule",
            response={"feasible": False, "fix_these_overlaps": violations[:40]})]))
    return chosen
```

The validator is the important half. The LLM does not enforce the constraints; the code does, and the model only ever sees a feasible-or-not verdict plus the specific overlaps it created. This keeps the agent honest: a schedule that double-books Svalbard gets bounced with the exact conflicting pass IDs and tries again.

## What actually happened

Two runs, same harness, told the whole story.

Gemini 3 Flash proposed 86 contacts with 2 overlaps on the first try, saw the two conflicts come back, dropped one pass from each, and returned a feasible schedule on the second round: 84 contacts, weighted 2190. That is **97.5% of the optimum**, and just under greedy's 98.3%. The agent solved the problem, but it did not beat ten lines of greedy, let alone the solver.

A weaker model made the case for the validator even more bluntly. Gemini 2.5 Flash opened by selecting almost every pass in the catalog (153 contacts, 111 overlaps), and across four rounds of being told exactly which passes collided, it only ground down to 87 violations. It never produced a runnable schedule. Its raw objective looked like it "beat" the optimum, but only because an infeasible schedule double-books resources it does not have. Without the validator bouncing every submission, you would have shipped a fantasy.

So on the pure objective the answer is clear: the solver wins, greedy ties it for free, and the LLM lands near but below both, when it lands at all. The agent earns its place on the part the solver cannot read: the soft preferences expressed in words, and a schedule that arrives with a rationale you can audit. Optimality versus explainability and flexibility is the actual trade, and it is the question my thesis circles around.

A practical note from building it: forcing the function call and validating every submission is what makes this usable. Letting the model answer in free text and parsing the result is where these agents fall apart, and the 2.5 Flash run shows how fast an unconstrained model drifts into nonsense. The structure is not decoration, it is what turns a chat model into something you can put in a loop.

## Why this is on the blog

This is the clearest single statement of the lab I want to build: machine learning, autonomy, and space, with the orchestration layer made open and reusable. The goal is for the code to be clean enough that someone running a mock CubeSat can pull it and drop the scheduler into their flight-software loop, with the solver as the safe default and the agent as the experimental layer on top.

## Full code

The scheduling baseline (passes, CP-SAT, greedy, plot) runs as-is. The agent module needs `ANTHROPIC_API_KEY` and the `anthropic` package.

```python
#!/usr/bin/env python
"""Ground-station contact scheduling: optimal solver vs greedy baseline.

Compute real satellite passes over a small ground-station network with skyfield,
then schedule contacts two ways: an exact CP-SAT solver and a greedy heuristic.
A station can run one contact at a time, and a satellite can talk to one station
at a time.
"""
import numpy as np
from collections import defaultdict, namedtuple
from datetime import datetime, timezone
import matplotlib.pyplot as plt
from skyfield.api import load, wgs84, EarthSatellite
from ortools.sat.python import cp_model

rng = np.random.default_rng(11)

# satellites (real TLEs) and ground stations
lines = [l for l in open("res/gs_tles.txt").read().splitlines() if l.strip()]
ts = load.timescale()
sats = [EarthSatellite(lines[i + 1], lines[i + 2], lines[i], ts)
        for i in range(0, len(lines), 3)]
print(f"[sched] {len(sats)} satellites:", ", ".join(s.name for s in sats))

STATIONS = {
    "Sao Paulo": wgs84.latlon(-23.56, -46.63),
    "Svalbard":  wgs84.latlon(78.23, 15.40),
}

EPOCH = datetime(2026, 6, 13, 0, 0, 0, tzinfo=timezone.utc)
t0 = ts.from_datetime(EPOCH)
t1 = ts.utc(2026, 6, 14)
MIN_ELEV = 10.0
SLEW_GAP = 300          # seconds a dish needs to slew/reconfigure between contacts

priority = {s.name: int(rng.integers(1, 6)) for s in sats}

Pass = namedtuple("Pass", "sat station start end dur weight")


def secs(t):
    return (t.utc_datetime() - EPOCH).total_seconds()


passes = []
for sat in sats:
    for sname, topos in STATIONS.items():
        t, ev = sat.find_events(topos, t0, t1, altitude_degrees=MIN_ELEV)
        rise = None
        for ti, e in zip(t, ev):
            if e == 0:
                rise = ti
            elif e == 2 and rise is not None:
                s, en = secs(rise), secs(ti)
                dur = en - s
                if dur >= 120:
                    w = priority[sat.name] * (dur / 60.0)
                    passes.append(Pass(sat.name, sname, s, en, dur, w))
                rise = None
print(f"[sched] {len(passes)} candidate passes over 24 h")

# exact schedule with CP-SAT
model = cp_model.CpModel()
by_station, by_sat, present = defaultdict(list), defaultdict(list), []
for i, p in enumerate(passes):
    s, e = int(p.start), int(p.end)
    pres = model.NewBoolVar(f"p{i}")
    iv_station = model.NewOptionalIntervalVar(s, e - s + SLEW_GAP, e + SLEW_GAP,
                                              pres, f"ivs{i}")
    iv_sat = model.NewOptionalIntervalVar(s, e - s, e, pres, f"ivt{i}")
    by_station[p.station].append(iv_station)
    by_sat[p.sat].append(iv_sat)
    present.append(pres)
for ivs in by_station.values():
    model.AddNoOverlap(ivs)
for ivs in by_sat.values():
    model.AddNoOverlap(ivs)
model.Maximize(sum(int(round(p.weight)) * present[i] for i, p in enumerate(passes)))

solver = cp_model.CpSolver()
status = solver.Solve(model)
opt_pick = [i for i in range(len(passes)) if solver.Value(present[i])]
opt_obj = sum(passes[i].weight for i in opt_pick)
print(f"[sched] CP-SAT status={solver.StatusName(status)}  "
      f"contacts={len(opt_pick)}  weighted={opt_obj:.0f}")

# greedy baseline: take the heaviest pass that still fits
order = sorted(range(len(passes)), key=lambda i: passes[i].weight, reverse=True)
busy_station, busy_sat = defaultdict(list), defaultdict(list)


def fits(busy, key, s, e):
    return all(e <= bs or s >= be for bs, be in busy[key])


greedy_pick = []
for i in order:
    p = passes[i]
    if fits(busy_station, p.station, p.start, p.end + SLEW_GAP) and \
       fits(busy_sat, p.sat, p.start, p.end):
        busy_station[p.station].append((p.start, p.end + SLEW_GAP))
        busy_sat[p.sat].append((p.start, p.end))
        greedy_pick.append(i)
greedy_obj = sum(passes[i].weight for i in greedy_pick)
print(f"[sched] greedy            contacts={len(greedy_pick)}  weighted={greedy_obj:.0f}")
print(f"[sched] greedy reaches {greedy_obj / opt_obj:.1%} of the optimal objective")

# figure: Gantt of both schedules
station_y = {s: k for k, s in enumerate(STATIONS)}
sat_color = {s.name: plt.cm.tab10(k) for k, s in enumerate(sats)}


def gantt(ax, pick, title):
    for i in pick:
        p = passes[i]
        ax.barh(station_y[p.station], (p.end - p.start) / 3600,
                left=p.start / 3600, height=0.6,
                color=sat_color[p.sat], edgecolor="k", linewidth=0.3)
    ax.set_yticks(list(station_y.values()))
    ax.set_yticklabels(list(station_y.keys()))
    ax.set_xlim(0, 24)
    ax.set_xlabel("hours from epoch")
    ax.set_title(title)


fig, ax = plt.subplots(2, 1, figsize=(12, 5.5), sharex=True)
gantt(ax[0], greedy_pick, f"Greedy: {len(greedy_pick)} contacts, weighted {greedy_obj:.0f}")
gantt(ax[1], opt_pick, f"Optimal (CP-SAT): {len(opt_pick)} contacts, weighted {opt_obj:.0f}")
handles = [plt.Rectangle((0, 0), 1, 1, color=sat_color[s.name]) for s in sats]
fig.tight_layout()
fig.legend(handles, [f"{s.name} (pri {priority[s.name]})" for s in sats],
           loc="lower center", ncol=4, fontsize=8, bbox_to_anchor=(0.5, -0.13))
fig.savefig("uploads/2026/06/groundstation-schedule.png", dpi=130, bbox_inches="tight")
print("[sched] saved uploads/2026/06/groundstation-schedule.png")
```

The agent layer on top, propose then validate then revise. This is the version I ran, against the Gemini API:

```python
#!/usr/bin/env python
"""LLM agent that plans the ground-station schedule, via the Gemini API.

Same propose -> validate -> revise loop: the model never enforces the
constraints, the validator does, and feeds violations back. Reuses `passes`
from the scheduling script above.
"""
import json
from collections import defaultdict
from google import genai
from google.genai import types

MODEL = "gemini-3-flash-preview"


def api_key():
    # read the key from wherever you keep it
    import os
    return os.environ["GEMINI_API_KEY"]


SUBMIT = types.FunctionDeclaration(
    name="submit_schedule",
    description="Submit the chosen contacts as a list of pass IDs. No two chosen "
                "passes may overlap on the same station (plus a 300s slew gap) or "
                "on the same satellite.",
    parameters=types.Schema(
        type="OBJECT",
        properties={"pass_ids": types.Schema(
            type="ARRAY", items=types.Schema(type="INTEGER"))},
        required=["pass_ids"]),
)

PROMPT = (
    "You are scheduling ground-station contacts. Maximize total weighted contact "
    "time. Constraints: a station runs one contact at a time with a 300-second "
    "slew gap between contacts; a satellite talks to one station at a time. Call "
    "submit_schedule with the pass IDs you choose. Catalog of candidate passes "
    "(times in seconds from epoch):\n\n"
)


def check(passes, chosen, slew_gap=300):
    """Return a list of constraint violations for the chosen pass IDs."""
    violations, by_station, by_sat = [], defaultdict(list), defaultdict(list)
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


def llm_schedule(passes, max_rounds=6):
    client = genai.Client(api_key=api_key())
    catalog = [{"id": i, "sat": p.sat, "station": p.station,
                "start": round(p.start), "end": round(p.end),
                "weight": round(p.weight)} for i, p in enumerate(passes)]
    config = types.GenerateContentConfig(
        tools=[types.Tool(function_declarations=[SUBMIT])],
        tool_config=types.ToolConfig(function_calling_config=types.FunctionCallingConfig(
            mode="ANY", allowed_function_names=["submit_schedule"])))
    contents = [types.Content(role="user",
                              parts=[types.Part(text=PROMPT + json.dumps(catalog))])]
    chosen = []
    for r in range(max_rounds):
        resp = client.models.generate_content(model=MODEL, contents=contents, config=config)
        fc = resp.candidates[0].content.parts[0].function_call
        chosen = [int(x) for x in fc.args["pass_ids"]]
        violations = check(passes, chosen)
        weight = sum(passes[i].weight for i in chosen)
        print(f"[gemini] round {r}: {len(chosen)} contacts, weighted {weight:.0f}, "
              f"{len(violations)} violations")
        if not violations:
            return chosen
        contents.append(resp.candidates[0].content)
        contents.append(types.Content(role="user", parts=[types.Part.from_function_response(
            name="submit_schedule",
            response={"feasible": False, "fix_these_overlaps": violations[:40]})]))
    return chosen


if __name__ == "__main__":
    from groundstation_schedule_demo import passes, opt_obj, opt_pick
    picked = llm_schedule(passes)
    weight = sum(passes[i].weight for i in picked)
    print(f"\n[gemini] final: {len(picked)} contacts, weighted {weight:.0f}, "
          f"feasible={not check(passes, picked)}")
    print(f"[gemini] optimal (CP-SAT): {len(opt_pick)} contacts, weighted {opt_obj:.0f}")
    print(f"[gemini] agent reaches {weight / opt_obj:.1%} of the optimum")
```
