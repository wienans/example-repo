/**
 * @file pi_controller.h
 * @brief Fixed-point PI controller with output clamping and anti-windup.
 * @ingroup domain
 */
#ifndef PI_CONTROLLER_H
#define PI_CONTROLLER_H

#include <stdint.h>

/**
 * @brief Controller tuning and output limits.
 *
 * Gains are Q8 (value / 256). Gains up to 65535 and |error| up to 100000
 * cannot overflow. |out_min| and |out_max| must not exceed INT32_MAX / 256
 * because the integrator is stored in Q8 output units.
 */
typedef struct {
    int32_t kp_q8;   /**< Proportional gain, Q8. */
    int32_t ki_q8;   /**< Integral gain per step, Q8. */
    int32_t out_min; /**< Lowest output; must be <= out_max. */
    int32_t out_max; /**< Highest output. */
} pi_config_t;

/** @brief Controller instance; owned by the caller. */
typedef struct {
    pi_config_t cfg;    /**< Copy of the configuration. */
    int32_t integrator; /**< Integral term in Q8 output units. */
} pi_controller_t;

/**
 * @brief Store the configuration and clear the integrator.
 * @param pi Controller to initialise.
 * @param cfg Tuning and limits; copied.
 */
void pi_init(pi_controller_t *pi, const pi_config_t *cfg);

/**
 * @brief Clear the integrator, keeping the configuration.
 * @param pi Controller to reset.
 */
void pi_reset(pi_controller_t *pi);

/**
 * @brief Run one control step.
 * @param pi Controller.
 * @param error Setpoint minus measurement.
 * @return (Kp * error + integral) clamped to [out_min, out_max].
 */
int32_t pi_step(pi_controller_t *pi, int32_t error);

#endif
