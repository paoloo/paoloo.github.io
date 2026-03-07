---
title: "Detect and Avoid for Small Drones"
date: 2026-03-07 12:00:00 -0300
author: paolo
layout: post
permalink: /2026/03/07/detect-and-avoid-for-small-drones/
categories:
  - en-US
tags:
  - uav
  - avionics
  - robotics
  - simulation
  - python
---

Small UAV autonomy becomes much less romantic when the problem is "do not hit the other aircraft." Route planning, mapping, and onboard AI are interesting, but beyond visual line of sight operations eventually hit the same hard question: what does the drone know about nearby traffic, and how early can it act?

I tested that as a small simulation. It is not a certified detect-and-avoid system. It is a timing model that makes the sensor trade visible.

The script is in:

```text
res/detect_avoid_uav_demo.py
```

I ran it with:

```bash
MPLCONFIGDIR=/tmp/mplconfig \
conda run -n exohunter python res/detect_avoid_uav_demo.py \
  --plot uploads/2026/03/uav-detect-avoid.png \
  --json /tmp/uav-detect-avoid.json
```

## The encounter

The setup has one UAV and one intruder aircraft in a two-dimensional encounter. Each vehicle is a point with position and velocity. At every second I compute distance and closest point of approach:

```python
def cpa(own_xy, own_v, intr_xy, intr_v):
    r = intr_xy - own_xy
    v = intr_v - own_v
    vv = float(np.dot(v, v))
    if vv == 0:
        return 0.0, float(np.linalg.norm(r))
    t = max(0.0, -float(np.dot(r, v)) / vv)
    d = float(np.linalg.norm(r + v * t))
    return t, d
```

I compared three cases:

```text
adsb   cooperative state is available immediately
camera target is detected only below range/FOV limits
fused  cooperative state plus the same avoidance policy
```

The avoidance maneuver is deliberately simple: if the predicted closest approach is inside the risk envelope, rotate the UAV velocity vector by 28 degrees. This is not flight software. It is a controlled way to compare detection timing.

## What happened

The raw geometry predicted a closest approach of about `152 m` if nothing changed. The runs produced:

```json
{
  "adsb": {
    "detected_s": 0.0,
    "avoided_s": 0.0,
    "min_distance_m": 598.7464219208974
  },
  "camera": {
    "detected_s": 20.0,
    "avoided_s": 20.0,
    "min_distance_m": 332.0382006912544
  },
  "fused": {
    "detected_s": 0.0,
    "avoided_s": 0.0,
    "min_distance_m": 598.7464219208974
  }
}
```

<figure class="wp-block-image"><img src="{{ site.baseurl }}/uploads/2026/03/uav-detect-avoid.png" alt="Detect-and-avoid simulation comparing ADS-B, camera, and fused detection timing" /><figcaption>Earlier detection gives the avoidance maneuver more room. The camera case still avoids the intruder, but it acts later and keeps less separation.</figcaption></figure>

The result is not surprising, but it is useful. ADS-B-like cooperative awareness gives the ownship enough time to turn early. The camera-only case sees the intruder later, so the same avoidance rule leaves much less margin.

## The ugly middle

ADS-B gives structured state, but only for cooperative targets. A camera can see non-cooperative traffic, but it gives less direct information and arrives later in this geometry. Radar helps, but costs power, mass, money, and integration time. Acoustic sensing can be attractive for small drones, but wind and local noise make it fragile.

The practical lesson is that detect-and-avoid is not one sensor. It is an uncertainty-management problem. The avionics layer needs to know when the picture is incomplete and when late detection forces conservative behavior.

## What this is not

This is not a BVLOS certification model, not a 3D airspace simulator, and not an aircraft dynamics model. I ignored wind, climb/descent, sensor false positives, tracker uncertainty, pilot intent, and regulatory separation minima.

It is a small geometry test. For teaching and early design, that is enough to show why "just add a camera" is not an answer. The timing of detection matters as much as the detector itself.

