/**
 * @file bsp_convert.c
 * @brief Raw-to-domain unit conversions.
 * @ingroup bsp
 */
#include "bsp_convert.h"

#include "board_config.h"
#include "bsp.h"

/** @brief Milliseconds per minute. */
#define MS_PER_MINUTE 60000

/**
 * @brief Wrap-safe signed counter difference.
 * @relation(SWR-BSP-001, scope=function, role=Implementation)
 */
int32_t bsp_encoder_delta(uint16_t previous, uint16_t current)
{
    /* The modulo-2^16 difference is reinterpreted as signed by hand because
     * converting an out-of-range value to int16_t is implementation-defined. */
    const uint16_t forward = (uint16_t)(current - previous);
    return forward <= INT16_MAX ? (int32_t)forward : (int32_t)forward - 65536;
}

/**
 * @brief Counts per sample period to rpm.
 * @relation(SWR-BSP-001, scope=function, role=Implementation)
 */
rpm_t bsp_counts_to_rpm(int32_t delta_counts)
{
    /* 32768 * 60000 < INT32_MAX, so the product cannot overflow. */
    return delta_counts * MS_PER_MINUTE / (BOARD_ENCODER_CPR * BSP_SAMPLE_PERIOD_MS);
}

/**
 * @brief ADC counts to milliamperes.
 * @relation(SWR-BSP-002, scope=function, role=Implementation)
 */
milliamp_t bsp_adc_to_ma(uint16_t raw)
{
    return ((int32_t)raw - BOARD_ADC_ZERO_COUNT) * BOARD_ADC_MA_PER_COUNT_NUM / BOARD_ADC_MA_PER_COUNT_DEN;
}
