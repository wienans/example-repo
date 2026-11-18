/**
 * @file motor_fsm.c
 * @brief Table-driven motor state machine.
 * @ingroup domain
 */
#include "motor_fsm.h"

/** @brief Next state indexed by [current state][event]. */
static const motor_state_t k_transitions[MOTOR_STATE_COUNT][MOTOR_EVENT_COUNT] = {
    [MOTOR_STATE_IDLE] = {
        [MOTOR_EVENT_START] = MOTOR_STATE_RUNNING,
        [MOTOR_EVENT_STOP] = MOTOR_STATE_IDLE,
        [MOTOR_EVENT_FAULT] = MOTOR_STATE_FAULT,
        [MOTOR_EVENT_CLEAR_FAULT] = MOTOR_STATE_IDLE,
    },
    [MOTOR_STATE_RUNNING] = {
        [MOTOR_EVENT_START] = MOTOR_STATE_RUNNING,
        [MOTOR_EVENT_STOP] = MOTOR_STATE_IDLE,
        [MOTOR_EVENT_FAULT] = MOTOR_STATE_FAULT,
        [MOTOR_EVENT_CLEAR_FAULT] = MOTOR_STATE_RUNNING,
    },
    [MOTOR_STATE_FAULT] = {
        [MOTOR_EVENT_START] = MOTOR_STATE_FAULT,
        [MOTOR_EVENT_STOP] = MOTOR_STATE_FAULT,
        [MOTOR_EVENT_FAULT] = MOTOR_STATE_FAULT,
        [MOTOR_EVENT_CLEAR_FAULT] = MOTOR_STATE_IDLE,
    },
};

/**
 * @brief Look up the next state in the transition table.
 * @relation(SWR-FSM-001, SWR-FSM-002, SWR-FSM-003, scope=function)
 */
motor_state_t motor_fsm_next(motor_state_t state, motor_event_t event)
{
    return k_transitions[state][event];
}
