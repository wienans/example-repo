#include "unity.h"
#include "board_config.h"
#include "bsp_convert.h"

void setUp(void) {}
void tearDown(void) {}

/**
 * @brief The expected values below assume this board's scaling.
 * @relation(SWR-BSP-001, SWR-BSP-002, scope=function, role=Test)
 */
void test_board_scaling_premise(void)
{
    TEST_ASSERT_EQUAL_INT(16384, BOARD_ENCODER_CPR);
    TEST_ASSERT_EQUAL_INT(2048, BOARD_ADC_ZERO_COUNT);
}

/**
 * @brief Counter difference is signed and survives wraps in both directions.
 * @relation(SWR-BSP-001, scope=function, role=Test)
 */
void test_encoder_delta_is_wrap_safe(void)
{
    TEST_ASSERT_EQUAL_INT32(16, bsp_encoder_delta(100, 116));
    TEST_ASSERT_EQUAL_INT32(-16, bsp_encoder_delta(116, 100));
    TEST_ASSERT_EQUAL_INT32(16, bsp_encoder_delta(65530, 10));
    TEST_ASSERT_EQUAL_INT32(-16, bsp_encoder_delta(10, 65530));
    TEST_ASSERT_EQUAL_INT32(32767, bsp_encoder_delta(0, 32767));
    TEST_ASSERT_EQUAL_INT32(-32768, bsp_encoder_delta(0, 32768));
}

/**
 * @brief A quarter revolution per sample period of 1 ms is 15000 rpm; fractions truncate toward zero.
 * @relation(SWR-BSP-001, scope=function, role=Test)
 */
void test_counts_to_rpm(void)
{
    TEST_ASSERT_EQUAL_INT32(0, bsp_counts_to_rpm(0));
    TEST_ASSERT_EQUAL_INT32(15000, bsp_counts_to_rpm(4096));
    TEST_ASSERT_EQUAL_INT32(-15000, bsp_counts_to_rpm(-4096));
    TEST_ASSERT_EQUAL_INT32(999, bsp_counts_to_rpm(273));
    TEST_ASSERT_EQUAL_INT32(120000, bsp_counts_to_rpm(32768));
    TEST_ASSERT_EQUAL_INT32(-120000, bsp_counts_to_rpm(-32768));
}

/**
 * @brief Mid-scale is 0 mA; each count is 3300 mV / 4096 at 100 mV/A.
 * @relation(SWR-BSP-002, scope=function, role=Test)
 */
void test_adc_to_milliamp(void)
{
    TEST_ASSERT_EQUAL_INT32(0, bsp_adc_to_ma(2048));
    TEST_ASSERT_EQUAL_INT32(4125, bsp_adc_to_ma(2560));
    TEST_ASSERT_EQUAL_INT32(-4125, bsp_adc_to_ma(1536));
    TEST_ASSERT_EQUAL_INT32(16491, bsp_adc_to_ma(4095));
    TEST_ASSERT_EQUAL_INT32(-16500, bsp_adc_to_ma(0));
}
