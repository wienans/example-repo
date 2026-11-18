/**
 * @file host_plant.h
 * @brief First-order DC motor model used by the host port.
 * @ingroup hal
 */
#ifndef HOST_PLANT_H
#define HOST_PLANT_H

/** @addtogroup hal
 * @{
 */

#include <stdbool.h>

/** @brief Motor state integrated by host_plant_step(). */
typedef struct {
    double omega_rad_s;  /**< Shaft speed. */
    double position_rev; /**< Shaft angle in revolutions, unbounded. */
    double current_a;    /**< Armature current. */
    bool locked;         /**< Rotor mechanically blocked. */
} host_plant_t;

/**
 * @brief Advance the model by one time step.
 * @param plant Model state.
 * @param voltage_v Armature voltage applied by the H-bridge.
 * @param driven false when the bridge is disabled and the motor coasts.
 * @param dt_s Step length in seconds.
 */
void host_plant_step(host_plant_t *plant, double voltage_v, bool driven, double dt_s);

/** @} */
#endif
