/**
 * @file app.h
 * @brief Application: wires the control core, the scheduler and the board.
 *
 * @defgroup app Application
 * @brief Task wiring and operator interface. Depends on the domain,
 *        middleware and BSP, never on the HAL or vendor code.
 * @{
 */
#ifndef APP_H
#define APP_H

#include "fault_monitor.h"
#include "motor_fsm.h"
#include "motor_types.h"

/** @brief Snapshot of the application for telemetry. */
typedef struct {
    motor_state_t state;    /**< Operating mode. */
    fault_flags_t faults;   /**< Latched faults. */
    rpm_t setpoint_rpm;     /**< Ramped setpoint being tracked. */
    motor_sample_t sample;  /**< Latest measurement. */
    drive_cmd_t cmd;        /**< Latest drive command. */
} app_status_t;

/**
 * @brief Initialise the control core with the configured setpoint and start the tasks.
 *
 * The board must already be initialised by bsp_init().
 */
void app_init(void);

/**
 * @brief Run every task that is due at the current bsp_millis() time.
 */
void app_poll(void);

/**
 * @brief Current application state.
 * @return Snapshot of state, faults, setpoint, latest sample and command.
 */
app_status_t app_status(void);

/** @} */
#endif
