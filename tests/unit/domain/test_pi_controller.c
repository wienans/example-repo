#include <stdint.h>

#include "unity.h"
#include "pi_controller.h"

static pi_controller_t pi;

void setUp(void) {}
void tearDown(void) {}

static void init(int32_t kp_q8, int32_t ki_q8, int32_t out_min, int32_t out_max)
{
    const pi_config_t cfg = { .kp_q8 = kp_q8, .ki_q8 = ki_q8, .out_min = out_min, .out_max = out_max };
    pi_init(&pi, &cfg);
}

/**
 * @brief Proportional-only output is Kp * error.
 * @relation(SWR-PI-001, scope=function, role=Test)
 */
void test_proportional_output_is_gain_times_error(void)
{
    init(512, 0, -1000, 1000);
    TEST_ASSERT_EQUAL_INT32(200, pi_step(&pi, 100));
    TEST_ASSERT_EQUAL_INT32(-200, pi_step(&pi, -100));
}

/**
 * @brief The integral term adds Ki * error every step, including the current one.
 * @relation(SWR-PI-001, scope=function, role=Test)
 */
void test_integral_accumulates_each_step(void)
{
    init(0, 128, -1000, 1000);
    TEST_ASSERT_EQUAL_INT32(5, pi_step(&pi, 10));
    TEST_ASSERT_EQUAL_INT32(10, pi_step(&pi, 10));
    TEST_ASSERT_EQUAL_INT32(15, pi_step(&pi, 10));
}

/**
 * @brief Output is the sum of both terms.
 * @relation(SWR-PI-001, scope=function, role=Test)
 */
void test_output_sums_proportional_and_integral(void)
{
    init(512, 256, -1000, 1000);
    TEST_ASSERT_EQUAL_INT32(30, pi_step(&pi, 10));
    TEST_ASSERT_EQUAL_INT32(40, pi_step(&pi, 10));
}

/**
 * @brief Output never leaves [out_min, out_max].
 * @relation(SWR-PI-001, scope=function, role=Test)
 */
void test_output_is_clamped_to_limits(void)
{
    init(256, 0, -300, 700);
    TEST_ASSERT_EQUAL_INT32(700, pi_step(&pi, 5000));
    TEST_ASSERT_EQUAL_INT32(-300, pi_step(&pi, -5000));
}

/**
 * @brief The integral contribution is bounded by the output limits.
 * @relation(SWR-PI-002, scope=function, role=Test)
 */
void test_integrator_is_clamped_to_output_limits(void)
{
    init(0, 256, -100, 100);
    for (int i = 0; i < 20; i++) {
        TEST_ASSERT_LESS_OR_EQUAL_INT32(100, pi_step(&pi, 50));
    }
    TEST_ASSERT_EQUAL_INT32(90, pi_step(&pi, -10));
}

/**
 * @brief While saturated in the direction of the error, the integrator holds.
 * @relation(SWR-PI-002, scope=function, role=Test)
 */
void test_integrator_holds_while_saturated_with_error(void)
{
    init(256, 256, -100, 100);
    for (int i = 0; i < 5; i++) {
        TEST_ASSERT_EQUAL_INT32(100, pi_step(&pi, 80));
    }
    TEST_ASSERT_EQUAL_INT32(0, pi_step(&pi, 0));
}

/**
 * @brief While saturated low with negative error, the integrator holds.
 * @relation(SWR-PI-002, scope=function, role=Test)
 */
void test_integrator_holds_while_saturated_low(void)
{
    init(256, 256, -100, 100);
    for (int i = 0; i < 5; i++) {
        TEST_ASSERT_EQUAL_INT32(-100, pi_step(&pi, -80));
    }
    TEST_ASSERT_EQUAL_INT32(0, pi_step(&pi, 0));
}

/**
 * @brief An error opposing the saturation still integrates and unwinds.
 * @relation(SWR-PI-002, scope=function, role=Test)
 */
void test_error_against_saturation_integrates(void)
{
    init(0, 256, -100, 100);
    TEST_ASSERT_EQUAL_INT32(60, pi_step(&pi, 60));
    TEST_ASSERT_EQUAL_INT32(100, pi_step(&pi, 60));
    TEST_ASSERT_EQUAL_INT32(70, pi_step(&pi, -30));
}

/**
 * @brief Reset discards the accumulated integral.
 * @relation(SWR-PI-003, scope=function, role=Test)
 */
void test_reset_clears_integrator(void)
{
    init(256, 256, -1000, 1000);
    pi_step(&pi, 100);
    pi_step(&pi, 100);
    pi_reset(&pi);
    TEST_ASSERT_EQUAL_INT32(0, pi_step(&pi, 0));
    TEST_ASSERT_EQUAL_INT32(20, pi_step(&pi, 10));
}

/**
 * @brief Gains of 65535 with |error| of 100000 keep the correct sign and value.
 * @relation(SWR-PI-001, SWR-PI-002, scope=function, role=Test)
 */
void test_extreme_gains_and_error_do_not_overflow(void)
{
    const int32_t limit = INT32_MAX / 256;
    init(65535, 0, -limit, limit);
    TEST_ASSERT_EQUAL_INT32(-limit, pi_step(&pi, -100000));
    TEST_ASSERT_EQUAL_INT32(limit, pi_step(&pi, 100000));

    init(0, 65535, -limit, limit);
    TEST_ASSERT_EQUAL_INT32(limit, pi_step(&pi, 100000));
    TEST_ASSERT_EQUAL_INT32(8388351, pi_step(&pi, -1));
}
