---
title: "A Small Swarm Scheduler for UAVs and CubeSats"
date: 2026-06-21 12:00:00 -0300
author: paolo
layout: post
permalink: /2026/06/21/a-small-swarm-scheduler-for-uavs-and-cubesats/
categories:
  - en-US
tags:
  - robotics
  - cubesat
  - optimization
  - python
---

Scheduling keeps showing up in my work. A ground station schedules contacts. A CubeSat schedules payload operations. A UAV swarm schedules tasks, battery, communication, and coverage. The domain changes, but the shape stays familiar: many possible actions, limited resources, and a cost for choosing badly.

I built a tiny swarm scheduler to compare a greedy assignment with an exhaustive optimum. The point was not to build a drone planner. It was to keep the resource accounting visible.

The script is in:

```text
res/swarm_scheduler_demo.py
```

I ran it with:

```bash
MPLCONFIGDIR=/tmp/mplconfig \
conda run -n exohunter python res/swarm_scheduler_demo.py \
  --plot uploads/2026/06/swarm-scheduler.png \
  --json /tmp/swarm-scheduler.json
```

## The toy mission

The mission has three UAVs and six inspection targets. Each target has a location, reward, and service time. Each vehicle starts at the same base and has a battery budget in minutes.

Travel time is just distance divided by speed:

```python
def travel(a, b, speed=180.0):
    return float(np.linalg.norm(a - b) / speed)
```

The route cost is travel plus service:

```python
def route_cost(vehicle, route):
    pos = VEHICLES[vehicle]["start"]
    cost = 0.0
    for task in route:
        cost += travel(pos, task["xy"]) + task["service"]
        pos = task["xy"]
    return cost
```

This is small enough that I can solve it by exhaustive assignment. That gives me a reference for the greedy result.

## Greedy versus optimal

The greedy rule takes the task with the best reward per added minute that still fits. The exhaustive solver tries every assignment to `uav-1`, `uav-2`, `uav-3`, or `skip`.

In this particular run, greedy reached the same reward as the optimum, but with a different route distribution:

```json
{
  "greedy": {
    "reward": 100,
    "tasks": 6,
    "routes": {
      "uav-1": ["antenna", "dish", "gate"],
      "uav-2": ["tower"],
      "uav-3": ["solar", "roof"]
    }
  },
  "optimal": {
    "reward": 100,
    "tasks": 6,
    "routes": {
      "uav-1": ["antenna", "roof", "solar"],
      "uav-2": ["tower", "gate"],
      "uav-3": ["dish"]
    }
  },
  "greedy_fraction_of_optimal": 1.0
}
```

<figure class="wp-block-image"><img src="{{ site.baseurl }}/uploads/2026/06/swarm-scheduler.png" alt="Optimal small swarm task assignment over six inspection targets" /><figcaption>The exhaustive optimum assigns all six tasks while keeping every UAV inside its battery budget.</figcaption></figure>

The tie is still useful. It tells me the greedy baseline is not embarrassing on this small case. If I bring an LLM agent or a more complex planner into the loop, it has to justify itself against this kind of simple baseline.

## The CubeSat mapping

The same structure maps cleanly to CubeSat operations:

```text
UAV battery       -> spacecraft energy budget
inspection target -> payload operation
travel time       -> slew, mode change, or downlink time
task reward       -> science priority
base station      -> ground contact window
```

The exact physics changes, but the operational question stays the same: which actions fit inside the available resources?

## Where an agent fits

The solver handles clean constraints. An agent can be useful when the input includes soft instructions:

```text
keep one UAV in reserve
inspect the antenna before the roof
avoid the vehicle with a flaky battery
prefer a payload task before the next ground pass
```

But the validator still owns the hard rules. A plan that exceeds battery or double-books a resource is not a clever plan. It is infeasible.

For me the architecture remains:

```text
greedy baseline
exact solver for small/reference cases
agent for soft preferences
validator for hard constraints
human for authority
```

That is the same pattern I keep finding in ground-station scheduling and spacecraft operations.

