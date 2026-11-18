/**
 * @file motor_fsm.h
 * @brief Operating-mode state machine of the motor.
 * @ingroup domain
 */
#ifndef MOTOR_FSM_H
#define MOTOR_FSM_H

/** @addtogroup domain
 * @{
 */

/** @brief Operating mode. */
typedef enum {
    MOTOR_STATE_IDLE = 0, /**< Drive disabled, ready to start. Initial state. */
    MOTOR_STATE_RUNNING,  /**< Closed-loop speed control active. */
    MOTOR_STATE_FAULT,    /**< Drive disabled until the fault is cleared. */
    MOTOR_STATE_COUNT     /**< Number of states; not a state. */
} motor_state_t;

/** @brief Input to the state machine. */
typedef enum {
    MOTOR_EVENT_START = 0,   /**< Operator start request. */
    MOTOR_EVENT_STOP,        /**< Operator stop request. */
    MOTOR_EVENT_FAULT,       /**< A protection tripped. */
    MOTOR_EVENT_CLEAR_FAULT, /**< Operator acknowledges a fault. */
    MOTOR_EVENT_COUNT        /**< Number of events; not an event. */
} motor_event_t;

/** @brief State a new controller starts in. */
#define MOTOR_FSM_INITIAL_STATE MOTOR_STATE_IDLE

/**
 * @brief Transition function.
 * @param state Current state, below MOTOR_STATE_COUNT.
 * @param event Event, below MOTOR_EVENT_COUNT.
 * @return Next state; equal to @p state when the event does not apply.
 */
motor_state_t motor_fsm_next(motor_state_t state, motor_event_t event);

/** @} */
#endif
