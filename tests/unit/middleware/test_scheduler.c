#include <stdint.h>

#include "unity.h"
#include "scheduler.h"

typedef struct {
    char id;
    int runs;
} probe_t;

static char order[16];
static int order_len;
static probe_t a;
static probe_t b;

static void record(void *ctx)
{
    probe_t *probe = ctx;
    probe->runs++;
    if (order_len < (int)sizeof order - 1) {
        order[order_len++] = probe->id;
    }
}

void setUp(void)
{
    order_len = 0;
    for (int i = 0; i < (int)sizeof order; i++) {
        order[i] = '\0';
    }
    a = (probe_t){ .id = 'A', .runs = 0 };
    b = (probe_t){ .id = 'B', .runs = 0 };
}

void tearDown(void) {}

/**
 * @brief A task first runs one full period after init, then every period.
 * @relation(SWR-SCH-001, scope=function)
 */
void test_task_runs_every_period(void)
{
    sched_task_t tasks[] = { { record, &a, 10, 0 } };
    sched_init(tasks, 1, 100);

    sched_run(tasks, 1, 109);
    TEST_ASSERT_EQUAL_INT(0, a.runs);
    sched_run(tasks, 1, 110);
    TEST_ASSERT_EQUAL_INT(1, a.runs);
    sched_run(tasks, 1, 115);
    sched_run(tasks, 1, 119);
    TEST_ASSERT_EQUAL_INT(1, a.runs);
    sched_run(tasks, 1, 120);
    TEST_ASSERT_EQUAL_INT(2, a.runs);
}

/**
 * @brief A late call does not shift later deadlines.
 * @relation(SWR-SCH-001, scope=function)
 */
void test_late_call_keeps_fixed_rate(void)
{
    sched_task_t tasks[] = { { record, &a, 10, 0 } };
    sched_init(tasks, 1, 0);

    sched_run(tasks, 1, 13);
    TEST_ASSERT_EQUAL_INT(1, a.runs);
    sched_run(tasks, 1, 19);
    TEST_ASSERT_EQUAL_INT(1, a.runs);
    sched_run(tasks, 1, 20);
    TEST_ASSERT_EQUAL_INT(2, a.runs);
}

/**
 * @brief Due tasks run in table order, each at most once per call.
 * @relation(SWR-SCH-001, scope=function)
 */
void test_due_tasks_run_in_table_order_once_per_call(void)
{
    sched_task_t tasks[] = { { record, &b, 1, 0 }, { record, &a, 2, 0 } };
    sched_init(tasks, 2, 0);

    sched_run(tasks, 2, 1);
    sched_run(tasks, 2, 2);
    sched_run(tasks, 2, 10);
    TEST_ASSERT_EQUAL_STRING("BBABA", order);
}

/**
 * @brief Elapsed time is computed correctly when the millisecond counter wraps.
 * @relation(SWR-SCH-001, scope=function)
 */
void test_wraparound_of_time(void)
{
    sched_task_t tasks[] = { { record, &a, 10, 0 } };
    sched_init(tasks, 1, UINT32_MAX - 7u);

    sched_run(tasks, 1, UINT32_MAX);
    TEST_ASSERT_EQUAL_INT(0, a.runs);
    sched_run(tasks, 1, 1u);
    TEST_ASSERT_EQUAL_INT(0, a.runs);
    sched_run(tasks, 1, 2u);
    TEST_ASSERT_EQUAL_INT(1, a.runs);
    sched_run(tasks, 1, 11u);
    TEST_ASSERT_EQUAL_INT(1, a.runs);
    sched_run(tasks, 1, 12u);
    TEST_ASSERT_EQUAL_INT(2, a.runs);
}

/**
 * @brief The same time passed twice does not run a task twice.
 * @relation(SWR-SCH-001, scope=function)
 */
void test_repeated_time_does_not_rerun(void)
{
    sched_task_t tasks[] = { { record, &a, 1, 0 } };
    sched_init(tasks, 1, 0);

    sched_run(tasks, 1, 1);
    sched_run(tasks, 1, 1);
    TEST_ASSERT_EQUAL_INT(1, a.runs);
}
