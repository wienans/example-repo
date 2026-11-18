/**
 * @file app_config.h
 * @brief Application tuning: setpoint, loop gains, limits and task periods.
 * @ingroup app
 */
#ifndef APP_CONFIG_H
#define APP_CONFIG_H

#include "bsp.h"

/** @brief Speed requested at start-up. */
#define APP_SETPOINT_RPM 1500
/** @brief Largest accepted setpoint magnitude. */
#define APP_MAX_SETPOINT_RPM 2200
/** @brief Setpoint slew limit per control tick (5000 rpm/s). */
#define APP_RAMP_RPM_PER_TICK 5

/** @brief Proportional gain, Q8 permille per rpm (about 0.7). */
#define APP_PI_KP_Q8 180
/** @brief Integral gain per tick, Q8 permille per rpm (about 0.016). */
#define APP_PI_KI_Q8 4
/** @brief Duty limit of the speed loop in permille. */
#define APP_DUTY_LIMIT_PERMILLE 1000

/** @brief Overcurrent trip level. */
#define APP_OVERCURRENT_MA 8000
/** @brief Duty at or above which a slow shaft counts as stalling. */
#define APP_STALL_MIN_DUTY_PERMILLE 300
/** @brief Speed below which a driven shaft counts as stalling. */
#define APP_STALL_MAX_SPEED_RPM 50
/** @brief Consecutive control ticks of stalling that trip the fault (100 ms). */
#define APP_STALL_TICKS 100

/** @brief Control task period; equals the BSP sample period. */
#define APP_CONTROL_PERIOD_MS BSP_SAMPLE_PERIOD_MS
/** @brief Button task period. */
#define APP_UI_PERIOD_MS 10

#endif
