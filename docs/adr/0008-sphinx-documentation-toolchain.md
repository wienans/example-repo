# ADR-0008 Sphinx documentation toolchain

- Status: proposed
- Date: 2026-11-20
- Supersedes: [ADR-0006](0006-documentation-toolchain.md)

## Context

ADR-0006 built the documentation on StrictDoc. Two parts of that setup work against the tool:

- StrictDoc builds a requirement's links to code from the depth of the document that defines it. So every document with requirements, generated ones included, has to sit at the same folder depth.
- Its JUnit and gcov imports do not fit Ceedling, so two scripts write native `.sdoc` documents. Test status shows only through a UID suffix that the CSS colours.

This branch tries Sphinx with sphinx-needs instead. sphinx-needs models requirements, tests and other artifacts as typed objects with typed links. Breathe brings the Doxygen API into the same site.

## Decision

| Content | Format | Location | Tool |
| --- | --- | --- | --- |
| Requirements | sphinx-needs `sys` and `swr` directives in reStructuredText | `docs/01_requirements/` | Sphinx, sphinx-needs |
| Architecture | Markdown with Mermaid flowcharts, sequence and state diagrams | `docs/02_architecture/` | MyST, sphinxcontrib-mermaid, GitHub |
| Decisions | Markdown | `docs/adr/` | MyST, GitHub |
| C API | Doxygen comments in `src/**/*.h` | `src/` | Doxygen XML, Breathe |
| Code traceability | Generated `impl` and `check` needs from the `@relation` markers | `docs/generated/` (git-ignored) | `tools/code_to_rst.py` |
| Test results | Generated `test` needs from Ceedling's JUnit report | `docs/generated/` (git-ignored) | `tools/test_results_to_rst.py` |
| Coverage | Generated `cov` needs from gcovr's JSON, plus gcovr's HTML | `docs/generated/` (git-ignored) | `tools/coverage_to_rst.py`, gcovr |

`docs/conf.py` declares one need type per artifact and one link type per relation:

| Need type | ID | Link | Target |
| --- | --- | --- | --- |
| `sys` System requirement | `SYS-nnn` | | |
| `swr` Software requirement | `SWR-<domain>-nnn` | `refines` | `sys` |
| `impl` Implementation | `IMPL-nnn` | `implements` | `swr` |
| `check` Check | `CHK-nnn` | `verifies` | `swr` |
| `test` Test result | `TR-nnn` | `verifies` | `swr` |
| `cov` Coverage | `COV-nnn` | `measures` | `swr` |

sphinx-needs adds the incoming side of each link to the target. A requirement page therefore lists "is refined by", "is implemented by", "is verified by" and "is measured by" with no extra markup.

The pieces connect in these places:

1. The `@relation(SWR-PI-001, scope=function, role=Implementation)` markers in the Doxygen comments stay as they were. `tools/source_markers.py` still reads them for every tool. `tools/code_to_rst.py` turns each `Implementation` and `Check` marker into a need, with a cross-reference to the Breathe entry of the function and a `literalinclude` of the marked lines.
2. Markdown pages link to a requirement with the MyST role `` {need}`SWR-PI-001` ``.
3. `make docs` runs `sphinx-build -W`. A link to an unknown need ID is a warning, so a marker or a role that names an unknown requirement fails the build. StrictDoc did the same on an unknown UID.
4. Each test result carries its status as the need's `status`, an enum that `needs_fields` declares, and as a `style` that `docs/_static/status.css` colours. The traceability page filters and counts on the status, for example with `needtable` and `needpie`.
5. `tools/check_trace.py` keeps the `make trace` gate. It now reads the requirement IDs from the `:id:` lines of `docs/01_requirements/*.rst`. Its check that every domain file is included went away, because Sphinx warns about a page that no toctree lists.
6. Mermaid CLI renders each diagram to SVG at build time. That is the same `mmdc` that `make diagrams` checks with, using the same configuration, so the site needs no network and prints to PDF.
7. Breathe renders the API page from Doxygen's XML, one `doxygengroup` per layer. `docs/conf.py` patches one Breathe function: Doxygen 1.18 writes a function-pointer typedef in a form that Breathe 5.1 cannot parse.

## Consequences

- One `sphinx-build` produces requirements, architecture, ADRs, the API and the evidence as one site with one search and one navigation. The Doxygen HTML stays for its source browser.
- Generated pages can sit anywhere under `docs/`. Links go by need ID, not by folder depth.
- `make docs` writes `needs.json`, a machine-readable export of every need and link.
- A need has no machine ID like StrictDoc's `MID`. The release changelog matches needs by ID, so a renamed ID shows as one removed need and one added need.
- There is no browser editor like `strictdoc server`. Requirements are edited as text.
- The C domain in Sphinx knows only the functions that Breathe renders. A marker on a static function in a `.c` file links to the code, not to an API entry.
- ADR-0001 and ADR-0007 still name StrictDoc in their reasons. They hold as records of the decisions made then.
