# Components of the firmware

Each component is one header and one source file with a single job. This technical diagram is for a reader who changes the code. It answers "what calls what". Each arrow points from the caller to the callee and names every function that the caller calls. Every name is a real function in `src/`.

```mermaid
flowchart TB
  accTitle: Calls between firmware components
  accDescr: main calls app and bsp. app calls the scheduler, motor_control and bsp. motor_control calls pi_controller, motor_fsm and fault_monitor. bsp calls bsp_convert and the HAL interface functions. The HAL port implements the HAL headers and calls the vendor library. The host HAL port also calls app_status to print telemetry.
  classDef boundary fill:#FFFFFF,stroke:#666666,stroke-width:1px,stroke-dasharray:5 5,color:black
  classDef firmware fill:#90EE90,stroke:#2E7D2E,stroke-width:2px,color:darkgreen
  classDef interface fill:#87CEEB,stroke:#4682B4,stroke-width:2px,color:darkblue
  classDef platform fill:#E6E6FA,stroke:#8A2BE2,stroke-width:2px,color:darkblue
  classDef edgeCall stroke:#2E7D2E,stroke-width:2px,color:black
  classDef edgeImplements stroke:#8A2BE2,stroke-width:2px,color:black
  classDef edgeVendor stroke:#333333,stroke-width:1.5px,color:black

  subgraph fw [Firmware image: target firmware or host simulator]
    subgraph appL [src/app]
      main["⚙️ main<br/>[Component: C99]<br/>Entry point and safe halt"]
      app["⚙️ app<br/>[Component: C99]<br/>Task table, buttons, the motor_control_t"]
    end
    subgraph mwL [src/middleware]
      sched["⚙️ scheduler<br/>[Component: C99]<br/>Runs due tasks in table order"]
    end
    subgraph domL [src/domain]
      ctl["⚙️ motor_control<br/>[Component: C99]<br/>Sample in, drive command out"]
      pi["⚙️ pi_controller<br/>[Component: C99]<br/>Q8 PI with anti-windup"]
      fsm["⚙️ motor_fsm<br/>[Component: C99]<br/>IDLE, RUNNING, FAULT table"]
      flt["⚙️ fault_monitor<br/>[Component: C99]<br/>Overcurrent and stall"]
    end
    subgraph bspL [src/bsp]
      bsp["⚙️ bsp<br/>[Component: C99]<br/>Board pins and channels"]
      conv["⚙️ bsp_convert<br/>[Component: C99]<br/>Counts to rpm, ADC to mA"]
    end
    hal["🔌 hal_tick, hal_gpio, hal_pwm,<br/>hal_encoder, hal_adc<br/>[Interface: C99 headers in src/hal]"]
    port["🔧 HAL port<br/>[Component: C99]<br/>src/hal/port/host, or &lt;mcu&gt; on target"]
  end

  vendor["🔧 Vendor library<br/>[External library]<br/>MCU SDK, or the C library on the host"]

  main e1@-->|"app_init, app_poll"| app
  main e2@-->|"bsp_init, bsp_motor_apply"| bsp
  app e3@-->|"sched_init, sched_run"| sched
  app e4@-->|"motor_control_init, motor_control_set_speed,<br/>motor_control_step, motor_control_handle,<br/>motor_control_state, motor_control_faults,<br/>motor_control_setpoint"| ctl
  app e5@-->|"bsp_millis, bsp_motor_sample,<br/>bsp_motor_apply, bsp_read_buttons"| bsp
  ctl e6@-->|"pi_init, pi_step, pi_reset"| pi
  ctl e7@-->|"motor_fsm_next"| fsm
  ctl e8@-->|"fault_monitor_init, fault_monitor_step,<br/>fault_monitor_reset"| flt
  bsp e9@-->|"bsp_encoder_delta,<br/>bsp_counts_to_rpm, bsp_adc_to_ma"| conv
  bsp e10@-->|"hal_*_init in bsp_init, then<br/>hal_tick_ms, hal_encoder_count, hal_adc_read,<br/>hal_gpio_read, hal_gpio_write, hal_pwm_set_duty"| hal
  hal ~~~ port
  port e11@-.->|"implements"| hal
  port e12@-.->|"calls"| vendor
  port e13@-->|"app_status, host port only"| app

  class fw,appL,mwL,domL,bspL boundary
  class main,app,sched,ctl,pi,fsm,flt,bsp,conv firmware
  class hal interface
  class port,vendor platform
  class e1,e2,e3,e4,e5,e6,e7,e8,e9,e10,e13 edgeCall
  class e11 edgeImplements
  class e12 edgeVendor

  %% Legend: green solid = function call. Purple dashed = implements a HAL header. Gray dashed = depends on code outside this repo.
```

