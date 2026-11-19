# Provenance

This skill merges two published Mermaid skills. Git history keeps the unmodified upstream copy in the commit "chore(skills): add mermaid-architect skill as published upstream".

## Sources

| Part | Source | Revision | License |
| --- | --- | --- | --- |
| `assets/`, `examples/`, `references/guides/`, `references/mermaid-diagram-guide.md`, `scripts/extract_mermaid.py`, `scripts/mermaid_to_image.py`, `scripts/resilient_diagram.py` | `skills/mermaid` in [SteveFeldman/agents-skills](https://github.com/SteveFeldman/agents-skills), a copy of [SpillwaveSolutions/design-doc-mermaid](https://github.com/SpillwaveSolutions/design-doc-mermaid) | `b0dfd0c077f5bf6c224bcafdff45c9c112c6e932` | The upstream README says "MIT License". Neither repository has a LICENSE file or names a copyright holder |
| Every other file in `references/` | `mastery-of-mermaid/references` in [flatrick/agent-skills](https://github.com/flatrick/agent-skills) | `eef829bfb3a5100b109eea07b5038a653741df18` | None stated. Default copyright applies, so redistribution outside this private repository is not granted |
| `SKILL.md`, `PROVENANCE.md`, `scripts/check_examples.py` | Written for this repository | | Same as this repository |

Clear both licenses with their authors before this repository, or this skill, is made public.

## Changes to the upstream files

- `SKILL.md` is rewritten. It keeps the design-doc-mermaid guides, examples, templates, scripts and high-contrast status palette. It takes the workflow, audience levels, node budget, structure rules, C4 guidance and "when not to draw" list from mastery-of-mermaid. The frontmatter `name` now matches the folder name.
- `README.md` and `HIGH_CONTRAST_UPDATE.md` are deleted. They held marketplace install steps and a release note. The palette from the release note is in `SKILL.md`.
- mastery-of-mermaid references are copied flat into `references/`. The `<img src="rendered/...">` lines and `mermaid-render` comments are removed, because the pre-rendered SVGs are not copied. The Mermaid source of every example is unchanged.
- Text colors that fell below a WCAG contrast of 4.5 are darkened. The fill and stroke are kept. This covers 35 classes in the design-doc-mermaid guides and the mastery-of-mermaid `queue` (`#bf360c` to `#8f2a09`) and `consumer` (`#1b5e20` to `#104713`) roles.
- Deliberately invalid examples moved from ```` ```mermaid ```` to ```` ```text ```` blocks: 19 in `references/guides/troubleshooting.md`, 1 in `references/guides/resilient-workflow.md` and 1 in `references/mermaid-diagram-guide.md`.
- Broken examples are fixed: 3 "Correct" fixes in `troubleshooting.md` that did not parse, 9 example diagrams with unquoted labels, a label typo or sequence-diagram `classDef` lines, a subgraph that shared its ID with a node, an undeclared class annotation, 5 inline `%%` comments, and 2 mastery-of-mermaid styling examples that set no text color.
- The `linkStyle` example in `references/mermaid-diagram-guide.md` now uses edge IDs.
- 25 relative links that pointed one directory level wrong are fixed, in `references/guides/code-to-diagram/README.md`, `examples/README.md` and `examples/java-webapp/README.md`.

## Check results

`scripts/check_examples.py` renders every Mermaid example and measures every class contrast.

| Revision | Examples passing |
| --- | --- |
| Upstream design-doc-mermaid, before the merge | 240 of 304 |
| This skill, Mermaid 11.17.2 | 421 of 421 |
| This skill, Mermaid 11.12.2, the version StrictDoc 0.31 bundles | 399 of 421. The 22 failures use diagram types or features added after 11.12: cynefin, event-modeling, ishikawa, railroad, swimlanes, tree-view, venn, wardley and labeled XY-chart points |
