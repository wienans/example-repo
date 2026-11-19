---
name: mermaid-architect
description: Create, edit and validate Mermaid diagrams of every kind (flowchart, sequence, class, state, ER, C4, deployment, Gantt and 25 other types) and design documents with embedded diagrams. Use when asked to diagram, visualize, map out or document a process, system, architecture, schema, timeline, release, incident or code path, to "create a diagram", "generate mermaid", "code to diagram" or "create a design doc", or to create or update a .mmd file or a mermaid code block.
---

# Mermaid architect

Mermaid diagrams are plain text, so they diff, review and version with the code they describe. This skill picks the diagram, writes correct syntax, checks it against the code, validates it with Mermaid CLI, and styles it so every label is readable.

## Workflow

1. **Name the question and the reader.** One diagram answers one question. An overview diagram is for someone new: plain names, 6 to 10 nodes, 12 at most. A technical diagram is for someone changing the code: exact identifiers, at most 20 nodes, or split it. Unsure how much detail? Read `references/scenario-detail-levels.md` first.
2. **Pick the type** from the tables below, and open its reference before you write syntax. Do not write syntax from memory.
3. **Check every node and edge against the source.** Grep each function, service or table name before you draw it. If you cannot verify a name or a connection, say so instead of drawing it.
4. **Write the diagram** to the rules in this file.
5. **Validate.** Render it: `mmdc -i diagram.mmd -o diagram.svg`. On an error, find the cause in `references/guides/troubleshooting.md`, fix it, and render again. Then open the SVG. Exit status 0 does not prove that the styles applied or that the layout reads well. Never say a diagram renders unless you rendered it. Without `mmdc`, use `mermaid.parse()` (`references/configuration.md`), or say plainly that the diagram is unverified.
6. **Publish.** GitHub, GitLab, StrictDoc, Obsidian and most doc sites render a fenced ```` ```mermaid ```` block, so commit the block, not an image. Export an image only for a target that cannot render Mermaid, such as Confluence or slides. Use `scripts/extract_mermaid.py`, `scripts/mermaid_to_image.py` or `scripts/resilient_diagram.py`, and see `references/guides/resilient-workflow.md`.

When you present a diagram, show the file name, the code block, and either "Validated with mmdc" or "Not validated" with the reason.

## Pick the diagram type

| Need to show | Type | Read |
| --- | --- | --- |
| Process, algorithm, decision tree, workflow | Flowchart | `references/flowchart.md`, `references/guides/diagrams/activity-diagrams.md` |
| What contains what: modules, packages, layers | Flowchart with subgraphs | `references/flowchart.md`, `references/scenario-codebase.md` |
| Calls or messages over time | Sequence | `references/sequence-diagram.md`, `references/guides/diagrams/sequence-diagrams.md` |
| Lifecycle or state machine | State | `references/state-diagram.md` |
| Relationships between types: inheritance, composition | Class | `references/class-diagram.md` |
| Tables and keys | ER | `references/erd.md` |
| Software architecture: context, container, component | C4, see [C4 views](#c4-views) | `references/c4.md`, `references/guides/diagrams/architecture-diagrams.md` |
| Infrastructure, cloud, Kubernetes, CI/CD topology | Flowchart or architecture | `references/guides/diagrams/deployment-diagrams.md`, `references/architecture-diagram.md` |
| Schedule | Gantt | `references/gantt.md` |
| Chronology of events | Timeline | `references/timeline.md` |
| Branching strategy | Git graph | `references/gitgraph.md` |
| Cross-team process with step owners | Swimlanes | `references/swimlanes.md` |
| Candidate causes of a failure | Ishikawa | `references/ishikawa.md` |
| Requirements traceability | Requirement | `references/requirement-diagram.md` |

Other types each have a reference named after them in `references/`: block, packet, kanban, mindmap, pie, quadrant, radar, sankey, treemap, tree-view, user-journey, venn, wardley, xy-chart, zenuml, cynefin, event-modeling and railroad. Confirm that the target renderer supports a newer type before you put it in a canonical document. Mermaid 11.12.2, which StrictDoc 0.31 bundles, cannot render cynefin, event-modeling, ishikawa, railroad, swimlanes, tree-view, venn or wardley diagrams, or labeled points in an XY chart. Mermaid 11.17.2 renders all of them.

Grouping is not a class diagram. If the boxes would have no arrows, draw a flowchart with subgraphs or a tree view.

## Find a pattern

| You need | Read |
| --- | --- |
| Runtime behavior: request lifecycles, retries, caching, sagas, backpressure | `references/scenario-runtime.md` |
| Codebase structure: dependency rules, call paths, ownership, test levels | `references/scenario-codebase.md` |
| Delivery: branching, environment promotion, canary, migrations | `references/scenario-delivery.md` |
| Operations: incident timelines, triage, escalation, postmortems | `references/scenario-operations.md` |
| Generic templates: auth flows, ER shapes, state machines | `references/common-patterns.md` |
| Diagrams from source code | `references/guides/code-to-diagram/README.md`, then `examples/<framework>/README.md` for Spring Boot, FastAPI, React, Express, Java servlets or Python ETL |
| A whole design document | `assets/<kind>-design-template.md` for architecture, API, feature, database or system design |

## Rules for every diagram

### Structure

- Put `accTitle:` and `accDescr:` on the two lines right after the type keyword. Describe what the diagram shows, in words a screen reader can read aloud.
- Declare every `classDef` before the first node or edge.
- Give every subgraph an explicit ID that no node uses: `subgraph api [API tier]`.
- Point an edge that crosses a subgraph boundary at the subgraph. Point at a node inside only when the subgraph is one stage of a straight pipeline, or when the node it reaches is the point of the diagram. Never point at a node inside a subgraph that sets its own `direction`. See `references/style-standard.md`.
- Do not wrap a single node in a subgraph, unless it is one band in a row of phase bands.
- Quote a label that contains `(`, `)`, `[`, `]` or `"`: `db["get_db()"]`. Inside quotes, write a double quote as `#quot;`.
- Never use `end` as a node ID. Quoting it does not help. Use another ID and put the word in the label: `endNode[end]`.
- Put a space between an arrow and an ID that starts with `o` or `x`. `A---ops` parses as a circle edge to `ps`.
- Put a `%%` comment on its own line. A comment after a node on the same line is a parse error.
- Draw one link per line when edges carry styles. Style them with edge IDs, `A e1@--> B` and then `class e1 edgeName`. Use `linkStyle` only for renderers older than Mermaid 11.6.
- A reversed arrow such as `B <-.- A` renders with no arrowhead. To rank `A` below `B` while the arrow points up, add `B ~~~ A` and draw `A -.-> B`.

