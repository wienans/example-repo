#include <stddef.h>

#include "unity.h"
#include "motor_fsm.h"

void setUp(void) {}
void tearDown(void) {}

/**
 * @brief The machine starts in IDLE.
 * @relation(SWR-FSM-001, scope=function)
 */
void test_initial_state_is_idle(void)
{
    TEST_ASSERT_EQUAL(MOTOR_STATE_IDLE, MOTOR_FSM_INITIAL_STATE);
}

/**
 * @brief Every state/event cell yields the transition the requirements define.
 * @relation(SWR-FSM-001, SWR-FSM-002, SWR-FSM-003, scope=function)
 */
void test_every_cell_of_the_transition_table(void)
{
    static const struct {
        motor_state_t from;
        motor_event_t event;
        motor_state_t to;
        const char *name;
    } cells[] = {
        { MOTOR_STATE_IDLE, MOTOR_EVENT_START, MOTOR_STATE_RUNNING, "IDLE+START" },
        { MOTOR_STATE_IDLE, MOTOR_EVENT_STOP, MOTOR_STATE_IDLE, "IDLE+STOP" },
        { MOTOR_STATE_IDLE, MOTOR_EVENT_FAULT, MOTOR_STATE_FAULT, "IDLE+FAULT" },
        { MOTOR_STATE_IDLE, MOTOR_EVENT_CLEAR_FAULT, MOTOR_STATE_IDLE, "IDLE+CLEAR_FAULT" },
        { MOTOR_STATE_RUNNING, MOTOR_EVENT_START, MOTOR_STATE_RUNNING, "RUNNING+START" },
        { MOTOR_STATE_RUNNING, MOTOR_EVENT_STOP, MOTOR_STATE_IDLE, "RUNNING+STOP" },
        { MOTOR_STATE_RUNNING, MOTOR_EVENT_FAULT, MOTOR_STATE_FAULT, "RUNNING+FAULT" },
        { MOTOR_STATE_RUNNING, MOTOR_EVENT_CLEAR_FAULT, MOTOR_STATE_RUNNING, "RUNNING+CLEAR_FAULT" },
        { MOTOR_STATE_FAULT, MOTOR_EVENT_START, MOTOR_STATE_FAULT, "FAULT+START" },
        { MOTOR_STATE_FAULT, MOTOR_EVENT_STOP, MOTOR_STATE_FAULT, "FAULT+STOP" },
        { MOTOR_STATE_FAULT, MOTOR_EVENT_FAULT, MOTOR_STATE_FAULT, "FAULT+FAULT" },
        { MOTOR_STATE_FAULT, MOTOR_EVENT_CLEAR_FAULT, MOTOR_STATE_IDLE, "FAULT+CLEAR_FAULT" },
    };
    TEST_ASSERT_EQUAL(MOTOR_STATE_COUNT * MOTOR_EVENT_COUNT, sizeof cells / sizeof cells[0]);
    for (size_t i = 0; i < sizeof cells / sizeof cells[0]; i++) {
        TEST_ASSERT_EQUAL_MESSAGE(cells[i].to, motor_fsm_next(cells[i].from, cells[i].event), cells[i].name);
    }
}
