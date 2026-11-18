/**
 * @file bsp_convert.h
 * @brief Pure conversions from raw peripheral values to domain units.
 * @ingroup bsp
 */
#ifndef BSP_CONVERT_H
#define BSP_CONVERT_H

/** @addtogroup bsp
 * @{
 */

#include <stdint.h>

#include "motor_types.h"

/**
 * @brief Signed distance between two readings of a 16-bit free-running counter.
 * @param previous Earlier reading.
 * @param current Later reading.
 * @return current - previous in -32768..32767, correct across a counter wrap.
 */
int32_t bsp_encoder_delta(uint16_t previous, uint16_t current);

/**
 * @brief Shaft speed from the counts seen in one sample period.
 * @param delta_counts Counts in BSP_SAMPLE_PERIOD_MS, |delta| <= 32768.
 * @return delta * 60000 / (BOARD_ENCODER_CPR * BSP_SAMPLE_PERIOD_MS), truncated toward zero.
 */
rpm_t bsp_counts_to_rpm(int32_t delta_counts);

/**
 * @brief Armature current from a raw current-sense reading.
 * @param raw ADC result.
 * @return (raw - BOARD_ADC_ZERO_COUNT) * NUM / DEN mA, truncated toward zero.
 */
milliamp_t bsp_adc_to_ma(uint16_t raw);

/** @} */
#endif
