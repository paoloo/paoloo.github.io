---
title: "Running a Tiny Vision-Language Model as a Robot Operator"
date: 2026-03-01 12:00:00 -0300
author: paolo
layout: post
permalink: /2026/03/01/running-a-tiny-vision-language-model-as-a-robot-operator/
categories:
  - en-US
tags:
  - robotics
  - machine-learning
  - llm
  - comp
  - python
---

I wanted a small test for the current "robot foundation model" idea without pretending that a language model is a motor controller. The experiment was deliberately narrow: take a scene description, accept a symbolic action proposal, and reject anything outside the robot's safety boundary.

No robot hardware was needed. I used four toy scenes and treated the proposed actions as if they came from a tiny vision-language model.

The script is in:

```text
res/vlm_robot_operator_demo.py
```

I ran it with:

```bash
MPLCONFIGDIR=/tmp/mplconfig \
conda run -n exohunter python res/vlm_robot_operator_demo.py \
  --plot uploads/2026/03/vlm-robot-operator.png \
  --json /tmp/vlm-robot-operator.json
```

## The interface

The robot accepts only five actions:

```python
ACTIONS = {"stop", "move_forward", "turn_left", "turn_right", "inspect"}
```

That is the main design choice. The model can describe the scene and propose an action, but the system does not execute arbitrary text.

The validator is short:

```python
def validate(scene):
    action = scene["proposal"].get("action")
    if action not in ACTIONS:
        return "rejected", f"invalid action: {action}"
    if scene.get("battery", 70) < 15 and action != "stop":
        return "rejected", "battery too low for movement"
    if scene["front_distance_m"] < 0.35 and action == "move_forward":
        return "rejected", "obstacle too close"
    return "accepted", "action inside bounds"
```

This is the part I would not give to a model. It is tied to hardware limits and mission policy.

## What happened

I tested four proposed actions:

```json
{
  "counts": {
    "accepted": 1,
    "rejected": 3
  }
}
```

The accepted case was simple: the workbench was visible on the left, the model proposed `turn_left`, and the safety checks passed.

The rejected cases were more interesting:

```text
obstacle_front -> rejected: obstacle too close
invalid_action -> rejected: invalid action: approach_target
low_battery -> rejected: battery too low for movement
```

<figure class="wp-block-image"><img src="{{ site.baseurl }}/uploads/2026/03/vlm-robot-operator.png" alt="Toy robot scenes with accepted and rejected model action proposals" /><figcaption>Four toy scenes for a bounded robot-action interface. Only one proposed action was accepted; the rest failed on obstacle, vocabulary, or battery constraints.</figcaption></figure>

## Where the model belongs

The model is useful when the scene requires semantic interpretation: the workbench is on the left, the target is near the shelf, the object of interest is not the obstacle. That does not mean it gets to control the robot directly.

The architecture I would keep is:

```text
perception and state estimation
    |
model proposes symbolic action
    |
validator checks action, battery, distance, mode
    |
controller executes accepted action
```

The reason is authority. A model can propose. The robot's safety layer decides whether that proposal is executable.

## What this is not

This is not a real VLM benchmark, not navigation, and not robot control. I did not run a camera model or a policy network. The point was the interface: a model-like proposal entering a strict action gate.

That interface is the same one I want for spacecraft and ground stations. The model can help with context. It does not redefine the valid action set.

