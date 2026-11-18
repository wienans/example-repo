/**
 * @file scheduler.h
 * @brief Cooperative fixed-period task scheduler.
 *
 * @defgroup middleware Middleware
 * @brief Hardware-independent services for the application layer.
 * @{
 */
#ifndef SCHEDULER_H
#define SCHEDULER_H

#include <stddef.h>
#include <stdint.h>

/** @brief Task body; runs to completion. */
typedef void (*sched_task_fn)(void *ctx);

/** @brief One entry of a caller-owned task table. */
typedef struct {
    sched_task_fn fn;     /**< Task body. */
    void *ctx;            /**< Argument passed to @ref fn. */
    uint32_t period_ms;   /**< Run interval; > 0. */
    uint32_t last_run_ms; /**< Start of the current period; set by the scheduler. */
} sched_task_t;

/**
 * @brief Start every task's first period at @p now_ms.
 * @param tasks Task table.
 * @param count Number of entries in @p tasks.
 * @param now_ms Current time.
 */
void sched_init(sched_task_t *tasks, size_t count, uint32_t now_ms);

/**
 * @brief Run each due task once, in table order.
 *
 * A task is due when at least period_ms has elapsed since the start of its
 * current period. Periods advance by exactly period_ms, so the rate does not
 * drift when a call is late. Time may wrap modulo 2^32.
 *
 * @param tasks Task table passed to sched_init().
 * @param count Number of entries in @p tasks.
 * @param now_ms Current time.
 */
void sched_run(sched_task_t *tasks, size_t count, uint32_t now_ms);

/** @} */
#endif
