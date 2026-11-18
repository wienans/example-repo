/**
 * @file hal_gpio.h
 * @brief Digital input/output interface.
 * @ingroup hal
 */
#ifndef HAL_GPIO_H
#define HAL_GPIO_H

/** @addtogroup hal
 * @{
 */

#include <stdbool.h>
#include <stdint.h>
#include "hal_types.h"

/** @brief Port-defined pin identifier. */
typedef uint8_t hal_gpio_pin_t;

/** @brief Pin direction. */
typedef enum {
    HAL_GPIO_INPUT = 0, /**< Digital input. */
    HAL_GPIO_OUTPUT     /**< Push-pull output, initially low. */
} hal_gpio_dir_t;

/**
 * @brief Configure a pin.
 * @param pin Pin to configure.
 * @param dir Input or output.
 * @return HAL_OK on success, otherwise an error status.
 */
hal_status_t hal_gpio_init(hal_gpio_pin_t pin, hal_gpio_dir_t dir);

/**
 * @brief Drive an output pin.
 * @param pin Output pin.
 * @param level true for high, false for low.
 */
void hal_gpio_write(hal_gpio_pin_t pin, bool level);

/**
 * @brief Read the level of an input pin.
 * @param pin Input pin.
 * @return true when the pin is high.
 */
bool hal_gpio_read(hal_gpio_pin_t pin);

/** @} */
#endif
