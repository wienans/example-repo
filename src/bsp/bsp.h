/**
 * @file bsp.h
 * @brief Board API in domain units; the only hardware interface the application sees.
 *
 * @defgroup bsp BSP
 * @brief Maps the motor board onto the HAL and converts raw peripheral values
 *        into domain types.
 * @{
 */
#ifndef BSP_H
#define BSP_H

#include <stdbool.h>
#include <stdint.h>

#include "motor_types.h"

/** @brief Interval in ms at which bsp_motor_sample() must be called. */
#define BSP_SAMPLE_PERIOD_MS 1

/** @brief Debounce-free snapshot of the operator buttons. */
typedef struct {
    bool start_pressed; /**< Start button held. */
    bool stop_pressed;  /**< Stop button held. */
} bsp_buttons_t;

/**
 * @brief Initialise every peripheral and leave the drive disabled.
 * @return false if any HAL initialisation failed; the board must not be used.
 */
bool bsp_init(void);

/**
 * @brief Milliseconds since bsp_init().
 * @return Free-running time that wraps modulo 2^32.
 */
uint32_t bsp_millis(void);

/**
 * @brief Measure the motor; call exactly once per BSP_SAMPLE_PERIOD_MS.
 * @return Speed from the encoder counts since the previous call and the current.
 */
motor_sample_t bsp_motor_sample(void);

/**
 * @brief Drive the power stage.
 * @param cmd Sign of duty selects the direction, |duty| the PWM, enable the bridge.
 */
void bsp_motor_apply(drive_cmd_t cmd);

/**
 * @brief Read the operator buttons.
 * @return Current button levels.
 */
bsp_buttons_t bsp_read_buttons(void);

/** @} */
#endif
