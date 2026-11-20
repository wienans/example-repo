Domain: fault monitor
=====================

.. swr:: Overcurrent detection
   :id: SWR-FLT-001
   :refines: SYS-003

   ``fault_monitor_step`` shall report ``FAULT_OVERCURRENT`` in the same call in
   which the absolute motor current exceeds ``overcurrent_ma``.

.. swr:: Stall detection
   :id: SWR-FLT-002
   :refines: SYS-004

   ``fault_monitor_step`` shall report ``FAULT_STALL`` when, for ``stall_ticks``
   consecutive calls, the absolute duty is at least ``stall_min_duty`` and the
   absolute speed is below ``stall_max_speed_rpm``. A call that breaks either
   condition shall restart the count.
