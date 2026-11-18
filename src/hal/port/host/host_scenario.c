/**
 * @file host_scenario.c
 * @brief Scripted run: start at 10 ms, rotor lock at 1500 ms, end at 2500 ms.
 * @ingroup hal
 */
#include "host_scenario.h"

#include <stdio.h>
#include <stdlib.h>

#include "app.h"

/** @brief Time the start button goes down. */
#define SCENARIO_START_PRESS_MS 10u
/** @brief How long the start button is held. */
#define SCENARIO_PRESS_LENGTH_MS 50u
/** @brief Time the rotor is mechanically blocked. */
#define SCENARIO_LOCK_MS 1500u
/** @brief Time the simulation ends. */
#define SCENARIO_END_MS 2500u
/** @brief Telemetry row interval. */
#define SCENARIO_TELEMETRY_MS 10u

/** @brief Printable name of each motor state. */
static const char *const k_state_names[MOTOR_STATE_COUNT] = {
    [MOTOR_STATE_IDLE] = "IDLE",
    [MOTOR_STATE_RUNNING] = "RUNNING",
    [MOTOR_STATE_FAULT] = "FAULT",
};

/**
 * @brief Print a CSV row every 10 ms and end the run at 2500 ms.
 */
void host_scenario_before_tick(uint32_t now_ms)
{
    if (now_ms == 0u) {
        printf("t_ms,setpoint_rpm,speed_rpm,current_ma,duty,state\n");
    }
    if (now_ms % SCENARIO_TELEMETRY_MS == 0u) {
        const app_status_t s = app_status();
        printf("%lu,%ld,%ld,%ld,%d,%s\n", (unsigned long)now_ms, (long)s.setpoint_rpm, (long)s.sample.speed_rpm,
               (long)s.sample.current_ma, (int)s.cmd.duty, k_state_names[s.state]);
    }
    if (now_ms >= SCENARIO_END_MS) {
        fflush(stdout);
        exit(0);
    }
}

/**
 * @brief Start button held from 10 ms for 50 ms.
 */
bool host_scenario_start_pressed(uint32_t now_ms)
{
    return now_ms >= SCENARIO_START_PRESS_MS && now_ms < SCENARIO_START_PRESS_MS + SCENARIO_PRESS_LENGTH_MS;
}

/**
 * @brief Stop button is never pressed in this scenario.
 */
bool host_scenario_stop_pressed(uint32_t now_ms)
{
    (void)now_ms;
    return false;
}

/**
 * @brief Rotor locked from 1500 ms on.
 */
bool host_scenario_rotor_locked(uint32_t now_ms)
{
    return now_ms >= SCENARIO_LOCK_MS;
}
