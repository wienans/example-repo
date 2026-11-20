Architecture constraints
========================

.. swr:: Layer include rule
   :id: SWR-ARC-001
   :refines: SYS-006, SYS-008

   Source files shall include only headers from the layers they may depend on:
   ``app`` on ``app``, ``domain``, ``middleware`` and ``bsp``. ``domain`` on
   ``domain``. ``middleware`` on ``middleware``. ``bsp`` on ``bsp``, ``hal`` and
   ``domain``. ``hal`` on ``hal``. Only ``src/hal/port`` may include vendor
   headers. ``tools/check_layers.py`` enforces this rule.

.. swr:: No heap and no floating point
   :id: SWR-DET-001
   :refines: SYS-007

   Source files outside ``src/hal/port`` shall not call ``malloc``, ``calloc``,
   ``realloc`` or ``free``, and shall not use ``float`` or ``double``.
   ``tools/check_layers.py`` enforces this rule.
