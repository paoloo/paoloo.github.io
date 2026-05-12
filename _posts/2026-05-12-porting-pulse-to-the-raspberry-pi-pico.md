---
title: "Porting Pulse to the Raspberry Pi Pico"
date: 2026-05-12 12:00:00 -0300
author: paolo
layout: post
permalink: /2026/05/12/porting-pulse-to-the-raspberry-pi-pico/
categories:
  - en-US
tags:
  - c
  - embedded
  - raspberry-pi
  - hardware
  - comp
---

In [Pulse: a Tiny Scheduler for Small Flight Software]({{ site.baseurl }}/2026/04/08/pulse-scheduler/) I described the scheduler model: a timer interrupt marks periodic tasks as ready, then the main context runs them cooperatively. That post used a generic port contract. This one connects the contract to real hardware on a Raspberry Pi Pico.

I wanted more than another LED demo, so I built a reusable RP2040 port, ran three periodic tasks and measured their timing. The test also exposed the failure modes that matter in flight-style embedded software.

## The boundary I had to implement

Pulse keeps hardware details behind these macros:

```c
PULSE_PORT_ENTER_CRITICAL()
PULSE_PORT_EXIT_CRITICAL()
PULSE_PORT_TIMER_INIT(tick_ms)
PULSE_PORT_ENABLE_GLOBAL_IRQ()
PULSE_PORT_DISABLE_GLOBAL_IRQ()
PULSE_PORT_IDLE_HOOK()
```

The scheduler itself owns task periods, elapsed ticks and the ready bitmask. The Pico port owns:

- interrupt-safe critical sections
- a periodic hardware-backed callback
- idle behavior
- board initialization

This separation is useful because scheduler policy can be tested on a laptop while the hardware layer stays small enough to review line by line.

## Project layout

```text
pulse-pico-demo/
├── CMakeLists.txt
├── src/
│   ├── main.c
│   ├── pulse.h
│   └── pulse_port_pico.h
└── pico_sdk_import.cmake
```

Copy `pulse.h` from the Pulse repository into `src/`. The port and application are the only new pieces.

## The Pico port

I put the hardware-specific code in `src/pulse_port_pico.h`:

```c
#ifndef PULSE_PORT_PICO_H
#define PULSE_PORT_PICO_H

#include <stdbool.h>
#include <stdint.h>

#include "pico/stdlib.h"
#include "pico/sync.h"
#include "pico/time.h"

void pulse_tick_isr(void);

static critical_section_t pulse_port_critical_section;
static repeating_timer_t pulse_port_timer;

static void pulse_port_init(void)
{
    critical_section_init(&pulse_port_critical_section);
}

static bool pulse_port_timer_callback(repeating_timer_t *timer)
{
    (void)timer;
    pulse_tick_isr();
    return true;
}

static void pulse_port_timer_init(uint32_t tick_ms)
{
    int64_t interval_ms = -(int64_t)tick_ms;

    (void)add_repeating_timer_ms(
        interval_ms,
        pulse_port_timer_callback,
        NULL,
        &pulse_port_timer
    );
}

#define PULSE_PORT_ENTER_CRITICAL() \
    critical_section_enter_blocking(&pulse_port_critical_section)

#define PULSE_PORT_EXIT_CRITICAL() \
    critical_section_exit(&pulse_port_critical_section)

#define PULSE_PORT_TIMER_INIT(tick_ms) \
    pulse_port_timer_init((tick_ms))

#define PULSE_PORT_ENABLE_GLOBAL_IRQ() \
    restore_interrupts(0u)

#define PULSE_PORT_DISABLE_GLOBAL_IRQ() \
    do { (void)save_and_disable_interrupts(); } while (0)

#define PULSE_PORT_IDLE_HOOK() \
    tight_loop_contents()

#endif
```

A negative interval passed to `add_repeating_timer_ms` requests start-to-start timing. With a positive interval, the next delay is measured after the callback finishes, which accumulates callback execution time as drift.

The callback does exactly one application-visible thing: `pulse_tick_isr()`. It does not toggle an LED, read a sensor or print over USB. Those operations belong in Pulse tasks running from main context.

## A note about critical sections

The ready mask is shared between the timer callback and the main loop. A read-modify-write on that mask must be protected.

I avoided implementing enter/exit as a blind disable/enable pair. If a critical section begins while interrupts are already disabled, an unconditional enable restores the wrong state. The Pico SDK `critical_section_t` gave this small port a reviewed synchronization primitive and also covered multicore locking if I expanded the application.

I initialized it before calling any Pulse function:

```c
pulse_port_init();
pulse_init(1u);
```

## The application

My `src/main.c` contained three periodic tasks:

```c
#include <stdint.h>
#include <stdio.h>

#include "pico/stdlib.h"
#include "pulse_port_pico.h"

#define PULSE_IMPLEMENTATION
#define PULSE_MAX_TASKS (8u)
#include "pulse.h"

static volatile uint32_t g_heartbeat_count;
static volatile uint32_t g_sensor_count;
static volatile uint32_t g_telemetry_count;

static pulse_state_t heartbeat_task(pulse_state_t state)
{
    bool next = (state == 0);

    gpio_put(PICO_DEFAULT_LED_PIN, next);
    g_heartbeat_count++;

    return next ? 1 : 0;
}

static pulse_state_t sensor_task(pulse_state_t state)
{
    (void)state;

    g_sensor_count++;
    return 0;
}

static pulse_state_t telemetry_task(pulse_state_t state)
{
    (void)state;

    g_telemetry_count++;

    printf(
        "heartbeat=%lu sensor=%lu telemetry=%lu\n",
        (unsigned long)g_heartbeat_count,
        (unsigned long)g_sensor_count,
        (unsigned long)g_telemetry_count
    );

    return 0;
}

int main(void)
{
    stdio_init_all();

    gpio_init(PICO_DEFAULT_LED_PIN);
    gpio_set_dir(PICO_DEFAULT_LED_PIN, GPIO_OUT);

    pulse_port_init();
    pulse_init(1u);

    if (pulse_add_task(0, 500u, heartbeat_task) != 0)
    {
        return 1;
    }

    if (pulse_add_task(0, 10u, sensor_task) != 0)
    {
        return 1;
    }

    if (pulse_add_task(0, 1000u, telemetry_task) != 0)
    {
        return 1;
    }

    pulse_start();
    return 0;
}
```

