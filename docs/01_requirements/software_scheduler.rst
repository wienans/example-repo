Middleware: scheduler
=====================

.. swr:: Fixed-period cooperative scheduling
   :id: SWR-SCH-001
   :refines: SYS-007

   ``sched_run`` shall call each task whose period has elapsed since its last run,
   in table order, once per call. It shall keep the period correct when the
   millisecond tick wraps around ``UINT32_MAX``.
