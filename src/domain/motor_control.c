/**
 * @file motor_control.c
 * @brief Speed-control core implementation.
 * @ingroup domain
 */
#include "motor_control.h"

/** @brief Command that leaves the motor coasting. */
static const drive_cmd_t k_drive_off = { .enable = false, .duty = 0 };

/**
 * @brief Limit a value to [lo, hi].
 * @param value Value to limit.
 * @param lo Lower bound.
 * @param hi Upper bound, >= lo.
 * @return The limited value.
 */
static int32_t clamp32(int32_t value, int32_t lo, int32_t hi)
{
    return value < lo ? lo : (value > hi ? hi : value);
}

/**
 * @brief Initialise to IDLE with a zero setpoint and no faults.
 * @relation(SWR-FSM-001, SWR-CTL-002, scope=function)
 */
void motor_control_init(motor_control_t *mc, const motor_control_config_t *cfg)
{
    mc->cfg = *cfg;
    mc->state = MOTOR_FSM_INITIAL_STATE;
    mc->target_rpm = 0;
    mc->ramped_rpm = 0;
    mc->measured_rpm = 0;
    mc->applied_duty = 0;
    mc->faults = FAULT_NONE;
    pi_init(&mc->pi, &cfg->pi);
    fault_monitor_init(&mc->monitor, &cfg->fault);
}

/**
 * @brief Store the target speed clamped to the configured range.
 * @relation(SWR-CTL-001, scope=function)
 */
void motor_control_set_speed(motor_control_t *mc, rpm_t rpm)
{
    mc->target_rpm = clamp32(rpm, -mc->cfg.max_setpoint_rpm, mc->cfg.max_setpoint_rpm);
}

/**
 * @brief Apply an event and run the entry and exit actions of the new state.
 * @relation(SWR-FSM-002, SWR-FSM-003, SWR-CTL-003, scope=function)
 */
void motor_control_handle(motor_control_t *mc, motor_event_t event)
{
    const motor_state_t next = motor_fsm_next(mc->state, event);
    if (next == mc->state) {
        return;
    }
    if (mc->state == MOTOR_STATE_FAULT) {
        mc->faults = FAULT_NONE;
        fault_monitor_reset(&mc->monitor);
    }
    if (next == MOTOR_STATE_RUNNING) {
        pi_reset(&mc->pi);
        mc->ramped_rpm = mc->measured_rpm;
    }
    mc->state = next;
}

/**
 * @brief Check faults, then ramp the setpoint and run the PI while RUNNING.
 * @relation(SWR-CTL-001, SWR-CTL-002, SWR-CTL-004, scope=function)
 */
drive_cmd_t motor_control_step(motor_control_t *mc, const motor_sample_t *sample)
{
    mc->measured_rpm = sample->speed_rpm;

    const fault_flags_t detected = fault_monitor_step(&mc->monitor, sample, mc->applied_duty);
    if (detected != FAULT_NONE) {
        mc->faults |= detected;
        motor_control_handle(mc, MOTOR_EVENT_FAULT);
    }

    if (mc->state != MOTOR_STATE_RUNNING) {
        mc->applied_duty = 0;
        return k_drive_off;
    }

    const rpm_t step = mc->cfg.ramp_rpm_per_tick;
    mc->ramped_rpm = clamp32(mc->target_rpm, mc->ramped_rpm - step, mc->ramped_rpm + step);
    mc->applied_duty = (duty_permille_t)pi_step(&mc->pi, mc->ramped_rpm - sample->speed_rpm);
    return (drive_cmd_t){ .enable = true, .duty = mc->applied_duty };
}

/**
 * @brief Current operating mode.
 * @relation(SWR-FSM-001, scope=function)
 */
motor_state_t motor_control_state(const motor_control_t *mc)
{
    return mc->state;
}

/**
 * @brief Latched faults.
 * @relation(SWR-CTL-004, scope=function)
 */
fault_flags_t motor_control_faults(const motor_control_t *mc)
{
    return mc->faults;
}

/**
 * @brief Ramped setpoint.
 * @relation(SWR-CTL-001, scope=function)
 */
rpm_t motor_control_setpoint(const motor_control_t *mc)
{
    return mc->ramped_rpm;
}
