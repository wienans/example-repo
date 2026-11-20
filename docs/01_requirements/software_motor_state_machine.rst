Domain: motor state machine
===========================

.. swr:: Motor states
   :id: SWR-FSM-001
   :refines: SYS-002

   The motor state machine shall have the states ``IDLE``, ``RUNNING`` and
   ``FAULT``, and shall start in ``IDLE``.

.. swr:: Start and stop transitions
   :id: SWR-FSM-002
   :refines: SYS-002

   The ``START`` event shall move ``IDLE`` to ``RUNNING``. The ``STOP`` event
   shall move ``RUNNING`` to ``IDLE``. Any other event in those states shall leave
   the state unchanged, except ``FAULT``.

.. swr:: Fault entry and acknowledge
   :id: SWR-FSM-003
   :refines: SYS-005

   The ``FAULT`` event shall move every state to ``FAULT``. In ``FAULT``, only
   ``CLEAR_FAULT`` shall change the state, and it shall move to ``IDLE``.
