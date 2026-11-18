# Diagram conventions

Every Mermaid diagram in `docs/` follows the rules on this page. `make diagrams` checks the rules that a script can check, renders every diagram with Mermaid CLI, and fails the build on the first broken one.

The rules combine two published Mermaid skills. [design-doc-mermaid](https://github.com/SteveFeldman/agents-skills/tree/main/skills/mermaid) contributes the high-contrast palette, the semantic symbols, and "validate before you publish". [mastery-of-mermaid](https://github.com/flatrick/agent-skills/tree/main/mastery-of-mermaid) contributes the audience levels, the node budget, accessibility metadata, edge IDs, and the subgraph edge rule. Where the two disagree, the table in [Where the sources disagree](#where-the-sources-disagree) records the choice.

## Before you draw

Answer three questions, and write the answers into the sentence that introduces the diagram.

1. **Which reader?** An overview diagram is for someone new to the repo. It uses plain names and 6 to 10 nodes, 12 at most. A technical diagram is for someone who changes the code. It uses exact identifiers from `src/` and at most 20 nodes.
2. **Which question?** One diagram answers one question. The component view answers "what calls what at run time". The layering view answers "what may include what at build time". Neither repeats the other.
3. **Does a diagram help?** Use a sentence for a relationship of two or three items, and a table for a flat list. Draw only nodes and edges that exist in the code. Check each function name against `src/` before you draw the edge.

## Element types

Each element type has one symbol and one style class. A diagram uses only these classes.

| Element type | Symbol | Class | Fill | Text | Border | Contrast |
| --- | --- | --- | --- | --- | --- | --- |
| Person | 👤 | `person` | `#FFE4B5` | `black` | `#FF8C00` | 17.0 |
| Firmware code in this repo | ⚙️ | `firmware` | `#90EE90` | `darkgreen` | `#2E7D2E` | 5.3 |
| HAL interface header | 🔌 | `interface` | `#87CEEB` | `darkblue` | `#4682B4` | 8.8 |
| MCU-specific code: HAL port or vendor library | 🔧 | `platform` | `#E6E6FA` | `darkblue` | `#8A2BE2` | 12.4 |
| Hardware outside the MCU | 🔩 | `hardware` | `#F0F0F0` | `black` | `#333333` | 18.4 |
| Build, test or documentation tool | 🛠️ | `tooling` | `#FFD700` | `black` | `#B8860B` | 15.0 |
| Fault state or forbidden dependency | ❌ | `fault` | `#FFB6C1` | `black` | `#DC143C` | 12.7 |
| C4 boundary drawn as a subgraph | none | `boundary` | `#FFFFFF` | `black` | `#666666`, dashed | 21.0 |

The contrast column is the WCAG 2.1 ratio of the text color on the fill. `tools/check_diagrams.py` recomputes it for every `classDef` and `style` line and fails below 4.5, the AA minimum for normal text.

Copy the classes a flowchart needs from this block:

	classDef person fill:#FFE4B5,stroke:#FF8C00,stroke-width:2px,color:black
	classDef firmware fill:#90EE90,stroke:#2E7D2E,stroke-width:2px,color:darkgreen
	classDef interface fill:#87CEEB,stroke:#4682B4,stroke-width:2px,color:darkblue
	classDef platform fill:#E6E6FA,stroke:#8A2BE2,stroke-width:2px,color:darkblue
	classDef hardware fill:#F0F0F0,stroke:#333333,stroke-width:2px,color:black
	classDef tooling fill:#FFD700,stroke:#B8860B,stroke-width:2px,color:black
	classDef fault fill:#FFB6C1,stroke:#DC143C,stroke-width:2px,color:black
	classDef boundary fill:#FFFFFF,stroke:#666666,stroke-width:1px,stroke-dasharray:5 5,color:black

## Edge types

Overview diagrams leave edges unstyled. Technical flowcharts style every edge through an edge ID, such as `app e1@--> sched`, and a trailing `class e1 edgeCall` line.

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

A diagram that colors its edges ends with a `%% Legend:` comment that says what each color means.

## Labels

A node label has up to three lines:

1. The symbol and the name. The name is the code identifier when one exists, such as `motor_control`.
2. The C4 element type and technology in brackets, such as `[Component: C99]`.
3. One short sentence about what the element does.

The symbol never replaces the name. A screen reader, or a renderer without an emoji font, still gets the full label.

An edge label is a verb phrase or the name of what crosses the edge: a function, a signal, or a protocol. In the context and container views, an edge points the way data or a command flows. In the component and layering views, an edge points from the caller to the callee, or from the file that includes to the header it includes.

## Structure

- The two lines after the type keyword are `accTitle:` and `accDescr:`. They describe what the diagram shows, in words a screen reader can read aloud.
- All `classDef` lines come next, before any node or edge.
- Every subgraph has an explicit ID, as in `subgraph dom [src/domain]`.
- An edge that crosses a subgraph boundary points at the subgraph, not at a node inside it. The exception is a stack of layers, where the edge must show which node breaks or follows the rule.
- No subgraph wraps a single node.
- Quote every label: `ctl["⚙️ motor_control"]`. Quotes avoid parse errors from parentheses and from the words `end`, `o` and `x` at the start of an ID.
- `linkStyle` is not allowed. Index-based styles break when an edge is added.
- A reversed arrow such as `hal <-.- port` renders with no arrowhead. To place `port` below `hal` while the arrow points up, add an invisible link `hal ~~~ port` and draw `port -.-> hal`.

## Diagram types

| View | Mermaid type | Reader |
| --- | --- | --- |
| C4 system context | `flowchart` | Overview |
| C4 containers | `flowchart` with subgraphs | Overview |
| C4 components | `flowchart` with one subgraph per layer | Technical |
| Include rule | `flowchart` with one subgraph per layer | Technical |
| Call order in one control tick | `sequenceDiagram` with one `box` per layer | Technical |
| Motor states | `stateDiagram-v2` | Technical |

## Where the sources disagree

| Topic | design-doc-mermaid | mastery-of-mermaid | Choice here | Reason |
| --- | --- | --- | --- | --- |
| C4 notation | C4 views as `flowchart` | Native `C4Context` and friends | `flowchart` | Native C4 types cannot take `classDef`, so they cannot follow the palette |
| Palette | Light fills, dark text | Medium fills, same-hue text | Light fills, dark text | Measured: two mastery-of-mermaid roles fall below 4.5 (`queue` 3.79, `consumer` 3.91). Every design-doc-mermaid table color passes |
| Symbols | On every node | Not mentioned | One per element type, always next to the name | Keeps the meaning when the emoji does not render |
| Published form | `.mmd` plus a PNG embedded as an image | `.mmd` or a fenced block | Fenced block in the Markdown page | StrictDoc and GitHub render fenced blocks. A committed PNG drifts from its source. `make diagrams` still writes `.mmd` and `.svg` files to `build/diagrams/` |
| Edge styling | `linkStyle` in examples | Edge IDs | Edge IDs | `linkStyle` indices shift when an edge is added |

## Validate a diagram

Run `make diagrams` from the repo root. For each diagram the tool:

1. Writes the source to `build/diagrams/<file>_<nn>_<type>_<title>.mmd`.
2. Checks the type, the `accTitle` and `accDescr` lines, the `classDef` order, the contrast, `linkStyle`, reversed arrows, and the node count.
3. Renders the `.mmd` file to an `.svg` file next to it with Mermaid CLI.

Each failure prints as `file:line: message`. `make docs` runs the same check first. Open the `.svg` files to review layout, which no script checks.
