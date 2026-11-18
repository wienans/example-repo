/**
 * @file hal_tick.h
 * @brief Millisecond time base interface.
 * @ingroup hal
 */
#ifndef HAL_TICK_H
#define HAL_TICK_H

#include <stdint.h>
#include "hal_types.h"

/**
 * @brief Start the 1 ms time base.
 * @return HAL_OK on success, otherwise an error status.
 */
hal_status_t hal_tick_init(void);

/**
 * @brief Milliseconds since hal_tick_init().
 * @return Free-running count that wraps modulo 2^32.
 */
uint32_t hal_tick_ms(void);

#endif
