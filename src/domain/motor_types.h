/**
 * @file motor_types.h
 * @brief Physical quantities exchanged between the domain core and the BSP.
 *
 * @defgroup domain Domain
 * @brief Pure, hardware-free motor control logic. Depends only on the C
 *        freestanding headers and other domain modules.
 * @{
 */
#ifndef MOTOR_TYPES_H
#define MOTOR_TYPES_H

#include <stdbool.h>
#include <stdint.h>

/** @brief Shaft speed in revolutions per minute; positive is forward. */
typedef int32_t rpm_t;
/** @brief Signed drive duty in 0.1 % steps, -1000..1000; the sign is direction. */
typedef int16_t duty_permille_t;
/** @brief Armature current in milliamperes; positive while motoring forward. */
typedef int32_t milliamp_t;

/** @brief One synchronous measurement of the motor. */
typedef struct {
    rpm_t speed_rpm;       /**< Measured shaft speed. */
    milliamp_t current_ma; /**< Measured armature current. */
} motor_sample_t;

/** @brief Command for the power stage. */
typedef struct {
    bool enable;          /**< false lets the motor coast. */
    duty_permille_t duty; /**< Signed duty; 0 whenever enable is false. */
} drive_cmd_t;

/** @} */
#endif
