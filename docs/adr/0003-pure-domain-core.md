# ADR-0003 Pure domain core

- Status: accepted
- Date: 2026-11-18

## Context

The control law, the state machine and the fault rules carry most of the risk. If they call the HAL or the BSP, every test of them needs mocks, and a change to the board touches the control code.

## Decision

The domain layer has no dependencies outside `src/domain/` and the C standard integer headers. Its entry point is one function:

	drive_cmd_t motor_control_step(motor_control_t *mc, const motor_sample_t *sample);

The `app` layer reads a `motor_sample_t` from the BSP, calls `motor_control_step`, and hands the returned `drive_cmd_t` back to the BSP. The domain types `rpm_t`, `milliamp_t` and `duty_permille_t` live in `src/domain/motor_types.h`. The BSP includes that header, so the dependency points from the board toward the domain.

All domain state lives in caller-owned structs. The domain has no `static` mutable variables.

## Consequences

- Domain tests call real code with literal samples and assert on the returned command. They use no mocks.
- The same `motor_control_t` code can drive two motors by holding two instances.
- The BSP converts raw counts to rpm and mA. Board scaling never reaches the domain.
