/**
 * @file scheduler.c
 * @brief Cooperative fixed-period task scheduler implementation.
 * @ingroup middleware
 */
#include "scheduler.h"

/**
 * @brief Start every task's first period at now_ms.
 * @relation(SWR-SCH-001, scope=function, role=Implementation)
 */
void sched_init(sched_task_t *tasks, size_t count, uint32_t now_ms)
{
    for (size_t i = 0; i < count; i++) {
        tasks[i].last_run_ms = now_ms;
    }
}

/**
 * @brief Run due tasks in table order.
 * @relation(SWR-SCH-001, scope=function, role=Implementation)
 */
void sched_run(sched_task_t *tasks, size_t count, uint32_t now_ms)
{
    for (size_t i = 0; i < count; i++) {
        /* Unsigned subtraction is modulo 2^32, so the elapsed time is correct
         * across a wrap of now_ms as long as it is below 2^32 ms. */
        if ((uint32_t)(now_ms - tasks[i].last_run_ms) >= tasks[i].period_ms) {
            tasks[i].last_run_ms += tasks[i].period_ms;
            tasks[i].fn(tasks[i].ctx);
        }
    }
}
