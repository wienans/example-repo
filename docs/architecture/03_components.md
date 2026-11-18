# Components of the firmware

Each component is one header and one source file with a single job. This technical diagram is for a reader who changes the code. It answers "what calls what at run time". Each arrow points from the caller to the callee and names the functions it calls. Every name is a real function in `src/`.

```mermaid
flowchart TB
  accTitle: Run-time calls between firmware components
  accDescr: main calls app and bsp. app calls the scheduler, motor_control and bsp. motor_control calls pi_controller, motor_fsm and fault_monitor. bsp calls bsp_convert and the HAL interface headers. The HAL port implements the HAL headers and calls the MCU vendor library.
  classDef boundary fill:#FFFFFF,stroke:#666666,stroke-width:1px,stroke-dasharray:5 5,color:black
  classDef firmware fill:#90EE90,stroke:#2E7D2E,stroke-width:2px,color:darkgreen
  classDef interface fill:#87CEEB,stroke:#4682B4,stroke-width:2px,color:darkblue
  classDef platform fill:#E6E6FA,stroke:#8A2BE2,stroke-width:2px,color:darkblue
  classDef edgeCall stroke:#2E7D2E,stroke-width:2px,color:black
  classDef edgeImplements stroke:#8A2BE2,stroke-width:2px,color:black
  classDef edgeVendor stroke:#333333,stroke-width:1.5px,color:black

  subgraph fw [Target firmware]
    subgraph appL [src/app]
      main["⚙️ main<br/>[Component: C99]<br/>Entry point and safe halt"]
      app["⚙️ app<br/>[Component: C99]<br/>Owns the task table and the motor_control_t"]
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
    subgraph halL [src/hal]
      hal["🔌 hal_pwm, hal_gpio, hal_encoder,<br/>hal_adc, hal_tick<br/>[Interface: C99 headers]"]
    end
    port["🔧 HAL port<br/>[Component: C99]<br/>src/hal/port/&lt;mcu&gt;"]
  end

  vendor["🔧 MCU vendor library<br/>[External library]"]

  main e1@-->|"app_init, app_poll"| app
  main e2@-->|"bsp_init, bsp_motor_apply"| bsp
  app e3@-->|"sched_init, sched_run"| sched
  app e4@-->|"motor_control_step,<br/>motor_control_handle"| ctl
  app e5@-->|"bsp_motor_sample, bsp_motor_apply,<br/>bsp_read_buttons, bsp_millis"| bsp
  ctl e6@-->|"pi_step, pi_reset"| pi
  ctl e7@-->|"motor_fsm_next"| fsm
  ctl e8@-->|"fault_monitor_step"| flt
  bsp e9@-->|"bsp_encoder_delta, bsp_counts_to_rpm,<br/>bsp_adc_to_ma"| conv
  bsp e10@-->|"hal_pwm_set_duty, hal_gpio_write,<br/>hal_encoder_count, hal_adc_read"| hal
  hal ~~~ port
  port e11@-.->|"implements"| hal
  port e12@-.->|"calls"| vendor

  class fw,appL,mwL,domL,bspL,halL boundary
  class main,app,sched,ctl,pi,fsm,flt,bsp,conv firmware
  class hal interface
  class port,vendor platform
  class e1,e2,e3,e4,e5,e6,e7,e8,e9,e10 edgeCall
  class e11 edgeImplements
  class e12 edgeVendor


  %% Legend: green solid = function call. Purple dashed = implements a HAL header. Gray dashed = depends on code outside this repo.
```

The arrows end at the component inside each layer box because the point of this view is which component calls which. The scheduler calls back into `app` through the function pointers in its task table. That callback is not drawn, because `scheduler.c` includes no `app` header.

## Responsibilities and interfaces

| Component | Owns | Public interface | Verified by |
| --- | --- | --- | --- |
| `app` | The single `motor_control_t`, the task table, the button edge state | `app.h` | `tests/unit/app/test_app.c` |
| `scheduler` | Nothing. The caller owns the task array | `scheduler.h` | `tests/unit/middleware/test_scheduler.c` |
| `motor_control` | State, ramped setpoint, latched faults | `motor_control.h` | `tests/unit/domain/test_motor_control.c` |
| `pi_controller` | The integral term | `pi_controller.h` | `tests/unit/domain/test_pi_controller.c` |
| `motor_fsm` | The transition table. It has no state of its own | `motor_fsm.h` | `tests/unit/domain/test_motor_fsm.c` |
| `fault_monitor` | The stall counter | `fault_monitor.h` | `tests/unit/domain/test_fault_monitor.c` |
| `bsp` | Previous encoder count, board constants | `bsp.h`, `board_config.h` | `tests/unit/bsp/test_bsp.c` with HAL mocks |
| `bsp_convert` | Nothing. Pure conversion functions | `bsp_convert.h` | `tests/unit/bsp/test_bsp_convert.c` |
| `hal` | Nothing. Interfaces only | `hal_*.h` | Each port's own bring-up tests |

The API reference for every interface is in the Doxygen output under `build/doxygen/html`. The design reasons are in these ADRs:

- [ADR-0002 Link-time HAL ports](../adr/0002-link-time-hal-ports.md)
- [ADR-0003 Pure domain core](../adr/0003-pure-domain-core.md)
- [ADR-0004 Fixed-point arithmetic](../adr/0004-fixed-point-arithmetic.md)
- [ADR-0005 Cooperative scheduler](../adr/0005-cooperative-scheduler.md)
