/**
 * @file host_scenario.h
 * @brief Scripted operator inputs and disturbances for the host simulation.
 * @ingroup hal
 */
#ifndef HOST_SCENARIO_H
#define HOST_SCENARIO_H

/** @addtogroup hal
 * @{
 */

#include <stdbool.h>
#include <stdint.h>

/**
 * @brief Hook run at the start of every tick, before time advances.
 * @param now_ms Simulated time whose control cycle has just completed.
 */
void host_scenario_before_tick(uint32_t now_ms);

/**
 * @brief Whether the start button is held.
 * @param now_ms Simulated time.
 * @return true while pressed.
 */
bool host_scenario_start_pressed(uint32_t now_ms);

/**
 * @brief Whether the stop button is held.
 * @param now_ms Simulated time.
 * @return true while pressed.
 */
bool host_scenario_stop_pressed(uint32_t now_ms);

/**
 * @brief Whether the rotor is mechanically blocked.
 * @param now_ms Simulated time.
 * @return true once the lock has happened.
 */
bool host_scenario_rotor_locked(uint32_t now_ms);

/** @} */
#endif
