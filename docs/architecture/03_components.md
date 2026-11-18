# Components of the firmware

Each component is one header and one source file with a single job. Arrows point from the caller to the interface it calls. No arrow points upward, and no component above `hal` sees a vendor type.

```mermaid
C4Component
  title Components: target firmware

  Container_Boundary(fw, "Target firmware") {
    Component(main, "main", "src/app/main.c", "Entry point. Calls bsp_init, app_init, then app_poll forever")
    Component(app, "app", "src/app/app.c", "Owns the motor_control_t instance and the task table. Maps buttons to events")
    Component(sched, "scheduler", "src/middleware/scheduler.c", "Runs due tasks in table order from a millisecond tick")
    Component(ctl, "motor_control", "src/domain/motor_control.c", "Pure step function. Sample in, drive command out")
    Component(pi, "pi_controller", "src/domain/pi_controller.c", "Q8 fixed-point PI with anti-windup")
    Component(fsm, "motor_fsm", "src/domain/motor_fsm.c", "IDLE, RUNNING and FAULT transition table")
    Component(flt, "fault_monitor", "src/domain/fault_monitor.c", "Overcurrent and stall detection")
    Component(bsp, "bsp", "src/bsp/bsp.c", "Maps board pins and channels to HAL calls. Converts raw counts to rpm and mA")
    Component(hal, "hal", "src/hal/*.h", "PWM, GPIO, encoder, ADC and tick interfaces. Headers only")
    Component(port, "hal port", "src/hal/port/<mcu>/", "The only code that includes vendor headers")
  }

  System_Ext(vendor, "MCU vendor library", "Register definitions and drivers")

  Rel(main, app, "app_init, app_poll")
  Rel(app, sched, "sched_run")
  Rel(app, ctl, "motor_control_step")
  Rel(app, bsp, "bsp_motor_sample, bsp_motor_apply")
  Rel(ctl, pi, "pi_step")
  Rel(ctl, fsm, "motor_fsm_next")
  Rel(ctl, flt, "fault_monitor_step")
  Rel(bsp, hal, "hal_pwm_set_duty, hal_encoder_read_count")
  Rel(port, hal, "Implements")
  Rel(port, vendor, "Calls")

  UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

## Responsibilities and interfaces

| Component | Owns | Public interface | Verified by |
| --- | --- | --- | --- |
| `app` | The single `motor_control_t`, the task table, the button edge state | `app.h` | `tests/unit/app/test_app.c` |
| `scheduler` | Nothing. The caller owns the task array | `scheduler.h` | `tests/unit/middleware/test_scheduler.c` |
| `motor_control` | State, ramped setpoint, latched faults | `motor_control.h` | `tests/unit/domain/test_motor_control.c` |
| `pi_controller` | The integral term | `pi_controller.h` | `tests/unit/domain/test_pi_controller.c` |
| `motor_fsm` | The transition table. It has no state of its own | `motor_fsm.h` | `tests/unit/domain/test_motor_fsm.c` |
| `fault_monitor` | The stall counter | `fault_monitor.h` | `tests/unit/domain/test_fault_monitor.c` |
| `bsp` | Previous encoder count, board constants | `bsp.h`, `board_config.h` | `tests/unit/bsp/test_bsp.c` with HAL mocks, `tests/unit/bsp/test_bsp_convert.c` |
| `hal` | Nothing. Interfaces only | `hal_*.h` | Each port's own bring-up tests |

The API reference for every interface is in the Doxygen output under `build/doxygen/html`. The design reasons are in the ADRs:

- [ADR-0002 Link-time HAL ports](../adr/0002-link-time-hal-ports.md)
- [ADR-0003 Pure domain core](../adr/0003-pure-domain-core.md)
- [ADR-0004 Fixed-point arithmetic](../adr/0004-fixed-point-arithmetic.md)
- [ADR-0005 Cooperative scheduler](../adr/0005-cooperative-scheduler.md)
