/**
 * @file hal_encoder.h
 * @brief Quadrature encoder counter interface.
 * @ingroup hal
 */
#ifndef HAL_ENCODER_H
#define HAL_ENCODER_H

#include <stdint.h>
#include "hal_types.h"

/** @brief Port-defined encoder identifier. */
typedef uint8_t hal_encoder_id_t;

/**
 * @brief Start a quadrature counter.
 * @param encoder Encoder to start.
 * @return HAL_OK on success, otherwise an error status.
 */
hal_status_t hal_encoder_init(hal_encoder_id_t encoder);

/**
 * @brief Read the free-running counter.
 * @param encoder Encoder previously passed to hal_encoder_init().
 * @return Count in quadrature edges. It increments forward, decrements in
 *         reverse and wraps modulo 2^16.
 */
uint16_t hal_encoder_count(hal_encoder_id_t encoder);

#endif
