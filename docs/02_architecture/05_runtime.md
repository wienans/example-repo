# Runtime behavior

The firmware has one thread of control, and no interrupt handlers above the HAL port. `main` calls `app_poll` in an endless loop. `app_poll` reads the millisecond tick once and passes it to `sched_run`, which runs each task whose period has elapsed. The outputs depend only on the tick and on the sampled inputs, which is what [LINK: SYS-007] asks for.

## One pass of the main loop

This technical sequence diagram shows the calls in one pass of the main loop, in the order the code makes them. Each colored band is one layer. Every message is a real function in `src/`. Most passes on a fast MCU find no task due and return after `sched_run`.

```mermaid
sequenceDiagram
  accTitle: Calls made during one pass of the main loop
  accDescr: main calls app_poll. app reads the tick through bsp and the HAL port, then calls sched_run. When the control task is due, the scheduler calls control_task, which samples the motor through bsp, calls motor_control_step, and applies the returned drive command through bsp. When the UI task is due, the scheduler calls ui_task, which reads both buttons through bsp and sends a start, stop or clear-fault event to motor_control on a rising edge.
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
  app->>sched: sched_run(s_tasks, APP_TASK_COUNT, now_ms)
  opt control task due, every 1 ms
    sched->>app: control_task(&s_app)
    app->>bsp: bsp_motor_sample()
    bsp->>hal: hal_encoder_count(), hal_adc_read()
    bsp-->>app: motor_sample_t {speed_rpm, current_ma}
    app->>ctl: motor_control_step(&app->motor, &app->sample)
    Note over ctl: fault_monitor_step runs first.<br/>A new fault moves the state to FAULT.
    alt state is RUNNING after the fault check
      ctl-->>app: drive_cmd_t {enable = true, duty = PI output}
    else IDLE or FAULT
      ctl-->>app: drive_cmd_t {enable = false, duty = 0}
    end
    app->>bsp: bsp_motor_apply(app->cmd)
    bsp->>hal: hal_gpio_write(DIR), hal_pwm_set_duty(|duty|), hal_gpio_write(ENABLE)
  end
  opt UI task due, every 10 ms
    sched->>app: ui_task(&s_app)
    app->>bsp: bsp_read_buttons()
    bsp->>hal: hal_gpio_read(START), hal_gpio_read(STOP)
    opt rising edge of the start button
      app->>ctl: motor_control_handle(&app->motor, MOTOR_EVENT_START)
    end
    opt rising edge of the stop button
      app->>ctl: motor_control_state(&app->motor)
      app->>ctl: motor_control_handle(&app->motor, CLEAR_FAULT in FAULT, else STOP)
    end
  end
```

The task table in `app.c` lists `control_task` before `ui_task`, so when both are due in the same pass, the control task runs first.

Inside `motor_control_step` the order is fixed:

1. Store the sampled speed as the measured speed.
2. Run `fault_monitor_step` on the sample and on the duty applied in the previous step. A detected fault is latched, and `motor_control_handle` receives `MOTOR_EVENT_FAULT`.
3. If the state is not `RUNNING`, return `{enable = false, duty = 0}`.
4. Move the ramped setpoint toward the target by at most `ramp_rpm_per_tick`.
5. Run `pi_step` on `ramped setpoint - measured speed`, and return its output as the duty.

Step 2 comes before step 3, so a fault disables the drive in the same call that detects it ([LINK: SWR-CTL-004]). The fault monitor trips on these conditions:

| Fault | Condition | Default in `app_config.h` |
| --- | --- | --- |
| `FAULT_OVERCURRENT` | One sample with \|current\| above `overcurrent_ma` | 8000 mA |
| `FAULT_STALL` | \|duty\| at least `stall_min_duty` and \|speed\| below `stall_max_speed_rpm`, for `stall_ticks` consecutive steps | 300 ‰, 50 rpm, 100 steps |

## Scheduler timing

`sched_init` starts every task's first period at the current tick. A task is due when at least `period_ms` has passed since the start of its current period. When the task runs, the start of its period moves forward by exactly `period_ms`, not to the current tick, so the average rate does not drift when a pass is late.

A pass that is late by several periods runs each task at most once. The task then runs on each following pass until it has caught up. The elapsed time is computed in `uint32_t`, so it stays correct across the wrap of the tick after 49.7 days ([LINK: SWR-SCH-001]).

## Motor states

This technical state diagram shows every transition that `motor_fsm_next` can make, and the actions that `motor_control_handle` runs when the state changes. Each transition label names the event and the code that sends it.

