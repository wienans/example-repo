#include "unity.h"
#include "fault_monitor.h"
#include "motor_control.h"
#include "motor_fsm.h"
#include "pi_controller.h"

static motor_control_t mc;

/* Kp = 1 permille per rpm and no integral make the commanded duty equal to
 * the tracking error, so expected duties follow directly from the ramp. */
static const motor_control_config_t cfg = {
    .pi = { .kp_q8 = 256, .ki_q8 = 0, .out_min = -1000, .out_max = 1000 },
    .fault = { .overcurrent_ma = 5000, .stall_min_duty = 500, .stall_max_speed_rpm = 50, .stall_ticks = 3 },
    .max_setpoint_rpm = 3000,
    .ramp_rpm_per_tick = 10,
};

void setUp(void)
{
    motor_control_init(&mc, &cfg);
}

void tearDown(void) {}

static drive_cmd_t step(rpm_t speed, milliamp_t current)
{
    const motor_sample_t sample = { .speed_rpm = speed, .current_ma = current };
    return motor_control_step(&mc, &sample);
}

static void assert_drive_off(drive_cmd_t cmd)
{
    TEST_ASSERT_FALSE(cmd.enable);
    TEST_ASSERT_EQUAL_INT16(0, cmd.duty);
}

static void start_at(rpm_t measured)
{
    step(measured, 0);
    motor_control_handle(&mc, MOTOR_EVENT_START);
}

/**
 * @brief A new controller is IDLE, fault-free and does not drive.
 * @relation(SWR-FSM-001, SWR-CTL-002, scope=function, role=Test)
 */
void test_starts_idle_with_drive_off(void)
{
    TEST_ASSERT_EQUAL(MOTOR_STATE_IDLE, motor_control_state(&mc));
    TEST_ASSERT_EQUAL_HEX8(FAULT_NONE, motor_control_faults(&mc));
    motor_control_set_speed(&mc, 1000);
    assert_drive_off(step(0, 0));
}

/**
 * @brief The tracked setpoint moves at most ramp_rpm_per_tick per step.
 * @relation(SWR-CTL-001, scope=function, role=Test)
 */
void test_setpoint_ramps_up_and_down(void)
{
    start_at(100);
    motor_control_set_speed(&mc, 135);

    drive_cmd_t cmd = step(100, 0);
    TEST_ASSERT_EQUAL_INT32(110, motor_control_setpoint(&mc));
    TEST_ASSERT_TRUE(cmd.enable);
    TEST_ASSERT_EQUAL_INT16(10, cmd.duty);
    step(100, 0);
    step(100, 0);
    TEST_ASSERT_EQUAL_INT32(130, motor_control_setpoint(&mc));
    step(100, 0);
    TEST_ASSERT_EQUAL_INT32(135, motor_control_setpoint(&mc));
    step(100, 0);
    TEST_ASSERT_EQUAL_INT32(135, motor_control_setpoint(&mc));

    motor_control_set_speed(&mc, 0);
    step(100, 0);
    TEST_ASSERT_EQUAL_INT32(125, motor_control_setpoint(&mc));
}

/**
 * @brief Requested setpoints beyond +/- max_setpoint_rpm are clamped.
 * @relation(SWR-CTL-001, scope=function, role=Test)
 */
void test_setpoint_is_clamped(void)
{
    start_at(2990);
    motor_control_set_speed(&mc, 5000);
    step(2990, 0);
    step(2990, 0);
    TEST_ASSERT_EQUAL_INT32(3000, motor_control_setpoint(&mc));

    motor_control_handle(&mc, MOTOR_EVENT_STOP);
    start_at(-2990);
    motor_control_set_speed(&mc, -5000);
    step(-2990, 0);
    step(-2990, 0);
    TEST_ASSERT_EQUAL_INT32(-3000, motor_control_setpoint(&mc));
}

/**
 * @brief STOP disables the drive from the next step.
 * @relation(SWR-CTL-002, scope=function, role=Test)
 */
void test_stop_disables_drive(void)
{
    start_at(100);
    motor_control_set_speed(&mc, 500);
    TEST_ASSERT_TRUE(step(100, 0).enable);
    motor_control_handle(&mc, MOTOR_EVENT_STOP);
    TEST_ASSERT_EQUAL(MOTOR_STATE_IDLE, motor_control_state(&mc));
    assert_drive_off(step(100, 0));
}

