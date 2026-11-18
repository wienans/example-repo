/**
 * @file hal_adc.h
 * @brief Analog input interface.
 * @ingroup hal
 */
#ifndef HAL_ADC_H
#define HAL_ADC_H

/** @addtogroup hal
 * @{
 */

#include <stdint.h>
#include "hal_types.h"

/** @brief Port-defined ADC channel identifier. */
typedef uint8_t hal_adc_channel_t;

/**
 * @brief Configure an ADC channel.
 * @param channel Channel to configure.
 * @return HAL_OK on success, otherwise an error status.
 */
hal_status_t hal_adc_init(hal_adc_channel_t channel);

/**
 * @brief Perform one blocking conversion.
 * @param channel Channel previously passed to hal_adc_init().
 * @return Raw right-aligned conversion result.
 */
uint16_t hal_adc_read(hal_adc_channel_t channel);

/** @} */
#endif