With a 1 ms tick:

| Task | Period | Purpose |
|---|---:|---|
| heartbeat | 500 ticks | Toggle LED every 500 ms |
| sensor | 10 ticks | Simulate a 100 Hz acquisition task |
| telemetry | 1000 ticks | Print counters once per second |

Registration order is task priority when several tasks are ready together. The heartbeat runs before sensor, and sensor runs before telemetry.

## CMake configuration

```cmake
cmake_minimum_required(VERSION 3.13)

include(pico_sdk_import.cmake)

project(pulse_pico_demo C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

pico_sdk_init()

add_executable(pulse_pico_demo
    src/main.c
)

target_include_directories(pulse_pico_demo PRIVATE
    ${CMAKE_CURRENT_LIST_DIR}/src
)

target_link_libraries(pulse_pico_demo
    pico_stdlib
)

pico_enable_stdio_usb(pulse_pico_demo 1)
pico_enable_stdio_uart(pulse_pico_demo 0)
pico_add_extra_outputs(pulse_pico_demo)
```

I built it with:

```bash
mkdir -p build
cd build
cmake -DPICO_BOARD=pico ..
cmake --build . -j
```

I flashed `pulse_pico_demo.uf2` through OpenOCD and the debug probe, although BOOTSEL worked for the same binary.

## What happens on each tick

At 1 kHz, the timer callback performs an `O(N)` scan over registered tasks. It increments counters and sets readiness bits. It does not execute task bodies.

Back in main context, `pulse_poll()` selects the lowest ready bit, clears it and runs that task to completion.

The timing model is therefore:

```text
timer IRQ: bounded scheduler bookkeeping
main loop: task A, then task B, then task C
```

This is cooperative scheduling. A task that takes too long delays every lower-priority ready task.

## How I measured execution

I used a spare GPIO as a scope marker:

```c
#define TIMING_PIN (2u)

static pulse_state_t sensor_task(pulse_state_t state)
{
    (void)state;

    gpio_put(TIMING_PIN, 1);
    g_sensor_count++;
    gpio_put(TIMING_PIN, 0);

    return 0;
}
```

I initialized it in `main`:

```c
gpio_init(TIMING_PIN);
gpio_set_dir(TIMING_PIN, GPIO_OUT);
```

With a logic analyzer connected, pulse width gave me task execution time and the distance between rising edges gave me release timing. This was more useful than adding `printf` inside fast tasks, because printing changed the timing I was trying to measure.

For each task, I recorded:

- minimum, average and maximum execution time
- period jitter
- missed or merged releases
- longest interval with interrupts disabled

## Overruns and release semantics

I tested a task with a 10 ms period that occasionally ran for 14 ms. Pulse did not preempt it and did not queue an unlimited number of missed releases. The ready bit recorded that work was pending, not how many deadlines had been missed.

That behavior is appropriate for many housekeeping tasks: run once with fresh data instead of replaying stale work. It is not appropriate for every control system.

Before assigning a period, I checked:

```text
WCET(task) < period(task)
sum of interfering WCETs < shortest relevant deadline
```

Cooperative scheduling makes the interference visible, but it does not remove it.

## What blocking did to periodic tasks

My first blocking version looked like this:

```c
static pulse_state_t bad_radio_task(pulse_state_t state)
{
    (void)state;
    radio_send_blocking(frame, frame_size);
    sleep_ms(100);
    return 0;
}
```

While it waits, no other Pulse task runs.

I replaced that form with a state machine:

```c
static pulse_state_t radio_task(pulse_state_t state)
{
    switch (state)
    {
        case 0:
            radio_begin(frame, frame_size);
            return 1;

        case 1:
            if (radio_done())
            {
                return 0;
            }
            return 1;

        default:
            return 0;
    }
}
```

Each invocation does bounded work and returns. DMA or a peripheral interrupt moves bytes in the background.

## Low-power idle

The initial port uses `tight_loop_contents()`, which is portable but does not save much power. A flight-oriented port can replace the idle hook with a wait-for-interrupt instruction after checking that no task is ready.

Be careful: sleep entry has a race if an interrupt arrives between checking readiness and sleeping. The correct low-power design depends on the SDK primitive and wake sources, so treat it as part of the port, not a cosmetic macro change.

## Debugging with the official probe

The setup from [pi official debug probe]({{ site.baseurl }}/2026/02/18/pi-official-debug-probe/) works well here:

```bash
openocd -f interface/cmsis-dap.cfg \
        -f target/rp2040.cfg \
        -c "adapter speed 5000"
```

I attached GDB with:

```bash
arm-none-eabi-gdb build/pulse_pico_demo.elf
```

```gdb
target extended-remote localhost:3333
monitor reset init
break heartbeat_task
continue
```

Remember that breakpoints stop the core while hardware time may continue or debugger behavior may affect timer callbacks. A logic analyzer is still the better instrument for timing validation.

The port code ended up small. Most of my time went into making assumptions explicit and checking that interrupt context stayed bounded, shared state was safe and every task returned before it became somebody else's timing problem.