### Color

- Every `classDef` or `style` that sets `fill` also sets `color`, with a WCAG contrast of at least 4.5 between them. Measure, do not judge by eye. White text on a mid-tone fill fails: `#fff` on `#4ECDC4` is 1.93.
- Use the role palette in `references/style-standard.md` for technical flowcharts (producer, queue, consumer, external, client, standalone, service). Its `queue` and `consumer` text colors were darkened to pass 4.5.
- The way a class is assigned differs between flowchart, class and state diagrams, and two of the wrong forms fail silently. Check the matrix in `references/style-standard.md` before you copy a style line between types.
- When colors or arrow shapes carry meaning, end the diagram with a `%% Legend:` comment.

Use this palette for status:

| State | Fill | Text | Border | Contrast |
| --- | --- | --- | --- | --- |
| Normal | `#F0F0F0` | `black` | `#333333` | 18.4 |
| Success | `#90EE90` | `darkgreen` | `#2E7D2E` | 5.3 |
| Warning | `#FFD700` | `black` | `#B8860B` | 15.0 |
| Error | `#FFB6C1` | `black` | `#DC143C` | 12.7 |
| Info | `#87CEEB` | `darkblue` | `#4682B4` | 8.8 |
| Public | `#FFE4B5` | `black` | `#FF8C00` | 17.0 |
| Private | `#E6E6FA` | `darkblue` | `#8A2BE2` | 12.4 |
| Dark | `#2C3E50` | `white` | `#34495E` | 11.0 |

### Symbols

A Unicode symbol is optional. If you use symbols, give each element type exactly one, use it the same way in every diagram of the document, and always put it next to the name, never instead of it. A reader without an emoji font, or a screen reader, must still get the full label. See `references/guides/unicode-symbols/guide.md`.

### Placement

Put one sentence before each diagram that says what it shows and for which reader. A diagram does not replace prose that explains non-obvious behavior. Change a diagram in the same commit as the behavior it documents.

## C4 views

- Start with native `C4Context` for the system context and `C4Container` for containers. Follow `references/c4.md`. Draw a component view only when it answers a question a developer has.
- Render the native diagram and look at it. Mermaid's C4 layout cannot be configured. When it drops or overlaps a relationship, which happens with two relations between the same pair of elements, or when it must show something that is not software, redraw the view as a flowchart. Keep the C4 element type in each label, such as `[Container: Linux executable]`, and draw each boundary as a dashed subgraph.
- Native C4 output differs between Mermaid versions. Check the view in the version that your target renderer bundles.
- A container is a separately deployable unit. Libraries, source sets and plug-in modules are not containers. They belong on the component view or in a container's description.

## When not to draw

Write prose or a table instead when:

- The relationship has two or three items.
- The content is a flat list, a set of values or a comparison.
- You cannot verify the entities or the connections. A plausible diagram reads as authoritative.
- The reader will copy a sequence of commands. Use a code block.

## Check this skill

`scripts/check_examples.py` renders every ```` ```mermaid ```` example in this folder with Mermaid CLI and measures every `classDef` contrast. Run it after you edit any reference:

	MMDC=/path/to/mmdc python3 scripts/check_examples.py

Put a deliberately broken example in a ```` ```text ```` block, so that neither the check nor a Markdown renderer tries to draw it. `PROVENANCE.md` records where each part of this skill came from.
