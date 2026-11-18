# Port the firmware to a new MCU

Use this guide when you bring up the firmware on an MCU that has no HAL port yet. You add files under `src/hal/port/<mcu>/` and, if the board differs, edit `src/bsp/board_config.h`. You change nothing in `src/app`, `src/domain` or `src/middleware`.

## Before you start

You need the vendor's C toolchain and its peripheral library or register headers. You also need the board schematic, which tells you the pins for PWM, direction, enable, the two buttons, the encoder timer and the current-sense ADC channel.

## Steps

1. Create `src/hal/port/<mcu>/`.
2. Implement every function declared in `src/hal/hal_pwm.h`, `hal_gpio.h`, `hal_encoder.h`, `hal_adc.h` and `hal_tick.h`. Use `src/hal/port/host/` as the reference for signatures and return values.
3. Return `HAL_ERR_PARAM` from an `*_init` function for a channel or pin the MCU does not have. `bsp_init` turns any non-`HAL_OK` status into a safe halt ([LINK: SWR-BSP-004]).
4. Make `hal_tick_ms` return a free-running millisecond counter that wraps at `UINT32_MAX`. The scheduler handles the wrap ([LINK: SWR-SCH-001]).
5. Make `hal_encoder_count` return the raw 16-bit timer count in quadrature mode. The BSP handles the wrap ([LINK: SWR-BSP-001]).
6. Edit `src/bsp/board_config.h` if the board's pins, channels, encoder resolution or current-sense scaling differ from the defaults.
7. Add a build for the vendor toolchain that compiles `src/app`, `src/domain`, `src/middleware`, `src/bsp` and your port directory. Use `-std=c99`.
8. Run `make lint`. It fails if any file outside your port includes a vendor header.

## Check the port

1. Run `make test`. The unit tests do not use your port, so they must still pass unchanged.
2. Flash the board with the motor disconnected. Probe the PWM pin and press start. You should see the PWM frequency from `board_config.h` and a duty that rises as the speed loop tries to reach the setpoint.
3. Connect the motor and press start. The motor should settle at the setpoint from `src/app/app_config.h`.
4. Hold the shaft. The drive should switch off after the stall time, and the state should stay `FAULT` until you press stop.
