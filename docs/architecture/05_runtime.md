# Runtime behavior

The firmware has one thread of control and no interrupts above the HAL port. `main` polls `app_poll` in a loop. `app_poll` reads the millisecond tick and hands it to the scheduler, which runs each task whose period has elapsed. Behavior depends only on the tick and the sampled inputs, which is what [LINK: SYS-007] asks for.

## The 1 ms control tick

```mermaid
sequenceDiagram
  autonumber
  participant main
  participant app
  participant sched as scheduler
  participant bsp
  participant ctl as motor_control
  participant hal as hal port

  main->>app: app_poll()
  app->>bsp: bsp_millis()
  bsp->>hal: hal_tick_ms()
  app->>sched: sched_run(tasks, now_ms)
  sched->>app: control_task()
  app->>bsp: bsp_motor_sample()
  bsp->>hal: hal_encoder_read_count(), hal_adc_read()
  bsp-->>app: motor_sample_t {speed_rpm, current_ma}
  app->>ctl: motor_control_step(&mc, &sample)
  ctl-->>app: drive_cmd_t {enable, duty}
  app->>bsp: bsp_motor_apply(cmd)
  bsp->>hal: hal_gpio_write(dir), hal_pwm_set_duty(|duty|), hal_gpio_write(enable)
```

Inside `motor_control_step` the order is fixed:

1. Run the fault monitor on the sample and the previous duty. A new fault latches and sends `FAULT` to the state machine.
2. If the state is not `RUNNING`, return `{enable = false, duty = 0}`.
3. Move the ramped setpoint toward the target by at most `ramp_rpm_per_tick`.
4. Run the PI controller on `ramped setpoint - measured speed` and return its output as the duty.

Step 1 comes first, so a fault disables the drive in the same call that detects it ([LINK: SWR-CTL-004]).

## Motor states

```mermaid
stateDiagram-v2
  [*] --> IDLE
  IDLE --> RUNNING: START
  RUNNING --> IDLE: STOP
  IDLE --> FAULT: FAULT
  RUNNING --> FAULT: FAULT
  FAULT --> IDLE: CLEAR_FAULT
```

`motor_fsm_next` is a lookup in a `const` table indexed by state and event. Every cell not drawn above maps a state to itself. The table is the single source of truth for [LINK: SWR-FSM-001], [LINK: SWR-FSM-002] and [LINK: SWR-FSM-003], and `tests/unit/domain/test_motor_fsm.c` checks every cell.

## User interface task

The 10 ms task reads both buttons and keeps the previous level of each. A rising edge of the start button sends `START`. A rising edge of the stop button sends `CLEAR_FAULT` when the state is `FAULT`, and `STOP` otherwise ([LINK: SWR-APP-002]). Sampling every 10 ms also debounces contacts that settle in under 10 ms.

## Timing budget

| Task | Period | Work per run |
| --- | --- | --- |
| control | 1 ms | 2 HAL reads, a fixed number of integer operations, 3 HAL writes |
| ui | 10 ms | 2 GPIO reads, at most 1 event |

Neither task loops over data or allocates memory, so each run takes a bounded number of instructions on every target.
