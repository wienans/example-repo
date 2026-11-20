Domain: motor control
=====================

.. swr:: Setpoint clamp and ramp
   :id: SWR-CTL-001
   :refines: SYS-001

   ``motor_control_set_speed`` shall clamp the target to
   ``[-max_setpoint_rpm, max_setpoint_rpm]``. Each ``motor_control_step`` call
   shall move the ramped setpoint toward the target by at most
   ``ramp_rpm_per_tick``.

.. swr:: Drive disabled outside RUNNING
   :id: SWR-CTL-002
   :refines: SYS-002, SYS-005

   In every state other than ``RUNNING``, ``motor_control_step`` shall return a
   drive command with ``enable = false`` and ``duty = 0``.

.. swr:: Bumpless start
   :id: SWR-CTL-003
   :refines: SYS-001

   On entering ``RUNNING``, the controller shall reset the PI controller and start
   the ramped setpoint at the measured speed.

   *Rationale:* Starting the ramp at the measured speed avoids a step in duty when the operator
   restarts a motor that is still coasting.

.. swr:: Same-step fault shutdown
   :id: SWR-CTL-004
   :refines: SYS-003, SYS-004, SYS-005

   When the fault monitor reports a fault, ``motor_control_step`` shall latch the
   fault flags, move the state machine to ``FAULT``, and return a disabled drive
   command in that same call. ``CLEAR_FAULT`` shall clear the latched flags.
