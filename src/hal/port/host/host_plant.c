/**
 * @file host_plant.c
 * @brief First-order DC motor model.
 * @ingroup hal
 */
#include "host_plant.h"

#include <math.h>

/* 24 V motor, Kv = 100 rpm/V (2400 rpm no-load), R = 4 ohm (6 A locked at
 * full duty), mechanical time constant J*R/(Kt*Ke) = 50 ms. The electrical
 * time constant is ignored, which makes the model first order in speed. */
/** @brief Radians per revolution. */
#define PLANT_TWO_PI 6.28318530717959
/** @brief Speed constant. */
#define PLANT_KV_RPM_PER_V 100.0
/** @brief Back-EMF constant in V/(rad/s). */
#define PLANT_KE (60.0 / (PLANT_TWO_PI * PLANT_KV_RPM_PER_V))
/** @brief Torque constant in N*m/A; equals Ke in SI units. */
#define PLANT_KT PLANT_KE
/** @brief Armature resistance. */
#define PLANT_R_OHM 4.0
/** @brief Rotor inertia giving a 50 ms mechanical time constant. */
#define PLANT_J_KGM2 (0.050 * PLANT_KT * PLANT_KE / PLANT_R_OHM)
/** @brief Viscous friction. */
#define PLANT_B_NM_PER_RAD_S 1.0e-5
/** @brief Coulomb friction. */
#define PLANT_COULOMB_NM 0.005

/**
 * @brief Integrate the motor one Euler step.
 */
void host_plant_step(host_plant_t *plant, double voltage_v, bool driven, double dt_s)
{
    if (plant->locked) {
        plant->omega_rad_s = 0.0;
    }
    plant->current_a = driven ? (voltage_v - PLANT_KE * plant->omega_rad_s) / PLANT_R_OHM : 0.0;
    if (plant->locked) {
        return;
    }

    double drive_nm = PLANT_KT * plant->current_a - PLANT_B_NM_PER_RAD_S * plant->omega_rad_s;
    if (plant->omega_rad_s == 0.0 && fabs(drive_nm) <= PLANT_COULOMB_NM) {
        return;
    }
    double friction_nm = copysign(PLANT_COULOMB_NM, plant->omega_rad_s != 0.0 ? plant->omega_rad_s : drive_nm);
    double next = plant->omega_rad_s + (drive_nm - friction_nm) / PLANT_J_KGM2 * dt_s;
    /* Friction alone must stop the shaft, not reverse it. */
    if (plant->omega_rad_s != 0.0 && next * plant->omega_rad_s < 0.0 && fabs(drive_nm) <= PLANT_COULOMB_NM) {
        next = 0.0;
    }
    plant->omega_rad_s = next;
    plant->position_rev += next / PLANT_TWO_PI * dt_s;
}
