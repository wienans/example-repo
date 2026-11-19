/**
 * @file app.c
 * @brief Application tasks and scheduler wiring.
 * @ingroup app
 */
#include "app.h"

#include "app_config.h"
#include "bsp.h"
#include "motor_control.h"
#include "scheduler.h"

/** @brief Everything the application tasks share. */
typedef struct {
    motor_control_t motor;      /**< Control core. */
    bsp_buttons_t buttons_prev; /**< Button levels seen by the previous UI run. */
    motor_sample_t sample;      /**< Latest measurement. */
    drive_cmd_t cmd;            /**< Latest drive command. */
} app_t;

/** @brief The single application instance. */
static app_t s_app;

/** @brief Control core configuration built from app_config.h. */
static const motor_control_config_t k_motor_config = {
    .pi = {
        .kp_q8 = APP_PI_KP_Q8,
        .ki_q8 = APP_PI_KI_Q8,
        .out_min = -APP_DUTY_LIMIT_PERMILLE,
        .out_max = APP_DUTY_LIMIT_PERMILLE,
    },
    .fault = {
        .overcurrent_ma = APP_OVERCURRENT_MA,
        .stall_min_duty = APP_STALL_MIN_DUTY_PERMILLE,
        .stall_max_speed_rpm = APP_STALL_MAX_SPEED_RPM,
        .stall_ticks = APP_STALL_TICKS,
    },
    .max_setpoint_rpm = APP_MAX_SETPOINT_RPM,
    .ramp_rpm_per_tick = APP_RAMP_RPM_PER_TICK,
};

/**
 * @brief Sample, step and apply.
 * @param ctx The app_t instance.
 * @relation(SWR-APP-001, scope=function, role=Implementation)
 */
static void control_task(void *ctx)
{
    app_t *app = ctx;
    app->sample = bsp_motor_sample();
    app->cmd = motor_control_step(&app->motor, &app->sample);
    bsp_motor_apply(app->cmd);
}

/**
 * @brief START on a start-button edge; STOP, or CLEAR_FAULT in FAULT, on a stop-button edge.
 * @param ctx The app_t instance.
 * @relation(SWR-APP-001, SWR-APP-002, scope=function, role=Implementation)
 */
static void ui_task(void *ctx)
{
    app_t *app = ctx;
    const bsp_buttons_t now = bsp_read_buttons();
    if (now.start_pressed && !app->buttons_prev.start_pressed) {
        motor_control_handle(&app->motor, MOTOR_EVENT_START);
    }
    if (now.stop_pressed && !app->buttons_prev.stop_pressed) {
        const bool faulted = motor_control_state(&app->motor) == MOTOR_STATE_FAULT;
        motor_control_handle(&app->motor, faulted ? MOTOR_EVENT_CLEAR_FAULT : MOTOR_EVENT_STOP);
    }
    app->buttons_prev = now;
}

/** @brief Task table in priority order: control before UI. */
static sched_task_t s_tasks[] = {
    { control_task, &s_app, APP_CONTROL_PERIOD_MS, 0u },
    { ui_task, &s_app, APP_UI_PERIOD_MS, 0u },
};

/** @brief Number of entries in s_tasks. */
#define APP_TASK_COUNT (sizeof s_tasks / sizeof s_tasks[0])

/**
 * @brief Configure the core, seed the button state and start the scheduler.
 * @relation(SWR-APP-001, SWR-APP-002, scope=function, role=Implementation)
 */
void app_init(void)
{
    motor_control_init(&s_app.motor, &k_motor_config);
    motor_control_set_speed(&s_app.motor, APP_SETPOINT_RPM);
    s_app.sample = (motor_sample_t){ .speed_rpm = 0, .current_ma = 0 };
    s_app.cmd = (drive_cmd_t){ .enable = false, .duty = 0 };
    s_app.buttons_prev = bsp_read_buttons();
    sched_init(s_tasks, APP_TASK_COUNT, bsp_millis());
}

/**
 * @brief Run due tasks at the current time.
 * @relation(SWR-APP-001, scope=function, role=Implementation)
 */
void app_poll(void)
{
    sched_run(s_tasks, APP_TASK_COUNT, bsp_millis());
}

/**
 * @brief Snapshot for telemetry.
 * @relation(SWR-APP-001, scope=function, role=Implementation)
 */
app_status_t app_status(void)
{
    return (app_status_t){
        .state = motor_control_state(&s_app.motor),
        .faults = motor_control_faults(&s_app.motor),
        .setpoint_rpm = motor_control_setpoint(&s_app.motor),
        .sample = s_app.sample,
        .cmd = s_app.cmd,
    };
}
