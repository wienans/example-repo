# Entity relationship diagram (ERD)

**Use for:** database schemas, table relationships, data modeling,
both abstract logical models and physical relational-table models.
**Avoid for:** non-database flows or a non-technical audience (use a birds-eye flowchart).

## Core syntax

```mermaid
erDiagram
    CUSTOMER ||--o{ ORDER : places
    CUSTOMER {
        int id PK
        string email UK
        string name
        datetime created_at
    }
    ORDER ||--|{ LINE_ITEM : contains
    ORDER {
        int id PK
        int customer_id FK
        decimal total
    }
```

Only the first entity in a statement is mandatory,
letting you declare a bare entity (`CUSTOMER`) with no relationship, useful while iterating.
Entity names conventionally use UPPERCASE and singular nouns (`CUSTOMER` not `CUSTOMERS`).

## Cardinality

Each side of a relationship has an outer character (maximum) and inner character (minimum):

| Left | Right | Meaning |
|---|---|---|
| `\|o` | `o\|` | Zero or one |
| `\|\|` | `\|\|` | Exactly one |
| `}o` | `o{` | Zero or more |
| `}\|` | `\|{` | One or more |

Combine for the common cases: `||--o{` (one-to-many), `||--||` (one-to-one),
`}o--o{` (many-to-many).
English aliases also work (`CAR 1 to zero or more NAMED-DRIVER : allows`).

Line style carries meaning too:
`--` (solid) is an *identifying* relationship (the child can't exist without the parent);
`..` (dashed) is *non-identifying* (both can exist independently).

## Attributes and keys

```mermaid
erDiagram
    PRODUCT {
        uuid id PK
        string sku UK "NOT NULL"
        decimal price "NOT NULL"
        uuid category_id FK
        string(99) name "max 99 chars"
    }
```

Attribute format is `type name [key] ["comment"]`.
Keys: `PK` (primary), `FK` (foreign), `UK` (unique); combine with a comma (`PK, FK`).
A trailing quoted string is a free-form comment/constraint note.
Optional/nullable types can end in `?` (`string? middleName`, v11.16+).

## Aliases, unicode, markdown

```mermaid
erDiagram
    p[Person] {
        string firstName
    }
    a["Customer Account"] {
        string email
    }
    p ||--o| a : has
```

Square-bracket aliases display a friendlier name than the internal identifier.
Entity names, relationships,
and attributes support unicode and basic markdown formatting when quoted.

## Direction and styling

```mermaid
erDiagram
    direction LR
    classDef core fill:#90caf9,stroke:#1565c0,color:#0d47a1

    CUSTOMER ||--o{ ADDRESS : "ships to"
    CUSTOMER:::core
```

`direction` sets `TB`/`BT`/`LR`/`RL`.
`style`/`classDef`/`class`/`:::` styling works the same as in flowcharts,
applied inline with `ENTITY:::className` or afterwards with `class ENTITY className`.

**Subgraphs do not work in `erDiagram`.**
On mermaid-cli 11.16 the parser treats `subgraph`, the quoted group title, and `end` as three more entity names,
and draws each as its own empty entity box.
There is no error and the exit code is 0, so this only shows up if you look at the picture.
To show grouping, draw the groups in a `flowchart` alongside the ERD, or split the entities across separate diagrams.

## Common pitfalls

- Omit FK attributes in a purely logical model (relationship lines already convey the association);
  include them in a model meant to mirror physical tables.
- Junction/many-to-many relationships are clearer modeled explicitly with a join entity (see `common-patterns.md`) than left as a bare `}o--o{`.
- Match attribute types to the real database's types, not generic placeholders,
  when documenting an actual schema.

## Common patterns

See `common-patterns.md` for self-referencing (hierarchical), junction-table, polymorphic,
soft-delete, and audit-trail ER shapes.
