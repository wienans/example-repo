/**
 * @file motor_control.h
 * @brief Speed-control core: state machine, setpoint ramp, PI loop and protection.
 * @ingroup domain
 */
#ifndef MOTOR_CONTROL_H
#define MOTOR_CONTROL_H

/** @addtogroup domain
 * @{
 */

#include "fault_monitor.h"
#include "motor_fsm.h"
#include "motor_types.h"
#include "pi_controller.h"

/** @brief Static configuration of the control core. */
typedef struct {
    pi_config_t pi;               /**< Speed loop; output limits in permille. */
    fault_monitor_config_t fault; /**< Protection thresholds. */
    rpm_t max_setpoint_rpm;       /**< Setpoints are clamped to +/- this. */
    rpm_t ramp_rpm_per_tick;      /**< Largest setpoint change per step; > 0. */
} motor_control_config_t;

/** @brief Control core instance; owned by the caller. */
typedef struct {
    motor_control_config_t cfg; /**< Copy of the configuration. */
    motor_state_t state;        /**< Current operating mode. */
    rpm_t target_rpm;           /**< Requested setpoint after clamping. */
    rpm_t ramped_rpm;           /**< Setpoint the loop currently tracks. */
    rpm_t measured_rpm;         /**< Speed of the latest sample. */
    duty_permille_t applied_duty; /**< Duty of the latest command. */
    fault_flags_t faults;       /**< Latched faults; cleared only by CLEAR_FAULT. */
    pi_controller_t pi;         /**< Speed loop. */
    fault_monitor_t monitor;    /**< Protection. */
} motor_control_t;

/**
 * @brief Initialise to IDLE with a zero setpoint and no faults.
 * @param mc Instance.
 * @param cfg Configuration; copied.
 */
void motor_control_init(motor_control_t *mc, const motor_control_config_t *cfg);

/**
 * @brief Request a new speed.
 * @param mc Instance.
 * @param rpm Target speed; clamped to +/- max_setpoint_rpm.
 */
void motor_control_set_speed(motor_control_t *mc, rpm_t rpm);

/**
 * @brief Apply an operator or system event.
 *
 * Entering RUNNING resets the PI and starts the ramp at the last measured
 * speed. Leaving FAULT clears the latched faults and the monitor.
 *
 * @param mc Instance.
 * @param event Event to apply.
 */
void motor_control_handle(motor_control_t *mc, motor_event_t event);

/**
 * @brief Run one control step.
 * @param mc Instance.
 * @param sample Measurement taken under the previous command.
 * @return Drive command; disabled with zero duty unless RUNNING after
 *         this step's fault check.
 */
drive_cmd_t motor_control_step(motor_control_t *mc, const motor_sample_t *sample);

/**
 * @brief Current operating mode.
 * @param mc Instance.
 * @return State.
 */
motor_state_t motor_control_state(const motor_control_t *mc);

/**
 * @brief Latched faults.
 * @param mc Instance.
 * @return Fault bitmask; FAULT_NONE outside FAULT.
 */
fault_flags_t motor_control_faults(const motor_control_t *mc);

/**
 * @brief Setpoint the loop currently tracks, after ramping.
 * @param mc Instance.
 * @return Ramped setpoint.
 */
rpm_t motor_control_setpoint(const motor_control_t *mc);

/** @} */
#endif
