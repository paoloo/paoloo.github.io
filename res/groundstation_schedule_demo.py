#!/usr/bin/env python
"""Ground-station contact scheduling: optimal solver vs greedy baseline.

Compute real satellite passes over a small ground-station network with skyfield,
then schedule contacts two ways: an exact CP-SAT solver and a greedy heuristic.
A station can run one contact at a time, and a satellite can talk to one station
at a time. The LLM-agent variant that plans the same problem lives in the post;
it needs an API key to run, so this script provides the ground truth it competes
against.
"""
import numpy as np
from collections import defaultdict, namedtuple
from datetime import datetime, timezone
import matplotlib.pyplot as plt
from skyfield.api import load, wgs84, EarthSatellite
from ortools.sat.python import cp_model

rng = np.random.default_rng(11)

# ---------------------------------------------------------------------------
# satellites (real TLEs) and ground stations
# ---------------------------------------------------------------------------
lines = [l for l in open("res/gs_tles.txt").read().splitlines() if l.strip()]
ts = load.timescale()
sats = [EarthSatellite(lines[i + 1], lines[i + 2], lines[i], ts)
        for i in range(0, len(lines), 3)]
print(f"[sched] {len(sats)} satellites:", ", ".join(s.name for s in sats))

STATIONS = {
    "Sao Paulo": wgs84.latlon(-23.56, -46.63),
    "Svalbard":  wgs84.latlon(78.23, 15.40),
}

# fixed 24-hour window (fixed epoch so the run is reproducible)
EPOCH = datetime(2026, 6, 13, 0, 0, 0, tzinfo=timezone.utc)
t0 = ts.from_datetime(EPOCH)
t1 = ts.utc(2026, 6, 14)
MIN_ELEV = 10.0
SLEW_GAP = 300          # seconds a dish needs to slew/reconfigure between contacts

# a fixed downlink priority per satellite (1-5)
priority = {s.name: int(rng.integers(1, 6)) for s in sats}

# ---------------------------------------------------------------------------
# find passes
# ---------------------------------------------------------------------------
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
                if dur >= 120:                       # ignore sub-2-minute passes
                    w = priority[sat.name] * (dur / 60.0)
                    passes.append(Pass(sat.name, sname, s, en, dur, w))
                rise = None
print(f"[sched] {len(passes)} candidate passes over 24 h")

# ---------------------------------------------------------------------------
# exact schedule with CP-SAT
# ---------------------------------------------------------------------------
model = cp_model.CpModel()
by_station, by_sat, present = defaultdict(list), defaultdict(list), []
for i, p in enumerate(passes):
    s, e = int(p.start), int(p.end)
    pres = model.NewBoolVar(f"p{i}")
    # the station is occupied for the contact plus a slew gap; the satellite
    # only for the contact itself.
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

# ---------------------------------------------------------------------------
# greedy baseline: take the heaviest pass that still fits
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# figure: Gantt of both schedules
# ---------------------------------------------------------------------------
station_y = {s: k for k, s in enumerate(STATIONS)}
sat_color = {s.name: plt.cm.tab10(k) for k, s in enumerate(sats)}


def gantt(ax, pick, title):
    for i in pick:
        p = passes[i]
        y = station_y[p.station]
        ax.barh(y, (p.end - p.start) / 3600, left=p.start / 3600, height=0.6,
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
