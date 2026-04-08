---
title: "Pulse: a Tiny Scheduler for Small Flight Software"
date: 2026-04-08 12:00:00 -0300
author: paolo
layout: post
permalink: /2026/04/08/pulse-scheduler/
categories:
  - en-US
tags:
  - comp
  - embedded
  - microcontrollers
  - cubesat
  - c
---

I wrote [Pulse](https://github.com/paoloo/pulse) as a small cooperative scheduler for periodic tasks on resource-constrained microcontrollers. The target use case is simple flight software, especially PocketQube and CubeSat-style systems where the workload is periodic, the task set is small, and predictability matters more than clever concurrency.

It is not a full RTOS. That is intentional.

Pulse sits between a bare-metal superloop and something like FreeRTOS, Zephyr or RTEMS. A superloop is easy to start with, but the timing rules are usually implicit. A full RTOS is powerful, but it adds kernel complexity, context switching, dynamic task behavior and more surface area to test. Pulse tries to keep the useful structure: explicit periods, a task lifecycle, bounded scheduler behavior and static configuration.

The whole thing is a small header-only C library. No heap. No dynamic task creation. No preemption. No application code inside the timer interrupt.

## How it works

Pulse has two phases.

First, a periodic timer interrupt calls:

```c
pulse_tick_isr();
```

That function only does bookkeeping. It increments per-task counters and marks tasks as ready when their period expires. It does not call user code.

Then the main loop calls:

```c
pulse_poll();
```

`pulse_poll()` runs every ready task in main context. Tasks run cooperatively and finish before the next ready task is dispatched. If more than one task is ready at the same time, the lower task index runs first, which means registration order is also priority order.

That split is the most important design decision in Pulse. Interrupts remain bounded and boring. Application code runs in a normal context where timing and worst-case execution time are easier to reason about.

## Task model

A task is just a function with a small state value:

```c
pulse_state_t task_fn(pulse_state_t state);
```

The scheduler stores the returned state and passes it back on the next run. That gives you a tiny state-machine pattern without allocating memory or creating task objects.

Task registration looks like this:

```c
pulse_init(10u); /* 10 ms scheduler tick */

/* initial state, period in ticks, task function */
assert(pulse_add_task(0, 10u, task_housekeeping) == 0);
assert(pulse_add_task(0, 50u, task_telemetry) == 0);
```

With a 10 ms tick, the first task runs every 100 ms and the second runs every 500 ms.

By default, tasks are marked ready when they are added. This is useful in tests and in systems where you want the first run immediately. The behavior can be changed at compile time with `PULSE_CFG_RUN_IMMEDIATELY`.

## A minimal example

Here is a small hosted example. The port macros are normally provided by a board-specific port header, but this shows the shape:

```c
#include <stdint.h>

/* Platform glue. On a real MCU these would map to interrupt control
 * and timer setup for the board.
 */
#define PULSE_PORT_ENTER_CRITICAL()      do { } while (0)
#define PULSE_PORT_EXIT_CRITICAL()       do { } while (0)
#define PULSE_PORT_TIMER_INIT(ms)        do { (void)(ms); } while (0)
#define PULSE_PORT_ENABLE_GLOBAL_IRQ()   do { } while (0)
#define PULSE_PORT_DISABLE_GLOBAL_IRQ()  do { } while (0)
#define PULSE_PORT_IDLE_HOOK()           do { } while (0)

#define PULSE_IMPLEMENTATION
#include "pulse.h"

static pulse_state_t blink_task(pulse_state_t state)
{
    /* Toggle a LED here. The state can hold the current LED value. */
    state = (state == 0) ? 1 : 0;
    return state;
}

int main(void)
{
    pulse_init(1u);                       /* 1 ms tick */
    (void)pulse_add_task(0, 500u, blink_task); /* run every 500 ms */

    for (;;)
    {
        /* In real hardware, this is called by the timer ISR. */
        pulse_tick_isr();

        /* Application tasks run here, not inside the ISR. */
        pulse_poll();
    }
}
```

This example is not trying to be a timer driver. It shows the contract: the interrupt side calls `pulse_tick_isr()`, and the main side calls `pulse_poll()`.

## Manual polling vs pulse_start

There are two integration styles.

Manual polling is explicit:

```c
int main(void)
{
    board_init();

    pulse_init(10u);
    (void)pulse_add_task(0, 1u, task_sensors);
    (void)pulse_add_task(0, 10u, task_radio);

    timer_init_10ms(); /* ISR calls pulse_tick_isr() */
    enable_interrupts();

    for (;;)
    {
        pulse_poll();
        sleep_until_interrupt();
    }
}
```

This is the pattern I prefer for flight-style code because the main loop stays visible.

Pulse also provides:

```c
pulse_start();
```

That initializes the platform timer through the port macro, enables global interrupts, and then runs the internal polling loop. It is convenient, but manual polling makes the integration points more obvious.

## A telemetry pattern

Pulse does not provide queues, semaphores or mailboxes. Since tasks do not run concurrently, most of that machinery is unnecessary for the systems Pulse targets.

For telemetry, I usually prefer a shared snapshot with a sequence counter. Producer tasks update the snapshot. A packaging or transmit task reads a consistent copy.

```c
typedef struct
{
    uint32_t tick;
    int16_t  temp_c;
    uint16_t vbat_mv;
} telemetry_t;

static volatile uint32_t g_seq;
static telemetry_t g_tlm;

static void tlm_write_begin(void)
{
    g_seq++; /* odd means write in progress */
}

static void tlm_write_end(void)
{
    g_seq++; /* even means stable */
}

static uint8_t tlm_read_snapshot(telemetry_t *out)
{
    uint32_t s0;
    uint32_t s1;

    if (out == (telemetry_t *)0)
    {
        return 0u;
    }

    for (;;)
    {
        s0 = g_seq;
        if ((s0 & 1u) != 0u)
        {
            continue;
        }

        *out = g_tlm;
        s1 = g_seq;

        if ((s0 == s1) && ((s1 & 1u) == 0u))
        {
            return 1u;
        }
    }
}
```

The sensor task writes:

```c
static pulse_state_t task_sensor(pulse_state_t state)
{
    (void)state;

    tlm_write_begin();
    g_tlm.temp_c = read_temperature();
    tlm_write_end();

    return 0;
}
```

The radio task reads:

```c
static pulse_state_t task_radio(pulse_state_t state)
{
    telemetry_t snap;

    (void)state;

    if (tlm_read_snapshot(&snap) != 0u)
    {
        radio_send_telemetry(&snap, sizeof(snap));
    }

    return 0;
}
```

This avoids long critical sections and still gives the radio task a consistent frame to downlink. It also works on small 8-bit systems where you do not want a pile of synchronization primitives.

## What Pulse deliberately does not do

Pulse does not do preemptive multitasking. It does not create or destroy tasks at runtime. It does not include built-in IPC. It does not try to be a general-purpose RTOS.

Those are design constraints, not missing features. The intended workload is small, periodic and statically known: housekeeping, sensor reads, state checks, telemetry packaging, watchdog servicing and radio downlink tasks.

If the system needs dynamic workloads, blocking synchronization, high throughput or multiple independent execution contexts, use a real RTOS. If the system needs a predictable periodic backbone that can be audited without much ceremony, Pulse fits better.

## How to use it

The repository is here:

```text
https://github.com/paoloo/pulse
```

The basic integration flow is:

```c
/* 1. Provide the port macros for your target. */
#include "my_board_pulse_port.h"

/* 2. Include the implementation in exactly one C file. */
#define PULSE_IMPLEMENTATION
#include "pulse.h"

/* 3. Initialize, register static tasks, then poll from main. */
pulse_init(10u);
(void)pulse_add_task(0, 1u, task_sensors);
(void)pulse_add_task(0, 5u, task_housekeeping);
(void)pulse_add_task(0, 100u, task_downlink);
```

Then connect the hardware timer ISR:

```c
void TIMER_ISR(void)
{
    pulse_tick_isr();
}
```

And keep the main loop boring:

```c
for (;;)
{
    pulse_poll();
    PULSE_PORT_IDLE_HOOK();
}
```

## How to cite it

If you use Pulse in a project, paper, thesis or mission prototype, cite the Zenodo record:

{% raw %}
```bibtex
@software{Pulse2026,
  author = {Oliveira, J. Paolo C. M.},
  month = {1},
  doi = {10.5281/zenodo.18187657},
  title = {{Pulse: A tiny cooperative real-time scheduler for microcontrollers}},
  url = {https://github.com/paoloo/pulse},
  version = {0.1.0},
  year = {2026}
}
```
{% endraw %}

Pulse is MIT licensed, so it is easy to use and modify. The important part is not the license text, though. The important part is the design discipline: keep timing explicit, keep memory static, keep interrupts short, and make the software boring enough that you can trust it.
