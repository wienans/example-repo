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

The pieces connect in four places:

1. Every implementing function and every test carries a StrictDoc marker inside its Doxygen comment, for example `@relation(SWR-PI-001, scope=function, role=Implementation)`. The role is `Implementation` in `src/`, `Test` in `tests/` and `Check` in `tools/`, so the StrictDoc traceability screen shows which links implement a requirement and which verify it. StrictDoc links the requirement to the code and fails `make docs` when a marker names an unknown UID. The Doxyfile defines `relation` as an alias, so Doxygen renders the marker as a "Requirement" paragraph instead of warning.
2. `tools/check_trace.py` fails `make trace` when a software requirement has no passing `Test` and no `Check`, when it has no `Implementation` marker, or when a marker carries the wrong role for its directory. A requirement verified by a `Check` needs no `Implementation` marker, because it constrains every source file rather than one function. A `Test` marker counts only when the `test_*` function below it passed: Ceedling's `report_tests_log_factory` plugin writes a JUnit report, `make trace` runs `make test` first, and the script rejects a report older than `src/`, `tests/` or `project.yml`.
3. Markdown pages link to requirements with `[LINK: UID]`. StrictDoc resolves the tag and fails on an unknown UID.
4. `tools/check_diagrams.py` checks every Mermaid diagram against `docs/architecture/00_diagram_conventions.md` and renders it with Mermaid CLI. `make docs` runs it first, so a diagram that does not render never reaches the StrictDoc site.

StrictDoc's HTML bundles Mermaid, so the diagrams render offline. Doxygen renders Mermaid since 1.17, but the diagrams already have one home in the StrictDoc site, so Doxygen reads only `src/` and the README. The README names other docs by path instead of linking them, because Doxygen fails on a link to a file outside its input.

## Consequences

- Renaming a requirement UID without updating its markers fails `make docs`.
- Deleting the last test of a requirement fails `make trace`. So does deleting the last function that implements it, or ignoring or breaking every test that names it.
- `make trace` takes as long as `make test`, because it needs fresh results.
- StrictDoc warns that the old `strictdoc.toml` format is deprecated, so the project uses `strictdoc_config.py`.
- GitHub shows `[LINK: UID]` tags as plain text. The reader then looks up the UID in the requirements files.
