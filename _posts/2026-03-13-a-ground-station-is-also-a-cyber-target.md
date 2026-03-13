---
title: "A Ground Station Is Also a Cyber Target"
date: 2026-03-13 12:00:00 -0300
author: paolo
layout: post
permalink: /2026/03/13/a-ground-station-is-also-a-cyber-target/
categories:
  - en-US
tags:
  - cubesat
  - security
  - ground-station
  - space
  - python
---

When people talk about satellite cybersecurity, the spacecraft gets most of the attention. That is understandable. It is the thing in orbit.

But the ground station is usually the easier target.

I tested that idea as a small command-path validator. The point was not to model a full mission operations center. It was to make the boundary explicit: receive-only operations, command proposals, signing, operator authorization, execution zone, and maintenance locks.

The script is in:

```text
res/ground_station_cyber_demo.py
```

I ran it with:

```bash
MPLCONFIGDIR=/tmp/mplconfig \
conda run -n exohunter python res/ground_station_cyber_demo.py \
  --plot uploads/2026/03/ground-station-cyber.png \
  --json /tmp/ground-station-cyber.json
```

## The boundary

A simplified ground segment has at least three zones:

```text
planning       proposes the intended operation
authorization  checks permission and signatures
execution      talks to radios, antennas, and command services
```

An agent can live in planning. It can propose a contact plan or command bundle. It does not get raw uplink access.

The validator checks five proposals:

```text
receive telemetry
payload downlink proposal
unsigned uplink
agent direct raw command
command during maintenance lock
```

## What the validator did

The run produced:

```json
{
  "counts": {
    "accepted": 1,
    "needs_handoff": 1,
    "rejected": 3
  }
}
```

The receive-only telemetry operation was accepted. The payload downlink proposal was valid, but still needed a handoff from planning into the execution zone. Three proposals were rejected:

```text
unsigned-uplink -> commanding proposal is unsigned
agent-direct-command -> raw uplink is not exposed to agents
maintenance-lock -> station locked for maintenance
```

<figure class="wp-block-image"><img src="{{ site.baseurl }}/uploads/2026/03/ground-station-cyber.png" alt="Ground-station command-path validation counts" /><figcaption>A tiny ground-station validator. Most dangerous proposals are rejected before they reach execution.</figcaption></figure>

## Why this matters

A mission can have good flight software and still be vulnerable if the command path on the ground is weak. Operator laptops, station APIs, signing keys, dashboards, scripts, and telemetry databases are part of the mission boundary.

This is also why MCP-style tool interfaces are attractive for agentic operations. The agent does not get shell access to the station. It gets typed tools:

```text
get_next_pass(spacecraft_id)
read_recent_telemetry(spacecraft_id)
propose_contact_plan(plan)
validate_command_bundle(bundle)
```

Those tools can enforce schema, authentication, rate limits, and audit logs. More importantly, they can distinguish propose from execute.

## What this is not

This is not a full threat model and not a real ground-station security architecture. It is a small validation model for one idea: command authority has to be explicit.

The spacecraft is hard to reach. The ground station is not. That is why the ground segment deserves the same security attention as the satellite it talks to.
