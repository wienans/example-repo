/**
 * @file pi_controller.c
 * @brief Fixed-point PI controller implementation.
 * @ingroup domain
 */
#include <stdbool.h>

#include "pi_controller.h"

/** @brief 1.0 in Q8. */
#define Q8_ONE 256

/**
 * @brief Limit a value to [lo, hi].
 * @param value Value to limit.
 * @param lo Lower bound.
 * @param hi Upper bound, >= lo.
 * @return The limited value.
 */
static int64_t clamp64(int64_t value, int64_t lo, int64_t hi)
{
    return value < lo ? lo : (value > hi ? hi : value);
}

/**
 * @brief Store the configuration and clear the integrator.
 * @relation(SWR-PI-001, SWR-PI-003, scope=function)
 */
void pi_init(pi_controller_t *pi, const pi_config_t *cfg)
{
    pi->cfg = *cfg;
    pi->integrator = 0;
}

/**
 * @brief Clear the integrator.
 * @relation(SWR-PI-003, scope=function)
 */
void pi_reset(pi_controller_t *pi)
{
    pi->integrator = 0;
}

/**
 * @brief Compute the clamped PI output with conditional integration.
 * @relation(SWR-PI-001, SWR-PI-002, scope=function)
 */
int32_t pi_step(pi_controller_t *pi, int32_t error)
{
    const int64_t out_min = pi->cfg.out_min;
    const int64_t out_max = pi->cfg.out_max;
    const int64_t proportional = (int64_t)pi->cfg.kp_q8 * error;
    const int64_t integrated = clamp64((int64_t)pi->integrator + (int64_t)pi->cfg.ki_q8 * error,
                                       out_min * Q8_ONE, out_max * Q8_ONE);
    const int64_t unclamped = (proportional + integrated) / Q8_ONE;

    const bool saturated_with_error = (unclamped > out_max && error > 0) || (unclamped < out_min && error < 0);
    if (!saturated_with_error) {
        pi->integrator = (int32_t)integrated;
    }
    return (int32_t)clamp64(unclamped, out_min, out_max);
}