```mermaid
stateDiagram-v2
  accTitle: Motor state machine
  accDescr: The motor starts in IDLE. START from ui_task moves IDLE to RUNNING. STOP from ui_task moves RUNNING to IDLE. A FAULT event from motor_control_step moves IDLE or RUNNING to FAULT. CLEAR_FAULT from ui_task moves FAULT back to IDLE. Entering RUNNING resets the PI controller and starts the ramp at the measured speed. Leaving FAULT clears the latched faults and resets the fault monitor.
  classDef fault fill:#FFB6C1,stroke:#DC143C,stroke-width:2px,color:black

  [*] --> IDLE
  IDLE --> RUNNING: START from ui_task
  RUNNING --> IDLE: STOP from ui_task
  IDLE --> FAULT: FAULT from motor_control_step
  RUNNING --> FAULT: FAULT from motor_control_step
  FAULT --> IDLE: CLEAR_FAULT from ui_task

  note right of RUNNING
    On entry: pi_reset.
    Ramp starts at measured speed.
  end note
  note right of FAULT
    On exit: faults cleared.
    fault_monitor_reset.
  end note

  class FAULT fault
```

`motor_fsm_next` is a lookup in a `const` table indexed by state and event. Every cell that the diagram does not draw maps a state to itself. In those cells `motor_control_handle` returns early and runs no action. The table is the single source of truth for [LINK: SWR-FSM-001], [LINK: SWR-FSM-002] and [LINK: SWR-FSM-003]. `tests/unit/domain/test_motor_fsm.c` checks all 12 cells.

The entry action on `RUNNING` is the bumpless start of [LINK: SWR-CTL-003]. The ramp starts from the current shaft speed. A motor that is still coasting when the operator presses start keeps turning, instead of being driven back toward zero first.

## User interface task

The 10 ms task reads both buttons and keeps the previous level of each. A rising edge of the start button sends `START`. A rising edge of the stop button sends `CLEAR_FAULT` when the state is `FAULT`, and `STOP` otherwise ([LINK: SWR-APP-002]). When both buttons rise in the same run, `START` is sent first.

`app_init` reads the buttons once before the first run. A button held down at power-up therefore produces no edge until it is released and pressed again.

The task debounces by sampling. If a contact settles in under 10 ms, at most one sample falls inside the bounce, so one press produces one rising edge.

## Timing budget

| Work | When | Work per run |
| --- | --- | --- |
| `app_poll` | Every pass of the main loop | 1 HAL read (`hal_tick_ms`), a loop over 2 task entries |
| `control_task` | Every 1 ms | 2 HAL reads, a fixed number of integer operations, 3 HAL writes |
| `ui_task` | Every 10 ms | 2 GPIO reads, at most 2 calls to `motor_control_handle` |

No task loops over data or allocates memory, so each run takes a bounded number of instructions on every target. [ADR-0005](../adr/0005-cooperative-scheduler.md) explains why both tasks share one cooperative scheduler.

## How the host port advances time

In the host simulator there is no real clock. This technical sequence diagram shows what one call to `hal_tick_ms` does in `src/hal/port/host/hal_host.c`. It is for a reader who changes the simulator or reads its telemetry.

```mermaid
sequenceDiagram
  accTitle: One call to hal_tick_ms in the host port
  accDescr: bsp_millis calls hal_tick_ms in the host port. The port first calls host_scenario_before_tick, which calls app_status and prints a CSV row every 10 ms, and exits the program at 2500 ms. The port then adds 1 ms to the simulated time, asks the scenario whether the rotor is locked, steps the motor model by 1 ms with the voltage set by the latched PWM duty and GPIO outputs, and returns the new time.
  box rgb(232,248,232) src/app
    participant app as ⚙️ app
  end
  box rgb(232,248,232) src/bsp
    participant bsp as ⚙️ bsp
  end
  box rgb(240,240,250) src/hal/port/host
    participant hal as 🔧 hal_host
    participant scn as 🔧 host_scenario
    participant plant as 🔧 host_plant
  end

  app->>bsp: bsp_millis()
  bsp->>hal: hal_tick_ms()
  hal->>scn: host_scenario_before_tick(s_now_ms)
  opt s_now_ms is a multiple of 10
    scn->>app: app_status()
    Note over scn: Prints one CSV row to stdout
  end
  opt s_now_ms is 2500 or more
    Note over scn: exit(0) ends the simulation
  end
  hal->>hal: s_now_ms++
  hal->>scn: host_scenario_rotor_locked(s_now_ms)
  hal->>plant: host_plant_step(&s_plant, voltage, enabled, 0.001)
  hal-->>bsp: s_now_ms
```

Each call to `hal_tick_ms` advances the simulated time by exactly 1 ms. `app_poll` calls it once per pass, so in the simulator every pass of the main loop is 1 ms long and runs the control task. The motor model sees the PWM duty and the GPIO levels that the previous control step wrote.

The `app_status` call runs inside `app_poll`, between two control steps, so each CSV row shows the sample and command of the control step that has just finished.