/**
 * @brief Entering RUNNING resets the PI and starts the ramp at the measured speed.
 * @relation(SWR-CTL-003, scope=function, role=Test)
 */
void test_entering_running_resets_pi_and_ramp(void)
{
    const motor_control_config_t integrating = {
        .pi = { .kp_q8 = 0, .ki_q8 = 256, .out_min = -1000, .out_max = 1000 },
        .fault = cfg.fault,
        .max_setpoint_rpm = 3000,
        .ramp_rpm_per_tick = 10,
    };
    motor_control_init(&mc, &integrating);
    start_at(0);
    motor_control_set_speed(&mc, 1000);
    TEST_ASSERT_EQUAL_INT16(10, step(0, 0).duty);
    TEST_ASSERT_EQUAL_INT16(30, step(0, 0).duty);
    TEST_ASSERT_EQUAL_INT16(60, step(0, 0).duty);

    motor_control_handle(&mc, MOTOR_EVENT_STOP);
    start_at(500);
    TEST_ASSERT_EQUAL_INT16(10, step(500, 0).duty);
    TEST_ASSERT_EQUAL_INT32(510, motor_control_setpoint(&mc));
}

/**
 * @brief The step that detects a fault already returns a disabled command and latches.
 * @relation(SWR-CTL-004, SWR-FLT-001, scope=function, role=Test)
 */
void test_overcurrent_disables_in_same_step_and_latches(void)
{
    start_at(100);
    motor_control_set_speed(&mc, 500);
    TEST_ASSERT_TRUE(step(100, 4000).enable);

    assert_drive_off(step(100, 6000));
    TEST_ASSERT_EQUAL(MOTOR_STATE_FAULT, motor_control_state(&mc));
    TEST_ASSERT_EQUAL_HEX8(FAULT_OVERCURRENT, motor_control_faults(&mc));

    assert_drive_off(step(100, 0));
    TEST_ASSERT_EQUAL_HEX8(FAULT_OVERCURRENT, motor_control_faults(&mc));
}

/**
 * @brief START and STOP do not leave FAULT; CLEAR_FAULT returns to IDLE with no faults.
 * @relation(SWR-CTL-004, SWR-FSM-003, scope=function, role=Test)
 */
void test_only_clear_fault_leaves_fault(void)
{
    start_at(100);
    step(100, 6000);
    motor_control_handle(&mc, MOTOR_EVENT_START);
    motor_control_handle(&mc, MOTOR_EVENT_STOP);
    TEST_ASSERT_EQUAL(MOTOR_STATE_FAULT, motor_control_state(&mc));

    motor_control_handle(&mc, MOTOR_EVENT_CLEAR_FAULT);
    TEST_ASSERT_EQUAL(MOTOR_STATE_IDLE, motor_control_state(&mc));
    TEST_ASSERT_EQUAL_HEX8(FAULT_NONE, motor_control_faults(&mc));

    motor_control_handle(&mc, MOTOR_EVENT_START);
    TEST_ASSERT_TRUE(step(100, 0).enable);
}

/**
 * @brief A locked rotor trips STALL once the applied duty has been high for stall_ticks steps.
 * @relation(SWR-CTL-004, SWR-FLT-002, scope=function, role=Test)
 */
void test_stall_trips_from_applied_duty(void)
{
    start_at(0);
    motor_control_set_speed(&mc, 3000);
    /* Duty after step k is 10*k, so step 50 applies 500; the sample of steps
     * 51, 52 and 53 is taken under duty >= 500, and step 53 trips. */
    for (int k = 1; k <= 52; k++) {
        TEST_ASSERT_TRUE(step(0, 0).enable);
    }
    assert_drive_off(step(0, 0));
    TEST_ASSERT_EQUAL(MOTOR_STATE_FAULT, motor_control_state(&mc));
    TEST_ASSERT_EQUAL_HEX8(FAULT_STALL, motor_control_faults(&mc));
}

/**
 * @brief An externally raised FAULT event also disables the drive.
 * @relation(SWR-CTL-002, SWR-FSM-003, scope=function, role=Test)
 */
void test_fault_event_disables_drive(void)
{
    start_at(100);
    motor_control_set_speed(&mc, 500);
    motor_control_handle(&mc, MOTOR_EVENT_FAULT);
    assert_drive_off(step(100, 0));
}
