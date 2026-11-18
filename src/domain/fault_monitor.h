/**
 * @file fault_monitor.h
 * @brief Overcurrent and stall detection.
 * @ingroup domain
 */
#ifndef FAULT_MONITOR_H
#define FAULT_MONITOR_H

#include <stdint.h>

#include "motor_types.h"

/** @brief Bitmask of detected faults. */
typedef uint8_t fault_flags_t;

/** @brief No fault. */
#define FAULT_NONE ((fault_flags_t)0x00u)
/** @brief |current| exceeded the overcurrent limit. */
#define FAULT_OVERCURRENT ((fault_flags_t)0x01u)
/** @brief Shaft stayed slow while driven hard. */
#define FAULT_STALL ((fault_flags_t)0x02u)

/** @brief Protection thresholds. */
typedef struct {
    milliamp_t overcurrent_ma;      /**< Trip when |current| is above this. */
    duty_permille_t stall_min_duty; /**< Stall counts only while |duty| >= this. */
    rpm_t stall_max_speed_rpm;      /**< Stall counts only while |speed| < this. */
    uint16_t stall_ticks;           /**< Consecutive stall steps that trip; >= 1. */
} fault_monitor_config_t;

/** @brief Monitor instance; owned by the caller. */
typedef struct {
    fault_monitor_config_t cfg; /**< Copy of the thresholds. */
    uint16_t stall_count;       /**< Consecutive steps meeting the stall condition. */
} fault_monitor_t;

/**
 * @brief Store the thresholds and reset the stall counter.
 * @param fm Monitor to initialise.
 * @param cfg Thresholds; copied.
 */
void fault_monitor_init(fault_monitor_t *fm, const fault_monitor_config_t *cfg);

/**
 * @brief Reset the stall counter.
 * @param fm Monitor.
 */
void fault_monitor_reset(fault_monitor_t *fm);

/**
 * @brief Evaluate one sample.
 * @param fm Monitor.
 * @param sample Measurement taken while @p applied_duty was driving the motor.
 * @param applied_duty Duty that produced the sample.
 * @return Faults detected in this step.
 */
fault_flags_t fault_monitor_step(fault_monitor_t *fm, const motor_sample_t *sample, duty_permille_t applied_duty);

#endif
