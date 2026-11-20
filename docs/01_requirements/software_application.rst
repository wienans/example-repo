Application
===========

.. swr:: Task periods
   :id: SWR-APP-001
   :refines: SYS-007

   The application shall run the control task every 1 ms and the user interface
   task every 10 ms.

.. swr:: Button events
   :id: SWR-APP-002
   :refines: SYS-002, SYS-005

   A rising edge of the start button shall send ``START``. A rising edge of the
   stop button shall send ``CLEAR_FAULT`` in ``FAULT`` and ``STOP`` in every other
   state.
