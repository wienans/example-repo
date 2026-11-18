/**
 * @file hal_pwm.h
 * @brief PWM output interface.
 * @ingroup hal
 */
#ifndef HAL_PWM_H
#define HAL_PWM_H

/** @addtogroup hal
 * @{
 */

#include <stdint.h>
#include "hal_types.h"

/** @brief Port-defined PWM channel identifier. */
typedef uint8_t hal_pwm_channel_t;

/**
 * @brief Configure a PWM channel at a fixed frequency with 0 % duty.
 * @param channel Channel to configure.
 * @param freq_hz PWM carrier frequency in Hz.
 * @return HAL_OK on success, otherwise an error status.
 */
hal_status_t hal_pwm_init(hal_pwm_channel_t channel, uint32_t freq_hz);

/**
 * @brief Set the duty cycle of a configured channel.
 * @param channel Channel previously passed to hal_pwm_init().
 * @param duty_permille Duty cycle in 0..1000 (0.1 % steps).
 */
void hal_pwm_set_duty(hal_pwm_channel_t channel, uint16_t duty_permille);

/** @} */
#endif
