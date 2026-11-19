/**
 * @file fault_monitor.c
 * @brief Overcurrent and stall detection implementation.
 * @ingroup domain
 */
#include <stdbool.h>

#include "fault_monitor.h"

/**
 * @brief Absolute value widened so INT32_MIN cannot overflow.
 * @param value Signed value.
 * @return |value|.
 */
static int64_t abs64(int32_t value)
{
    return value < 0 ? -(int64_t)value : (int64_t)value;
}

/**
 * @brief Store the thresholds and reset the stall counter.
 * @relation(SWR-FLT-001, SWR-FLT-002, scope=function, role=Implementation)
 */
void fault_monitor_init(fault_monitor_t *fm, const fault_monitor_config_t *cfg)
{
    fm->cfg = *cfg;
    fm->stall_count = 0u;
}

/**
 * @brief Reset the stall counter.
 * @relation(SWR-FLT-002, scope=function, role=Implementation)
 */
void fault_monitor_reset(fault_monitor_t *fm)
{
    fm->stall_count = 0u;
}

/**
 * @brief Detect overcurrent immediately and stall after consecutive steps.
 * @relation(SWR-FLT-001, SWR-FLT-002, scope=function, role=Implementation)
 */
fault_flags_t fault_monitor_step(fault_monitor_t *fm, const motor_sample_t *sample, duty_permille_t applied_duty)
{
    fault_flags_t flags = FAULT_NONE;
    if (abs64(sample->current_ma) > fm->cfg.overcurrent_ma) {
        flags |= FAULT_OVERCURRENT;
    }

    const bool stalling = abs64(applied_duty) >= fm->cfg.stall_min_duty &&
                          abs64(sample->speed_rpm) < fm->cfg.stall_max_speed_rpm;
    if (!stalling) {
        fm->stall_count = 0u;
    } else if (fm->stall_count < fm->cfg.stall_ticks) {
        fm->stall_count++;
    }
    if (fm->stall_count >= fm->cfg.stall_ticks) {
        flags |= FAULT_STALL;
    }
    return flags;
}
