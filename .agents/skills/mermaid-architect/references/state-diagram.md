# State diagram

**Use for:** state machines, record lifecycles,
status transitions (`stateDiagram-v2` is the current, actively-developed syntax;
prefer it over the legacy `stateDiagram`).
**Avoid for:** continuous polling loops (use a sequence diagram) or a process where "who does this step" matters more than which state something is in (use `swimlanes.md`).

## Core syntax

```mermaid
stateDiagram-v2
    [*] --> Still
    Still --> [*]
    Still --> Moving
    Moving --> Still
    Moving --> Crash
    Crash --> [*]
```

`[*]` is the special start/end pseudostate;
the direction of the arrow to/from it determines whether it's a start or an end.
A transition can carry a label: `s1 --> s2 : A transition`.
A state gets a description either via `state "Description" as s2` or `s2 : Description`.

## Composite (nested) states

```mermaid
stateDiagram-v2
    [*] --> First
    state First {
        [*] --> second
        second --> [*]
    }
    [*] --> NamedComposite
    NamedComposite: Another Composite
    state NamedComposite {
        [*] --> namedSimple
        namedSimple --> [*]
    }
```

Nesting can go arbitrarily deep.
Transitions between composite states are allowed at the outer level;
transitions between internal states of *different* composite states are not.

## Choice, fork, join

```mermaid
stateDiagram-v2
    state if_state <<choice>>
    [*] --> IsPositive
    IsPositive --> if_state
    if_state --> False: if n < 0
    if_state --> True : if n >= 0

    state fork_state <<fork>>
    [*] --> fork_state
    fork_state --> State2
    fork_state --> State3
    state join_state <<join>>
    State2 --> join_state
    State3 --> join_state
    join_state --> State4
```

## Concurrency

Within a composite state, separate parallel regions with `--`:

```mermaid
stateDiagram-v2
    [*] --> Active
    state Active {
        [*] --> NumLockOff
        NumLockOff --> NumLockOn : EvNumLockPressed
        --
        [*] --> CapsLockOff
        CapsLockOff --> CapsLockOn : EvCapsLockPressed
    }
```

## Notes, direction, comments

```mermaid
stateDiagram-v2
    direction LR
    State1: The state with a note
    note right of State1
        Important information
    end note
    State1 --> State2
    note left of State2 : Shorter note form
    %% this is a comment
```

`direction` (`TB`/`LR`/etc.) sets layout,
including per-composite-state via a nested `direction` line.

## Styling

```mermaid
stateDiagram-v2
    classDef movement font-style:italic
    classDef badBadEvent fill:#f00,color:black,font-weight:bold

    [*] --> Still
    Still --> Moving
    Moving --> Crash

    class Moving, Crash movement
    Crash:::badBadEvent
```

Two ways to apply a `classDef`: the `class` statement (works for start/end states too),
or the `:::` shorthand at the point of use.
**Limitation:** `classDef` styling cannot be applied to or within composite states themselves.

## Common pitfalls

- Spaces in a state's name require defining it with a bare id first (`stateId: Description with spaces`),
  then referencing the id.
- Transitions can't cross between internal states of two different composite states;
  route the transition through the composite states themselves.
- The legacy `stateDiagram` (without `-v2`) still works but has fewer features;
  use `stateDiagram-v2` for new diagrams.
- **Styling rules here are not the class-diagram rules.**
  `class Idle hot` and `class Idle,Busy hot` both work in `stateDiagram-v2`, and both are wrong in a `classDiagram`.
  The reverse trap also exists: `state Idle:::hot` on its own line parses and silently applies nothing, while `[*] --> Idle:::hot` inside a transition works.
  See the per-type matrix in `style-standard.md`.
- **A note must name a defined state, never a transition label.**
  `note right of Foo` where `Foo` is the text after a transition's `:` parses cleanly and then dies at layout with `Error: No such shape: undefined`,
  which names neither the note nor the offending target.
  Check that every note target also appears on the left or right of a `-->`.
- **Inside a composite state's body, never reference the composite's own alias, as either source or target.**
  Both `state "Proposed" as P { P --> design }` and `state "Proposed" as P { design --> P }` fail with
  `Error: Setting P as parent of P would create a cycle` (verified on mermaid-cli 11.16), because `P` is being parented inside its own body.
  Use the internal start/end pseudostate instead (`[*] --> design`, `design --> [*]`),
  and put any transition into or out of the composite state as a whole at the outer level, outside the `{ }`.

## Common patterns

See `common-patterns.md` for order-lifecycle and user-account-state templates.
