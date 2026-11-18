#include <stdbool.h>
#include <stdint.h>

#include "unity.h"
#include "app.h"
#include "app_config.h"
#include "fault_monitor.h"
#include "mock_bsp.h"
#include "motor_control.h"
#include "motor_fsm.h"
#include "pi_controller.h"
#include "scheduler.h"

/* A fake board behind the BSP mock: the test owns time, buttons and the
 * measured sample, and the fake records what the application drove. */
static uint32_t now_ms;
static bsp_buttons_t buttons;
static motor_sample_t measured;
static int samples_taken;
static int applies;
static int button_reads;
static drive_cmd_t last_cmd;

static uint32_t fake_millis(int n) { (void)n; return now_ms; }
static motor_sample_t fake_sample(int n) { (void)n; samples_taken++; return measured; }
static void fake_apply(drive_cmd_t cmd, int n) { (void)n; applies++; last_cmd = cmd; }
static bsp_buttons_t fake_buttons(int n) { (void)n; button_reads++; return buttons; }

static void run_until(uint32_t end_ms)
{
    while (now_ms < end_ms) {
        now_ms++;
        app_poll();
    }
}

static void boot(void)
{
    app_init();
    samples_taken = 0;
    applies = 0;
    button_reads = 0;
}

static void press_start_at(uint32_t t)
{
    run_until(t - 1u);
    buttons.start_pressed = true;
    run_until(t);
    buttons.start_pressed = false;
}

static void press_stop_at(uint32_t t)
{
    run_until(t - 1u);
    buttons.stop_pressed = true;
    run_until(t);
    buttons.stop_pressed = false;
}

void setUp(void)
{
    now_ms = 0u;
    buttons = (bsp_buttons_t){ .start_pressed = false, .stop_pressed = false };
    measured = (motor_sample_t){ .speed_rpm = 1000, .current_ma = 0 };
    last_cmd = (drive_cmd_t){ .enable = false, .duty = 0 };
    bsp_millis_Stub(fake_millis);
    bsp_motor_sample_Stub(fake_sample);
    bsp_motor_apply_Stub(fake_apply);
    bsp_read_buttons_Stub(fake_buttons);
}

void tearDown(void) {}

/**
 * @brief The control task runs every 1 ms and the UI task every 10 ms.
 * @relation(SWR-APP-001, scope=function)
 */
void test_task_rates(void)
{
    boot();
    run_until(100u);
    TEST_ASSERT_EQUAL_INT(100, samples_taken);
    TEST_ASSERT_EQUAL_INT(100, applies);
    TEST_ASSERT_EQUAL_INT(10, button_reads);
}

/**
 * @brief Polling without time passing runs nothing.
 * @relation(SWR-APP-001, scope=function)
 */
void test_poll_without_elapsed_time_runs_nothing(void)
{
    boot();
    app_poll();
    app_poll();
    TEST_ASSERT_EQUAL_INT(0, samples_taken);
    TEST_ASSERT_EQUAL_INT(0, button_reads);
}

/**
 * @brief The drive stays off until START.
 * @relation(SWR-APP-001, SWR-CTL-002, scope=function)
 */
void test_drive_off_before_start(void)
{
    boot();
    run_until(50u);
    TEST_ASSERT_EQUAL(MOTOR_STATE_IDLE, app_status().state);
    TEST_ASSERT_FALSE(last_cmd.enable);
}

/**
 * @brief A start-button press starts the motor toward the configured setpoint.
 * @relation(SWR-APP-002, scope=function)
 */
void test_start_edge_runs_toward_configured_setpoint(void)
{
    boot();
    press_start_at(10u);
    TEST_ASSERT_EQUAL(MOTOR_STATE_RUNNING, app_status().state);
    run_until(11u);
    TEST_ASSERT_TRUE(last_cmd.enable);
    TEST_ASSERT_GREATER_THAN_INT16(0, last_cmd.duty);

    run_until(400u);
    TEST_ASSERT_EQUAL_INT32(APP_SETPOINT_RPM, app_status().setpoint_rpm);
}

/**
 * @brief A held button produces one event, not one per UI run.
 * @relation(SWR-APP-002, scope=function)
 */
void test_held_start_triggers_once(void)
{
    boot();
    buttons.start_pressed = true;
    run_until(10u);
    TEST_ASSERT_EQUAL(MOTOR_STATE_RUNNING, app_status().state);
    press_stop_at(20u);
    buttons.start_pressed = true;
    run_until(40u);
    TEST_ASSERT_EQUAL(MOTOR_STATE_IDLE, app_status().state);
}

/**
 * @brief A start button already held at boot does not start the motor.
 * @relation(SWR-APP-002, scope=function)
 */
void test_start_held_at_boot_is_not_an_edge(void)
{
    buttons.start_pressed = true;
    boot();
    run_until(50u);
    TEST_ASSERT_EQUAL(MOTOR_STATE_IDLE, app_status().state);
}

/**
 * @brief A stop-button press stops a running motor.
 * @relation(SWR-APP-002, scope=function)
 */
void test_stop_edge_stops(void)
{
    boot();
    press_start_at(10u);
    press_stop_at(30u);
    TEST_ASSERT_EQUAL(MOTOR_STATE_IDLE, app_status().state);
    run_until(31u);
    TEST_ASSERT_FALSE(last_cmd.enable);
}

/**
 * @brief In FAULT, start is ignored and a stop-button press clears the fault.
 * @relation(SWR-APP-002, SWR-CTL-004, scope=function)
 */
void test_stop_edge_clears_fault(void)
{
    boot();
    press_start_at(10u);
    measured.current_ma = APP_OVERCURRENT_MA + 1;
    run_until(15u);
    measured.current_ma = 0;
    TEST_ASSERT_EQUAL(MOTOR_STATE_FAULT, app_status().state);
    TEST_ASSERT_EQUAL_HEX8(FAULT_OVERCURRENT, app_status().faults);
    TEST_ASSERT_FALSE(last_cmd.enable);

    press_start_at(20u);
    TEST_ASSERT_EQUAL(MOTOR_STATE_FAULT, app_status().state);

    press_stop_at(30u);
    TEST_ASSERT_EQUAL(MOTOR_STATE_IDLE, app_status().state);
    TEST_ASSERT_EQUAL_HEX8(FAULT_NONE, app_status().faults);
}
