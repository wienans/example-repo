# ADR-0007 Draw C4 views as flowcharts

- Status: accepted
- Date: 2026-11-18

## Context

The architecture pages show the C4 system context, container and component views. Mermaid offers native `C4Context`, `C4Container` and `C4Component` types. The two skills behind [Diagram conventions](../architecture/00_diagram_conventions.md) disagree on them:

- mastery-of-mermaid makes native `C4Context` its default for the overview level. It names a plain flowchart as the fallback "when Mermaid's C4 layout drops a relationship label across a box".
- design-doc-mermaid draws every C4 view as a `flowchart` with subgraphs.

Native C4 can follow the palette through `UpdateElementStyle`, so color does not decide the question. To decide it, we drew the context and container views both ways and rendered each with Mermaid 11.12.2, the version StrictDoc 0.31 bundles, and with Mermaid 11.17.2 from Mermaid CLI.

## Findings

| Check | Native C4 | Flowchart |
| --- | --- | --- |
| Firmware sends commands to the power stage and reads current back | `Rel` plus `Rel` draws both arrows with overlapping labels. `Rel` plus `Rel_Back` drops the command arrow in both versions | Both arrows and labels drawn |
| Power stage and encoder shown as hardware | Shown as `[Software System]` in 11.17 and `<<external_system>>` in 11.12. `System_Ext` has no parameter for a custom type | `[Hardware]` |
| Label text `src/hal/port/<mcu>` | 11.17 drops `<mcu>` | Drawn in both versions |
| Relation label near a boundary | "Drives" overlaps the `example-repo` boundary title in both versions | No overlap |
| Same source in 11.12 and 11.17 | Different shapes, type labels and rows per line | Same layout |
| Accessibility metadata | `accTitle` and `accDescr` parse | `accTitle` and `accDescr` parse |

The first finding is the fallback condition that mastery-of-mermaid names. A context diagram that loses the firmware's only output is wrong, not merely untidy. `UpdateRelStyle` offsets can move one label, but the offsets are pixel values, and the two Mermaid versions place the boxes differently.

## Decision

Draw all three C4 views as `flowchart` diagrams. Keep the C4 vocabulary in the labels: each node states its C4 element type, such as `[Container: Linux executable]`, and each boundary is a dashed `boundary` subgraph. `tools/check_diagrams.py` rejects native C4 types, so a new diagram cannot fall back to them by accident.

Keep the C4 modelling rules from mastery-of-mermaid. A container is a separately deployable unit. Source sets, libraries and HAL ports are not containers, so the container view shows only the three executables.

## Consequences

- The diagrams render the same in StrictDoc, in Mermaid CLI, and in any renderer from Mermaid 11.6 on, which is the first version with edge IDs.
- Flowcharts have no person shape. A person is a `person`-class node with the 👤 symbol.
- Revisit this ADR when StrictDoc bundles a Mermaid version whose C4 renderer keeps both relations between one pair of elements. To recheck, draw the context view in `C4Context` and render it with that version.
