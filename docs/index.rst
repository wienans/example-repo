Motor control example
=====================

Firmware for closed-loop speed control of a brushed DC motor. The pages below
hold its requirements, architecture, design decisions, C API, and the results
of the last test and coverage run, all linked by requirement ID.

.. toctree::
   :maxdepth: 2
   :caption: Requirements

   01_requirements/system_requirements
   01_requirements/software_requirements

.. toctree::
   :maxdepth: 1
   :caption: Architecture
   :glob:

   02_architecture/*

.. toctree::
   :maxdepth: 1
   :caption: Decisions
   :glob:

   adr/*

.. toctree::
   :maxdepth: 2
   :caption: Reference

   api
   traceability

.. toctree::
   :maxdepth: 2
   :caption: Evidence

   generated/code
   generated/test_results
   generated/coverage
