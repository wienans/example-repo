#include "unity.h"
#include "fault_monitor.h"

static fault_monitor_t fm;

static const fault_monitor_config_t cfg = {
    .overcurrent_ma = 5000,
    .stall_min_duty = 500,
    .stall_max_speed_rpm = 50,
    .stall_ticks = 3,
};

void setUp(void)
{
    fault_monitor_init(&fm, &cfg);
}

void tearDown(void) {}

static fault_flags_t step(rpm_t speed, milliamp_t current, duty_permille_t duty)
{
    const motor_sample_t sample = { .speed_rpm = speed, .current_ma = current };
    return fault_monitor_step(&fm, &sample, duty);
}

/**
 * @brief Current at the limit is fine; above it in either direction trips at once.
 * @relation(SWR-FLT-001, scope=function)
 */
void test_overcurrent_trips_above_limit_in_both_directions(void)
{
    TEST_ASSERT_EQUAL_HEX8(FAULT_NONE, step(1000, 5000, 100));
    TEST_ASSERT_EQUAL_HEX8(FAULT_NONE, step(1000, -5000, 100));
    TEST_ASSERT_EQUAL_HEX8(FAULT_OVERCURRENT, step(1000, 5001, 100));
    TEST_ASSERT_EQUAL_HEX8(FAULT_OVERCURRENT, step(1000, -5001, 100));
}

/**
 * @brief Stall trips on the stall_ticks-th consecutive stalled step.
 * @relation(SWR-FLT-002, scope=function)
 */
void test_stall_trips_after_consecutive_ticks(void)
{
    TEST_ASSERT_EQUAL_HEX8(FAULT_NONE, step(0, 0, 500));
    TEST_ASSERT_EQUAL_HEX8(FAULT_NONE, step(49, 0, 500));
    TEST_ASSERT_EQUAL_HEX8(FAULT_STALL, step(-49, 0, -600));
}

/**
 * @brief One step at or above the speed threshold restarts the count.
 * @relation(SWR-FLT-002, scope=function)
 */
void test_stall_count_resets_when_shaft_turns(void)
{
    step(0, 0, 800);
    step(0, 0, 800);
    TEST_ASSERT_EQUAL_HEX8(FAULT_NONE, step(50, 0, 800));
    TEST_ASSERT_EQUAL_HEX8(FAULT_NONE, step(0, 0, 800));
    TEST_ASSERT_EQUAL_HEX8(FAULT_NONE, step(0, 0, 800));
    TEST_ASSERT_EQUAL_HEX8(FAULT_STALL, step(0, 0, 800));
}

/**
 * @brief One step below the duty threshold restarts the count.
 * @relation(SWR-FLT-002, scope=function)
 */
void test_stall_count_resets_when_duty_drops(void)
{
    step(0, 0, 800);
    step(0, 0, 800);
    TEST_ASSERT_EQUAL_HEX8(FAULT_NONE, step(0, 0, 499));
    TEST_ASSERT_EQUAL_HEX8(FAULT_NONE, step(0, 0, 800));
    TEST_ASSERT_EQUAL_HEX8(FAULT_NONE, step(0, 0, 800));
    TEST_ASSERT_EQUAL_HEX8(FAULT_STALL, step(0, 0, 800));
}

/**
 * @brief Low duty never counts as a stall.
 * @relation(SWR-FLT-002, scope=function)
 */
void test_low_duty_never_stalls(void)
{
    for (int i = 0; i < 100; i++) {
        TEST_ASSERT_EQUAL_HEX8(FAULT_NONE, step(0, 0, 499));
    }
}

/**
 * @brief Reset restarts the stall count.
 * @relation(SWR-FLT-002, scope=function)
 */
void test_reset_restarts_stall_count(void)
{
    step(0, 0, 800);
    step(0, 0, 800);
    fault_monitor_reset(&fm);
    TEST_ASSERT_EQUAL_HEX8(FAULT_NONE, step(0, 0, 800));
    TEST_ASSERT_EQUAL_HEX8(FAULT_NONE, step(0, 0, 800));
    TEST_ASSERT_EQUAL_HEX8(FAULT_STALL, step(0, 0, 800));
}

/**
 * @brief Both faults are reported together.
 * @relation(SWR-FLT-001, SWR-FLT-002, scope=function)
 */
void test_overcurrent_and_stall_report_together(void)
{
    step(0, 0, 800);
    step(0, 0, 800);
    TEST_ASSERT_EQUAL_HEX8(FAULT_OVERCURRENT | FAULT_STALL, step(0, 9000, 800));
}
