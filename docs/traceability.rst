Traceability
============

Every software requirement with the system requirements it refines and the
code, checks and tests that close it. The Code traceability, Test results and
Code coverage pages hold the linked needs; ``make reports`` writes them.

Requirement tree
----------------

.. needflow::
   :types: sys, swr
   :link_types: refines
   :direction: right
   :show_link_names:

System to software
------------------

.. needtable::
   :types: sys
   :columns: id, title, refines_back as "Refined by"
   :style: table

Software requirements
---------------------

.. needtable::
   :types: swr
   :columns: id, title, refines, implements_back as "Implemented by", verifies_back as "Verified by", measures_back as "Coverage"
   :style: table

Test status
-----------

.. needpie:: Test results by status
   :labels: Passed, Failed, Skipped, Not run
   :colors: #2e7d2e, #c62828, #d99a00, #888888

   type == "test" and status == "PASSED"
   type == "test" and status == "FAILED"
   type == "test" and status == "SKIPPED"
   type == "test" and status == "NOT_RUN"

.. needtable::
   :types: test
   :filter: status != "PASSED"
   :columns: id, title, status, verifies, location
   :style: table
