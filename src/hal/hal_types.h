/**
 * @file hal_types.h
 * @brief Types shared by every HAL interface.
 *
 * @defgroup hal HAL
 * @brief MCU-agnostic peripheral interfaces. A port under src/hal/port/
 *        implements them for one target; nothing above the BSP calls them.
 * @{
 */
#ifndef HAL_TYPES_H
#define HAL_TYPES_H

/** @brief Result of a HAL operation that can fail. */
typedef enum {
    HAL_OK = 0,      /**< Operation succeeded. */
    HAL_ERROR,       /**< Peripheral failed or is unavailable. */
    HAL_INVALID_ARG  /**< Channel, pin or parameter not supported by the port. */
} hal_status_t;

/** @} */
#endif
