# ADR-0001 Record architecture decisions

- Status: accepted
- Date: 2026-11-18

## Context

The design choices in this repo, such as where the hardware boundary sits and why the control loop uses integers, are not visible from the code alone. A reader who ports the firmware needs to know which choices are load-bearing.

## Decision

Record each decision that shapes more than one module as an ADR in `docs/adr/`. Use the file name `NNNN-title-in-kebab-case.md` and these sections: Context, Decision, Consequences. Never edit an accepted ADR's decision. Write a new ADR that supersedes it and set the old one's status to `superseded by ADR-NNNN`.

ADRs are Markdown, so they render on GitHub and in the StrictDoc export, and they can link to requirements with `[LINK: UID]`.

## Consequences

- A change that contradicts an ADR shows up in review as a missing superseding ADR.
- The StrictDoc site lists the ADRs next to the requirements they justify.
