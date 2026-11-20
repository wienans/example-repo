System requirements
===================

Purpose
-------

This document states what the motor control system must do, as seen by the
operator and by the team that ports the firmware to a new board. The software
requirements in :doc:`software_requirements` refine each item here.

Motor control
-------------

.. sys:: Closed-loop speed control
   :id: SYS-001

   The system shall hold the motor shaft speed within 2 % of the commanded
   setpoint in steady state, and shall settle to that band within 1 s of a start
   command.

   *Rationale:* The driven load needs a known speed. Open-loop duty control drifts with supply
   voltage and load torque.

.. sys:: Operator start and stop
   :id: SYS-002

   The system shall start the motor when the operator presses the start button,
   and shall stop the motor when the operator presses the stop button.

Protection
----------

.. sys:: Overcurrent protection
   :id: SYS-003

   The system shall disable the motor drive within one control period when the
   motor current exceeds the configured limit.

   *Rationale:* Sustained overcurrent damages the H-bridge and the motor windings.

.. sys:: Stall protection
   :id: SYS-004

   The system shall disable the motor drive when the motor is driven but does not
   turn for a configured time.

.. sys:: Fault recovery
   :id: SYS-005

   After a fault, the system shall keep the drive disabled until the operator
   presses the stop button to acknowledge the fault.

Quality attributes
------------------

.. sys:: Platform portability
   :id: SYS-006

   The application and domain logic shall build without change for any MCU that
   provides an implementation of the HAL interfaces in ``src/hal``.

   *Rationale:* The product line uses more than one MCU vendor. A port must only touch the HAL
   port and the board support package.

.. sys:: Deterministic behavior
   :id: SYS-007

   The control loop shall run at a fixed period of 1 ms, and shall produce the
   same outputs for the same inputs on every target.

   *Rationale:* Floating-point rounding, heap allocation and unbounded loops make timing and
   results differ between targets and between runs.

.. sys:: Host testability
   :id: SYS-008

   All logic above the HAL port shall be testable on a development host without
   target hardware.
