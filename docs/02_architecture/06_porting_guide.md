# Port the firmware to a new MCU

Use this guide when you bring up the firmware on an MCU that has no HAL port yet. You add files under `src/hal/port/<mcu>/`. If the board differs from the defaults, you also edit `src/bsp/board_config.h`. You change nothing in `src/app`, `src/domain` or `src/middleware`.

## Before you start

You need the vendor's C toolchain, and its peripheral library or register headers. You also need the board schematic. It gives you the pins for PWM, direction, enable and the two buttons, the encoder timer, and the ADC channel of the current sense.

## Write the port

1. Create `src/hal/port/<mcu>/`.
2. Implement every function that `src/hal/hal_tick.h`, `hal_gpio.h`, `hal_pwm.h`, `hal_encoder.h` and `hal_adc.h` declare. Use `src/hal/port/host/hal_host.c` as the reference for signatures and return values.
3. Return `HAL_INVALID_ARG` from an `*_init` function for a pin, channel or encoder that the MCU does not have. Return `HAL_ERROR` when a peripheral fails to start. `bsp_init` stops at the first status that is not `HAL_OK`, and `main` then keeps the drive disabled forever ([LINK: SWR-BSP-004]).
4. Make `hal_gpio_init` start an output pin low. The enable pin is an output, and a low enable lets the motor coast until the firmware starts.
5. Make `hal_tick_ms` return a free-running millisecond counter that wraps at `UINT32_MAX`, without blocking. The scheduler handles the wrap ([LINK: SWR-SCH-001]).
6. Make `hal_encoder_count` return the raw 16-bit timer count in quadrature mode, counting all four edges. The BSP handles the wrap ([LINK: SWR-BSP-001]).
7. Make `hal_pwm_set_duty` accept 0 to 1000 permille. The BSP passes the magnitude and sets the direction on a separate pin.
8. Make `hal_adc_read` run one blocking conversion and return the right-aligned raw result.
9. Include only the HAL headers, your vendor headers and the C library in the port. `make lint` does not check files under `src/hal/port/`, so a reviewer checks this. The host port also includes `board_config.h` and `app.h` for the simulator. A target port has no need for either.

## Adapt the board and the build

1. If the board differs, edit `src/bsp/board_config.h`. It sets the pins, the PWM channel and frequency, the encoder ID and counts per revolution, and the ADC zero point and scale. The default ADC zero point, 2048, assumes a 12-bit converter.
2. Add a build for the vendor toolchain. Compile `src/app`, `src/domain`, `src/middleware`, `src/bsp` and your port directory. Every file includes headers by name only, so add each of those directories to the include path. The host build in the `Makefile` uses `-std=c99 -Wall -Wextra -Wconversion -Werror`. Use the same flags.
3. Run `make lint`. It fails if a file outside your port includes a vendor header, or uses heap or floating point.

## Check the port

1. Run `make test`. The unit tests do not compile your port, so they must still pass unchanged.
2. Flash the board with the motor disconnected. Probe the PWM pin, and press start. The PWM runs at the frequency in `board_config.h`, 20 kHz by default, and its duty rises as the speed loop sees no speed. After about 150 ms the stall check trips, and the PWM and the enable pin go low. Press stop to clear the fault.
3. Connect the motor, and press start. The motor settles at the setpoint in `src/app/app_config.h`, 1500 rpm by default, within 1 s.
4. Hold the shaft. The drive switches off 100 ms after the duty reaches 30 % with the shaft below 50 rpm. The drive stays off until you press stop.
