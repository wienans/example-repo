# Runtime behavior

The firmware has one thread of control and no interrupts above the HAL port. `main` calls `app_poll` in a loop. `app_poll` reads the millisecond tick and passes it to the scheduler, which runs each task whose period has elapsed. The outputs depend only on the tick and the sampled inputs, which is what [LINK: SYS-007] asks for.

## The 1 ms control tick

This technical sequence diagram shows the calls in one control tick, in the order the code makes them. Each colored band is one layer. Every message is a real function in `src/`.

```mermaid
sequenceDiagram
  accTitle: Calls made during one 1 ms control tick
  accDescr: main calls app_poll. app reads the tick through bsp and the HAL port, then calls sched_run. The scheduler calls control_task. control_task samples the motor through bsp, which reads the encoder and the ADC from the HAL port. motor_control_step returns an enabled drive command when the state is RUNNING and a disabled one otherwise. bsp_motor_apply writes the direction pin, the PWM duty and the enable pin.
  autonumber
  box rgb(232,248,232) src/app
    participant main as ⚙️ main
    participant app as ⚙️ app
  end
  box rgb(232,248,232) src/middleware
    participant sched as ⚙️ scheduler
  end
  box rgb(232,248,232) src/domain
    participant ctl as ⚙️ motor_control
  end
  box rgb(232,248,232) src/bsp
    participant bsp as ⚙️ bsp
  end
  box rgb(240,240,250) src/hal/port
    participant hal as 🔧 HAL port
  end

  main->>app: app_poll()
  app->>bsp: bsp_millis()
  bsp->>hal: hal_tick_ms()
  app->>sched: sched_run(tasks, count, now_ms)
  sched->>app: control_task(ctx)
  app->>bsp: bsp_motor_sample()
  bsp->>hal: hal_encoder_count(), hal_adc_read()
  bsp-->>app: motor_sample_t {speed_rpm, current_ma}
  app->>ctl: motor_control_step(&mc, &sample)
  Note over ctl: fault_monitor_step runs first.<br/>A new fault moves the state to FAULT.
  alt state is RUNNING
    ctl-->>app: drive_cmd_t {enable = true, duty = PI output}
  else IDLE or FAULT
    ctl-->>app: drive_cmd_t {enable = false, duty = 0}
  end
  app->>bsp: bsp_motor_apply(cmd)
  bsp->>hal: hal_gpio_write(DIR), hal_pwm_set_duty(|duty|), hal_gpio_write(ENABLE)
```

Inside `motor_control_step` the order is fixed:

1. Run the fault monitor on the sample and on the duty applied in the previous tick. A new fault latches and sends `FAULT` to the state machine.
2. If the state is not `RUNNING`, return `{enable = false, duty = 0}`.
3. Move the ramped setpoint toward the target by at most `ramp_rpm_per_tick`.
4. Run the PI controller on `ramped setpoint - measured speed` and return its output as the duty.

Step 1 comes first, so a fault disables the drive in the same call that detects it ([LINK: SWR-CTL-004]).

## Motor states

This technical state diagram shows every transition that `motor_fsm_next` can make. Each label names the event and the code that sends it.

```mermaid
stateDiagram-v2
  accTitle: Motor state machine
  accDescr: The motor starts in IDLE. START from the start button moves IDLE to RUNNING. STOP from the stop button moves RUNNING to IDLE. A FAULT event from the fault monitor moves IDLE or RUNNING to FAULT. CLEAR_FAULT from the stop button moves FAULT back to IDLE.
  classDef fault fill:#FFB6C1,stroke:#DC143C,stroke-width:2px,color:black

  [*] --> IDLE
  IDLE --> RUNNING: START, start button
  RUNNING --> IDLE: STOP, stop button
  IDLE --> FAULT: FAULT, fault monitor
  RUNNING --> FAULT: FAULT, fault monitor
  FAULT --> IDLE: CLEAR_FAULT, stop button

  class FAULT fault
```

`motor_fsm_next` is a lookup in a `const` table indexed by state and event. Every cell not drawn above maps a state to itself. The table is the single source of truth for [LINK: SWR-FSM-001], [LINK: SWR-FSM-002] and [LINK: SWR-FSM-003], and `tests/unit/domain/test_motor_fsm.c` checks all 12 cells.

## User interface task

The 10 ms task reads both buttons and keeps the previous level of each. A rising edge of the start button sends `START`. A rising edge of the stop button sends `CLEAR_FAULT` when the state is `FAULT`, and `STOP` otherwise ([LINK: SWR-APP-002]). Contacts that settle in under 10 ms cannot produce two edges, because the task samples them only once every 10 ms.

## Timing budget

| Task | Period | Work per run |
| --- | --- | --- |
| control | 1 ms | 2 HAL reads, a fixed number of integer operations, 3 HAL writes |
| ui | 10 ms | 2 GPIO reads, at most 1 event |

Neither task loops over data or allocates memory, so each run takes a bounded number of instructions on every target.