The arrows end at the component inside each layer box, because the point of this view is which component calls which.

Two calls are easy to miss:

- The scheduler calls `control_task` and `ui_task` in `app.c` through the function pointers in its task table. The diagram has no arrow for them, because `scheduler.c` includes no `app` header.
- The host port calls `app_status` from `host_scenario_before_tick` to print one telemetry row every 10 ms. That call runs inside `hal_tick_ms`, so it happens in the middle of `app_poll`. [Runtime](05_runtime.md#how-the-host-port-advances-time) shows the order. A target port has no reason to call `app`, and [Layering](04_layering.md#what-the-check-does-not-cover) explains why no check stops it.

## Responsibilities and interfaces

| Component | Owns | Public interface | Verified by |
| --- | --- | --- | --- |
| `main` | Nothing. It runs `bsp_init`, then `app_init`, then `app_poll` forever. If `bsp_init` fails, it writes a disabled drive command forever | None | Nothing. `project.yml` excludes `src/app/main.c` from the unit tests |
| `app` | The single `app_t`: the `motor_control_t`, the previous button levels, the latest sample and command. Also the task table and the configuration built from `app_config.h` | `app.h`, `app_config.h` | `tests/unit/app/test_app.c` with a `bsp` mock |
| `scheduler` | Nothing. The caller owns the task array | `scheduler.h` | `tests/unit/middleware/test_scheduler.c` |
| `motor_control` | The state, the target and ramped setpoints, the last measured speed and applied duty, the latched faults | `motor_control.h` | `tests/unit/domain/test_motor_control.c` |
| `pi_controller` | The integral term | `pi_controller.h` | `tests/unit/domain/test_pi_controller.c` |
| `motor_fsm` | The `const` transition table. It has no mutable state | `motor_fsm.h` | `tests/unit/domain/test_motor_fsm.c` |
| `fault_monitor` | The stall counter | `fault_monitor.h` | `tests/unit/domain/test_fault_monitor.c` |
| `bsp` | The previous encoder count | `bsp.h`, `board_config.h` | `tests/unit/bsp/test_bsp.c` with HAL mocks |
| `bsp_convert` | Nothing. Pure conversion functions | `bsp_convert.h` | `tests/unit/bsp/test_bsp_convert.c` |
| `hal` | Nothing. Declarations only | `hal_types.h` and the five `hal_*.h` headers | No unit tests. `make sim` runs the host port |
| Host port | Simulated time, latched GPIO outputs, PWM duty, the motor model | `hal_*.h` | No unit tests. `make sim` runs it |

The domain types `rpm_t`, `milliamp_t`, `duty_permille_t`, `motor_sample_t` and `drive_cmd_t` are in `src/domain/motor_types.h`. The `app`, `domain` and `bsp` layers include it. The scheduler does not.

The API reference for every interface is in the Doxygen output under `build/doxygen/html`. The design reasons are in these ADRs:

- [ADR-0002 Link-time HAL ports](../adr/0002-link-time-hal-ports.md)
- [ADR-0003 Pure domain core](../adr/0003-pure-domain-core.md)
- [ADR-0004 Fixed-point arithmetic](../adr/0004-fixed-point-arithmetic.md)
- [ADR-0005 Cooperative scheduler](../adr/0005-cooperative-scheduler.md)
