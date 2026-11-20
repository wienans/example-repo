Software requirements
=====================

Conventions
-----------

Each requirement names the module that implements it. Code and tests point back
at a requirement with a marker inside their Doxygen comment, in the form
``@relation(SWR-PI-001, scope=function, role=Implementation)``. The role is
``Implementation`` in ``src/``, ``Test`` in ``tests/`` and ``Check`` in
``tools/``. Where only part of a function implements a requirement,
``scope=line`` marks one code line and ``scope=range_start`` /
``scope=range_end`` mark several. ``make docs`` fails when a marker names a UID that this document
does not define. ``make trace`` fails when a requirement has no
implementation, or when none of its tests passed in the last Ceedling run.

Units: speed in rpm (``rpm_t``), current in mA (``milliamp_t``), and duty in
permille from -1000 to 1000 (``duty_permille_t``). The sign of the duty sets
the direction of rotation.

.. toctree::
   :maxdepth: 1

   software_pi_controller
   software_motor_state_machine
   software_fault_monitor
   software_motor_control
   software_scheduler
   software_board_support_package
   software_application
   software_architecture_constraints
