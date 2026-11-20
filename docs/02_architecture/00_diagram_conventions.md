# Diagram conventions

Every Mermaid diagram in `docs/` follows the rules on this page. `make diagrams` checks the rules that a script can check, renders every diagram with Mermaid CLI, and fails on the first broken one.

The rules come from the `mermaid-architect` skill in `.agents/skills/mermaid-architect/`. This page records only what the repo adds to the skill or decides differently. [Where this repo departs from the skill](#where-this-repo-departs-from-the-skill) lists the differences.

## Before you draw

Answer three questions, and write the answers into the sentence that introduces the diagram.

1. **Which reader?** An overview diagram is for someone new to the repo. It uses plain names and 6 to 10 nodes, 12 at most. A technical diagram is for someone who changes the code. It uses exact identifiers from `src/` and at most 20 nodes.
2. **Which question?** One diagram answers one question. The component view answers "what calls what". The layering view answers "what may include what". Neither repeats the other.
3. **Does a diagram help?** Use a sentence for a relationship between two or three items, and a table for a flat list. Draw only the nodes and edges that exist in the code. Grep each function name in `src/` before you draw its edge.

## Element types

Each element type has one symbol and one style class. A flowchart uses only these classes.

| Element type | Symbol | Class | Fill | Text | Border | Contrast |
| --- | --- | --- | --- | --- | --- | --- |
| Person | 👤 | `person` | `#FFE4B5` | `black` | `#FF8C00` | 17.0 |
| Firmware code in this repo | ⚙️ | `firmware` | `#90EE90` | `darkgreen` | `#2E7D2E` | 5.3 |
| HAL interface header | 🔌 | `interface` | `#87CEEB` | `darkblue` | `#4682B4` | 8.8 |
| MCU-specific code: a HAL port or a vendor library | 🔧 | `platform` | `#E6E6FA` | `darkblue` | `#8A2BE2` | 12.4 |
| Hardware outside the MCU | 🔩 | `hardware` | `#F0F0F0` | `black` | `#333333` | 18.4 |
| Build, test or documentation tool | 🛠️ | `tooling` | `#FFD700` | `black` | `#B8860B` | 15.0 |
| Fault state or forbidden dependency | ❌ | `fault` | `#FFB6C1` | `black` | `#DC143C` | 12.7 |
| C4 boundary drawn as a subgraph | none | `boundary` | `#FFFFFF` | `black` | `#666666`, dashed | 21.0 |

The fills are the status palette from the skill. The contrast column is the WCAG 2.1 ratio of the text color on the fill. `tools/check_diagrams.py` recomputes it for every `classDef` and `style` line and fails below 4.5, the AA minimum for normal text.

Copy the classes that a flowchart needs from this block:

	classDef person fill:#FFE4B5,stroke:#FF8C00,stroke-width:2px,color:black
	classDef firmware fill:#90EE90,stroke:#2E7D2E,stroke-width:2px,color:darkgreen
	classDef interface fill:#87CEEB,stroke:#4682B4,stroke-width:2px,color:darkblue
	classDef platform fill:#E6E6FA,stroke:#8A2BE2,stroke-width:2px,color:darkblue
	classDef hardware fill:#F0F0F0,stroke:#333333,stroke-width:2px,color:black
	classDef tooling fill:#FFD700,stroke:#B8860B,stroke-width:2px,color:black
	classDef fault fill:#FFB6C1,stroke:#DC143C,stroke-width:2px,color:black
	classDef boundary fill:#FFFFFF,stroke:#666666,stroke-width:1px,stroke-dasharray:5 5,color:black

A sequence diagram cannot use classes. It groups participants in one `box` per layer: `rgb(232,248,232)` for firmware layers and `rgb(240,240,250)` for the HAL port. Both are lighter tints of the `firmware` and `platform` fills.

## Edge types

Overview diagrams leave edges unstyled. A technical flowchart styles every edge through an edge ID, such as `app e1@--> sched`, and a `class e1 edgeCall` line after the last edge.

| Edge class | Arrow | Stroke | Meaning |
| --- | --- | --- | --- |
| `edgeCall` | `-->` | `#2E7D2E`, 2px | Calls a function, or may include a header |
| `edgeImplements` | `-.->` | `#8A2BE2`, 2px | Defines the functions that a header declares |
| `edgeVendor` | `-.->` | `#333333`, 1.5px | Depends on code outside this repo |
| `edgeViolation` | `-->` | `#DC143C`, 3px | An include that `make lint` rejects |

	classDef edgeCall stroke:#2E7D2E,stroke-width:2px,color:black
	classDef edgeImplements stroke:#8A2BE2,stroke-width:2px,color:black
	classDef edgeVendor stroke:#333333,stroke-width:1.5px,color:black
	classDef edgeViolation stroke:#DC143C,stroke-width:3px,color:black

An edge class has no fill. The check measures its label color against `#e8e8e8`, the edge label background of the default theme.

A diagram that colors its edges ends with a `%% Legend:` comment that says what each color means.

## Labels

A node label has up to three lines:

1. The symbol and the name. The name is the code identifier when one exists, such as `motor_control`.
2. The C4 element type and the technology in brackets, such as `[Component: C99]`.
3. One short sentence about what the element does.

The symbol never replaces the name. A screen reader, or a renderer without an emoji font, still gets the full label.

An edge label is a verb phrase, or the name of what crosses the edge: a function, a signal, or a protocol. In the context and container views, an edge points the way that data or a command travels. In the component and layering views, an edge points from the caller to the callee, or from the including file to the header it includes.

## Structure

- The two lines after the type keyword are `accTitle:` and `accDescr:`. They describe what the diagram shows, in words that a screen reader can read aloud.
- All `classDef` lines come next, before any node or edge.
- Every subgraph has an explicit ID, as in `subgraph domL [src/domain]`.
- An edge that crosses a subgraph boundary points at the subgraph, not at a node inside it. The exception is a view whose point is which node an edge reaches, such as the component view.
- No subgraph wraps a single node.
- A C4 container is a separately deployable unit, such as an executable. Source sets, libraries and HAL ports are not containers. They appear on the component view or in a container's description.
- Quote every label: `ctl["⚙️ motor_control"]`. Quotes prevent parse errors from parentheses and from IDs that start with `o` or `x`.
- Never use `end` as a node ID. Quotes do not help.
- Never use `linkStyle`. Index-based styles break when someone adds an edge.
- A reversed arrow such as `hal <-.- port` renders with no arrowhead. To place `port` below `hal` while the arrow points up, add the invisible link `hal ~~~ port` and draw `port -.-> hal`.

## Diagram types

| Page | View | Mermaid type | Reader |
| --- | --- | --- | --- |
| [System context](01_system_context.md) | C4 system context | `flowchart` | Overview |
| [Containers](02_containers.md) | C4 containers | `flowchart` with one boundary subgraph | Overview |
| [Components](03_components.md) | C4 components | `flowchart` with one subgraph per layer | Technical |
| [Layering](04_layering.md) | Include rule | `flowchart` | Technical |
| [Runtime](05_runtime.md) | Calls in one pass of the main loop | `sequenceDiagram` with one `box` per layer | Technical |
| [Runtime](05_runtime.md) | Motor states | `stateDiagram-v2` | Technical |
| [Runtime](05_runtime.md) | How the host port advances time | `sequenceDiagram` | Technical |

`tools/check_diagrams.py` accepts only `flowchart`, `sequenceDiagram` and `stateDiagram-v2`.

## Where this repo departs from the skill

| Topic | Skill | This repo | Reason |
| --- | --- | --- | --- |
| C4 notation | Native `C4Context` and `C4Container` first, a flowchart when native C4 drops a relationship | Always a `flowchart` | Native C4 dropped the firmware-to-power-stage relation and labeled hardware as software. See [ADR-0007](../adr/0007-c4-views-as-flowcharts.md) |
| Quoting | Quote a label that contains `(`, `)`, `[`, `]` or `"` | Quote every label | One rule is easier to review than a list of characters |
| Symbols | Optional | Required, one per element type | Every diagram here mixes firmware, platform code and hardware. The symbol carries that difference when the colors do not print |
| `linkStyle` | Allowed for renderers older than Mermaid 11.6 | Never | Mermaid CLI 11.17 renders every diagram, and it supports edge IDs |
| Published form | A fenced block. An image only for targets that cannot render Mermaid | A fenced block. `make diagrams` also writes `.mmd` and `.svg` files to `build/diagrams/` for review | Sphinx renders fenced blocks through Mermaid CLI, and GitHub renders them itself. A committed image drifts from its source |

## Validate a diagram

Run `make diagrams` from the repo root. For each diagram, the tool:

1. Writes the source to `build/diagrams/<file>_<nn>_<type>_<heading>.mmd`.
2. Checks the type, the `accTitle` and `accDescr` lines, the `classDef` order, the contrast, `linkStyle`, reversed arrows, and the flowchart node count.
3. Renders the `.mmd` file to an `.svg` file next to it with Mermaid CLI.

Each failure prints as `file:line: message`. `make docs` runs the same check first.

No script checks the layout. Open each `.svg` file and confirm that every edge and label is visible. `make docs` renders the diagrams with the same Mermaid CLI, so the site shows what the `.svg` files show.
