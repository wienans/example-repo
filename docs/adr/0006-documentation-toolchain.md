# ADR-0006 Documentation toolchain

- Status: accepted
- Date: 2026-11-18

## Context

The repo has four kinds of documentation: requirements, architecture, design decisions and the C API. Each has its own best tool. If they drift apart, a requirement can point at a function that was renamed or deleted.

## Decision

| Content | Format | Location | Tool |
| --- | --- | --- | --- |
| Requirements | StrictDoc `.sdoc` | `docs/requirements/` | StrictDoc |
| Architecture | Markdown with Mermaid C4, sequence and state diagrams | `docs/architecture/` | StrictDoc, GitHub |
| Decisions | Markdown | `docs/adr/` | StrictDoc, GitHub |
| C API | Doxygen comments in `src/**/*.h` | `src/` | Doxygen |

The pieces connect in three places:

1. Every implementing function and every test carries a StrictDoc marker inside its Doxygen comment, for example `@relation(SWR-PI-001, scope=function)`. StrictDoc links the requirement to the code and fails `make docs` when a marker names an unknown UID. The Doxyfile defines `relation` as an alias, so Doxygen renders the marker as a "Requirement" paragraph instead of warning.
2. `tools/check_trace.py` fails `make trace` when a software requirement has no marker under `tests/` or `tools/`.
3. Markdown pages link to requirements with `[LINK: UID]`. StrictDoc resolves the tag and fails on an unknown UID.

StrictDoc's HTML bundles Mermaid, so the diagrams render offline. Doxygen 1.9 cannot render Mermaid, so Doxygen reads only `src/` and the README. The README names other docs by path instead of linking them, because Doxygen fails on a link to a file outside its input.

## Consequences

- Renaming a requirement UID without updating its markers fails `make docs`.
- Deleting the last test of a requirement fails `make trace`.
- StrictDoc warns that the old `strictdoc.toml` format is deprecated, so the project uses `strictdoc_config.py`.
- GitHub shows `[LINK: UID]` tags as plain text. The reader then looks up the UID in the requirements files.
