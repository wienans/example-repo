Board support package
=====================

.. swr:: Encoder speed conversion
   :id: SWR-BSP-001
   :refines: SYS-001, SYS-006

   ``bsp_motor_sample`` shall compute the speed from the change of the 16-bit
   encoder count since the previous sample, the board's counts per revolution and
   the 1 ms sample period. The result shall be correct when the counter wraps.

.. swr:: Current conversion
   :id: SWR-BSP-002
   :refines: SYS-003, SYS-006

   ``bsp_motor_sample`` shall convert the raw ADC reading of the current-sense
   channel to mA with the board's scale and offset.

.. swr:: Drive command mapping
   :id: SWR-BSP-003
   :refines: SYS-006

   ``bsp_motor_apply`` shall set the direction pin from the sign of the duty, set
   the PWM duty to the absolute duty, and set the bridge enable pin from
   ``enable``.

.. swr:: Checked initialisation
   :id: SWR-BSP-004
   :refines: SYS-006

   ``bsp_init`` shall check the status of every HAL initialisation call and return
   ``false`` if any call fails.
