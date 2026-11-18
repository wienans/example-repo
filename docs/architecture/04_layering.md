# Layering

This page lists the layers, what each layer may include, and the check that enforces the rule.

## Include rule

The technical diagram below answers "what may include what at build time". Each green arrow is an allowed include. Each red arrow is an include that `make lint` rejects. Run-time calls are on the [component page](03_components.md).

```mermaid
flowchart TB
  accTitle: Allowed and forbidden includes between layers
  accDescr: app may include middleware, domain and bsp. bsp may include domain and hal. The HAL port includes and implements hal and depends on the vendor library. app including hal, and domain including bsp, are forbidden and fail the lint check.
  classDef firmware fill:#90EE90,stroke:#2E7D2E,stroke-width:2px,color:darkgreen
  classDef interface fill:#87CEEB,stroke:#4682B4,stroke-width:2px,color:darkblue
  classDef platform fill:#E6E6FA,stroke:#8A2BE2,stroke-width:2px,color:darkblue
  classDef edgeCall stroke:#2E7D2E,stroke-width:2px,color:black
  classDef edgeImplements stroke:#8A2BE2,stroke-width:2px,color:black
  classDef edgeVendor stroke:#333333,stroke-width:1.5px,color:black
  classDef edgeViolation stroke:#DC143C,stroke-width:3px,color:black

  app["⚙️ app<br/>src/app"]
  mw["⚙️ middleware<br/>src/middleware"]
  bsp["⚙️ bsp<br/>src/bsp"]
  dom["⚙️ domain<br/>src/domain"]
  hal["🔌 hal<br/>src/hal/*.h"]
  port["🔧 HAL port<br/>src/hal/port/&lt;mcu&gt;"]
  vendor["🔧 MCU vendor library"]

  app e1@--> mw
  app e2@--> bsp
  app e3@--> dom
  bsp e4@--> dom
  bsp e5@--> hal
  hal ~~~ port
  port e6@-.->|"includes and implements"| hal
  port e7@-.-> vendor
  app e8@-->|"❌ rejected by make lint"| hal
  dom e9@-->|"❌ rejected by make lint"| bsp

  class app,mw,bsp,dom firmware
  class hal interface
  class port,vendor platform
  class e1,e2,e3,e4,e5 edgeCall
  class e6 edgeImplements
  class e7 edgeVendor
  class e8,e9 edgeViolation

  %% Legend: green = allowed include. Purple dashed = includes and implements. Gray dashed = vendor dependency. Red thick = forbidden include.
```

The same rule as a table:

| Layer | Directory | May include |
| --- | --- | --- |
| app | `src/app/` | app, domain, middleware, bsp |
| domain | `src/domain/` | domain |
| middleware | `src/middleware/` | middleware |
| bsp | `src/bsp/` | bsp, hal, domain |
| hal | `src/hal/*.h` | hal |
| hal port | `src/hal/port/<mcu>/` | hal, vendor headers, the C library |

Every layer may include `<stdint.h>`, `<stdbool.h>` and `<stddef.h>`.

The `bsp` layer includes `domain/motor_types.h` so that `bsp.h` speaks in rpm and mA. The dependency points inward, toward the domain, so the domain stays free of board knowledge. See [ADR-0003](../adr/0003-pure-domain-core.md).

## Enforcement

`make lint` runs `tools/check_layers.py`. The script reads every `#include` under `src/` and fails on an include that breaks the table above. It also fails on `malloc`, `calloc`, `realloc`, `free`, `float` or `double` outside `src/hal/port/`. Adding `#include "hal_pwm.h"` to `src/app/app.c` prints:

	src/app/app.c:9: layer 'app' must not include 'hal_pwm.h' from layer 'hal'

| Requirement | Check |
| --- | --- |
| [LINK: SWR-ARC-001] | `tools/check_layers.py` include table |
| [LINK: SWR-DET-001] | `tools/check_layers.py` forbidden tokens |
