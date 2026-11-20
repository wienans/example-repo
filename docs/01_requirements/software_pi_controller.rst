Domain: PI controller
=====================

.. swr:: Proportional-integral output
   :id: SWR-PI-001
   :refines: SYS-001, SYS-007

   ``pi_step`` shall return ``Kp * e + I``, clamped to ``[out_min, out_max]``,
   where ``e`` is the speed error and ``I`` is the accumulated integral term
   ``sum(Ki * e)``. Gains are Q8 fixed-point integers, so a gain of 256 is 1.0.

.. swr:: Integrator anti-windup
   :id: SWR-PI-002
   :refines: SYS-001

   The integral term shall stay within the output limits, and shall not grow
   further while the output is saturated in the direction of the error.

   *Rationale:* Without this, a long saturation stores a large integral that overshoots the
   setpoint when the load releases.

.. swr:: Controller reset
   :id: SWR-PI-003
   :refines: SYS-001

   ``pi_reset`` shall set the integral term to zero.
