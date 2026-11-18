/**
 * @file hal_host.c
 * @brief HAL implementation for the host simulation.
 * @ingroup hal
 */
#include <math.h>
#include <stdbool.h>
#include <stdint.h>

#include "board_config.h"
#include "hal_adc.h"
#include "hal_encoder.h"
#include "hal_gpio.h"
#include "hal_pwm.h"
#include "hal_tick.h"
#include "host_plant.h"
#include "host_scenario.h"

/** @brief H-bridge supply voltage. */
#define HOST_SUPPLY_V 24.0
/** @brief Number of simulated GPIO pins. */
#define HOST_GPIO_PINS 8u

/** @brief Simulated time. */
static uint32_t s_now_ms;
/** @brief Latched output level per pin. */
static bool s_gpio_out[HOST_GPIO_PINS];
/** @brief Duty on the motor PWM channel. */
static uint16_t s_duty_permille;
/** @brief Motor model. */
static host_plant_t s_plant;

/**
 * @brief Start the simulated time base at 0 ms.
 */
hal_status_t hal_tick_init(void)
{
    s_now_ms = 0u;
    return HAL_OK;
}

/**
 * @brief Advance simulated time and the plant by 1 ms, then return the new time.
 */
uint32_t hal_tick_ms(void)
{
    host_scenario_before_tick(s_now_ms);
    s_now_ms++;
    s_plant.locked = host_scenario_rotor_locked(s_now_ms);
    bool enabled = s_gpio_out[BOARD_PIN_MOTOR_ENABLE];
    double sign = s_gpio_out[BOARD_PIN_MOTOR_DIR] ? 1.0 : -1.0;
    double voltage = enabled ? sign * HOST_SUPPLY_V * (double)s_duty_permille / 1000.0 : 0.0;
    host_plant_step(&s_plant, voltage, enabled, 0.001);
    return s_now_ms;
}

/**
 * @brief Accept any pin below HOST_GPIO_PINS.
 */
hal_status_t hal_gpio_init(hal_gpio_pin_t pin, hal_gpio_dir_t dir)
{
    (void)dir;
    if (pin >= HOST_GPIO_PINS) {
        return HAL_INVALID_ARG;
    }
    s_gpio_out[pin] = false;
    return HAL_OK;
}

/**
 * @brief Latch an output level for the plant to read.
 */
void hal_gpio_write(hal_gpio_pin_t pin, bool level)
{
    if (pin < HOST_GPIO_PINS) {
        s_gpio_out[pin] = level;
    }
}

/**
 * @brief Return scripted button levels; other pins read back their output.
 */
bool hal_gpio_read(hal_gpio_pin_t pin)
{
    if (pin == BOARD_PIN_BUTTON_START) {
        return host_scenario_start_pressed(s_now_ms) ? BOARD_BUTTON_PRESSED_LEVEL : !BOARD_BUTTON_PRESSED_LEVEL;
    }
    if (pin == BOARD_PIN_BUTTON_STOP) {
        return host_scenario_stop_pressed(s_now_ms) ? BOARD_BUTTON_PRESSED_LEVEL : !BOARD_BUTTON_PRESSED_LEVEL;
    }
    return pin < HOST_GPIO_PINS && s_gpio_out[pin];
}

/**
 * @brief Accept the single motor PWM channel.
 */
hal_status_t hal_pwm_init(hal_pwm_channel_t channel, uint32_t freq_hz)
{
    (void)freq_hz;
    s_duty_permille = 0u;
    return channel == BOARD_PWM_CH_MOTOR ? HAL_OK : HAL_INVALID_ARG;
}

/**
 * @brief Store the duty the plant sees on the next tick.
 */
void hal_pwm_set_duty(hal_pwm_channel_t channel, uint16_t duty_permille)
{
    if (channel == BOARD_PWM_CH_MOTOR) {
        s_duty_permille = duty_permille > 1000u ? 1000u : duty_permille;
    }
}

/**
 * @brief Accept the single motor encoder.
 */
hal_status_t hal_encoder_init(hal_encoder_id_t encoder)
{
    return encoder == BOARD_ENCODER_MOTOR ? HAL_OK : HAL_INVALID_ARG;
}

/**
 * @brief Shaft angle in quadrature counts, modulo 2^16.
 */
uint16_t hal_encoder_count(hal_encoder_id_t encoder)
{
    (void)encoder;
    long long counts = (long long)floor(s_plant.position_rev * (double)BOARD_ENCODER_CPR);
    return (uint16_t)(counts & 0xFFFF);
}

/**
 * @brief Accept the single current-sense channel.
 */
hal_status_t hal_adc_init(hal_adc_channel_t channel)
{
    return channel == BOARD_ADC_CH_MOTOR_CURRENT ? HAL_OK : HAL_INVALID_ARG;
}

/**
 * @brief Plant current encoded as a 12-bit current-sense reading.
 */
uint16_t hal_adc_read(hal_adc_channel_t channel)
{
    (void)channel;
    double counts = (double)BOARD_ADC_ZERO_COUNT +
                    s_plant.current_a * 1000.0 * (double)BOARD_ADC_MA_PER_COUNT_DEN / (double)BOARD_ADC_MA_PER_COUNT_NUM;
    double clamped = fmin(fmax(round(counts), 0.0), 4095.0);
    return (uint16_t)clamped;
}
