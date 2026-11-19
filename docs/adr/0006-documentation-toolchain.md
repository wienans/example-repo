# ADR-0006 Documentation toolchain

- Status: accepted
- Date: 2026-11-18

## Context

The repo has four kinds of documentation: requirements, architecture, design decisions and the C API. Each has its own best tool. If they drift apart, a requirement can point at a function that was renamed or deleted.

## Decision

| Content | Format | Location | Tool |
| --- | --- | --- | --- |
| Requirements | StrictDoc `.sdoc` | `docs/requirements/` | StrictDoc |
| Architecture | Markdown with Mermaid flowcharts for the C4 views, plus sequence and state diagrams | `docs/architecture/` | StrictDoc, GitHub |
| Decisions | Markdown | `docs/adr/` | StrictDoc, GitHub |
| C API | Doxygen comments in `src/**/*.h` | `src/` | Doxygen |
| Test results | Generated `.sdoc` from Ceedling's JUnit report | `build/test_results/` | `tools/test_results_to_sdoc.py`, StrictDoc |
| Coverage | Generated `.sdoc` from gcovr's JSON, plus gcovr's HTML | `build/coverage/` | `tools/coverage_to_sdoc.py`, gcovr, StrictDoc |

The pieces connect in six places:

1. Every implementing function and every test carries a StrictDoc marker inside its Doxygen comment, for example `@relation(SWR-PI-001, scope=function, role=Implementation)`. The role is `Implementation` in `src/`, `Test` in `tests/` and `Check` in `tools/`, so the StrictDoc traceability screen shows which links implement a requirement and which verify it. StrictDoc links the requirement to the code and fails `make docs` when a marker names an unknown UID. The Doxyfile defines `relation` as an alias, so Doxygen renders the marker as a "Requirement" paragraph instead of warning. When only part of a function implements a requirement, a `scope=line` marker names one code line and `scope=range_start` / `scope=range_end` name several. StrictDoc checks the role of a line marker against the requirement's grammar, so `docs/requirements/software/software_requirements.sgra` declares the three roles and every domain document imports it. `tools/source_markers.py` reads the markers for all tools the way StrictDoc's C reader does, so a marker StrictDoc ignores, such as one in a one-line `/* */` comment, fails `make trace` instead of counting.
2. `tools/check_trace.py` fails `make trace` when a software requirement has no passing `Test` and no `Check`, when it has no `Implementation` marker, or when a marker carries the wrong role for its directory. A requirement verified by a `Check` needs no `Implementation` marker, because it constrains every source file rather than one function. A `Test` marker counts only when the `test_*` function below it passed: Ceedling's `report_tests_log_factory` plugin writes a JUnit report, `make trace` runs `make test` first, and the script rejects a report older than `src/`, `tests/` or `project.yml`.
3. Markdown pages link to requirements with `[LINK: UID]`. StrictDoc resolves the tag and fails on an unknown UID.
4. `make docs` runs the unit tests once under gcov, and `tools/test_results_to_sdoc.py` turns the JUnit report into a Test results document: one section per test file with a summary table, one result per test with its status, linked to the test function and, with the role "verifies", to each requirement its marker names. The result UID ends in its status, and `tools/strictdoc/site.css` colours on it, so each requirement lists its tests in green, amber or red. A failing test does not stop `make docs`; `make trace` is the gate.
5. `tools/coverage_to_sdoc.py` turns gcovr's JSON into a Code coverage document: per requirement, the line and branch coverage of the code its `Implementation` markers name, and per file and function the same with links to the uncovered lines in gcovr's HTML, which `make docs` publishes next to the page. A line inside a line or range marker counts only for that marker's requirements.
6. `tools/check_diagrams.py` checks every Mermaid diagram against `docs/architecture/00_diagram_conventions.md` and renders it with Mermaid CLI. `make docs` runs it first, so a diagram that does not render never reaches the StrictDoc site.

StrictDoc's own JUnit import does not fit Ceedling: each of its dialects resolves a test name to a Google Test macro, a Python file or a Rust path, never to a C function, and on a requirement page it shows neither status nor skipped tests. Its own `*.gcov.json` import only marks a function covered once it ran and never reaches a requirement. Hence the two generated documents. StrictDoc skips every path in `.gitignore`, so `make docs` passes them to `strictdoc export` as input paths of their own.

StrictDoc's HTML bundles Mermaid, so the diagrams render offline. Doxygen renders Mermaid since 1.17, but the diagrams already have one home in the StrictDoc site, so Doxygen reads only `src/` and the README. The README names other docs by path instead of linking them, because Doxygen fails on a link to a file outside its input.

## Consequences

- Renaming a requirement UID without updating its markers fails `make docs`.
- Deleting the last test of a requirement fails `make trace`. So does deleting the last function that implements it, or ignoring or breaking every test that names it.
- `make trace` takes as long as `make test`, because it needs fresh results.
- `make docs` runs the test suite under gcov and rebuilds the site from scratch, because StrictDoc only rewrites a page whose own inputs changed.
- Coverage is that of the whole suite, not of the tests that verify a requirement. Code can count as covered because a test of another requirement runs through it.
- A test result UID changes with its status. Nothing links to these UIDs by hand.
- StrictDoc warns that the old `strictdoc.toml` format is deprecated, so the project uses `strictdoc_config.py`.
- GitHub shows `[LINK: UID]` tags as plain text. The reader then looks up the UID in the requirements files.
