# ADR-0005 Cooperative scheduler

- Status: accepted
- Date: 2026-11-18

## Context

The firmware runs two periodic jobs, the 1 ms control loop and the 10 ms button scan. An RTOS would add a vendor or third-party dependency, a port per MCU, stacks per task, and preemption, which the firmware would then have to make safe around shared state.

## Decision

Use a cooperative scheduler in `src/middleware/scheduler.c`. The caller owns a static array of `sched_task_t` entries with a function, a context pointer and a period. `sched_run(tasks, count, now_ms)` runs each due task in array order and records when it ran. The scheduler reads no clock. The caller passes the tick in, so tests drive time directly ([LINK: SWR-SCH-001]).

Elapsed time is `now_ms - last_run_ms` in `uint32_t`. Unsigned subtraction gives the right answer across the wrap at `UINT32_MAX`, which comes after 49.7 days of uptime.

## Consequences

- No task preempts another, so `app` needs no locks around the `motor_control_t` instance.
- A task that overruns delays the next one. Each task must finish well inside 1 ms. The [runtime page](../02_architecture/05_runtime.md) lists the work per task.
- Moving to an RTOS later means replacing `scheduler.c` and `app_poll`. The domain and BSP do not change.
