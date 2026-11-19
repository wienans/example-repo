# Layering

This page lists the layers, what each layer may include, and the check that enforces the rule.

## Include rule

The technical diagram below answers "what may include what at build time". Each green arrow is an allowed include. Each red arrow is an example of an include that `make lint` rejects. Calls between components are on the [component page](03_components.md).

```mermaid
flowchart TB
  accTitle: Allowed and forbidden includes between layers
  accDescr: app may include middleware, domain and bsp. bsp may include domain and hal. The HAL port includes and implements hal, and depends on the vendor library. app including hal, and domain including bsp, are two examples of includes that fail the lint check.
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
  vendor["🔧 Vendor library"]

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

The table below states the same rule. It mirrors `ALLOWED` in `tools/check_layers.py`.

| Layer | Directory | May include |
| --- | --- | --- |
| app | `src/app/` | app, domain, middleware, bsp |
| domain | `src/domain/` | domain |
| middleware | `src/middleware/` | middleware |
| bsp | `src/bsp/` | bsp, hal, domain |
| hal | `src/hal/*.h` | hal |
| HAL port | `src/hal/port/<mcu>/` | Not checked. See [What the check does not cover](#what-the-check-does-not-cover) |

Every layer may also include `<stdint.h>`, `<stdbool.h>` and `<stddef.h>`. Any other header that is not under `src/` fails the check.

The `bsp` layer includes `motor_types.h` from the domain, so that `bsp.h` speaks in rpm and mA. The dependency points inward, toward the domain, and the domain stays free of board knowledge. See [ADR-0003](../adr/0003-pure-domain-core.md).

## Enforcement

`make lint` runs `tools/check_layers.py`. The script reads every `#include` in the `.c` and `.h` files under `src/`. It fails on an include that breaks the table above. Outside `src/hal/port/`, it also fails on a call to `malloc`, `calloc`, `realloc` or `free`, and on the words `float` and `double`. It ignores comments and string literals.

Each failure prints as `path:line: message`. For example, adding `#include "hal_pwm.h"` as line 9 of `src/app/app.c` prints:

	src/app/app.c:9: layer 'app' must not include 'hal_pwm.h' from layer 'hal'

The script finds a header's layer by its file name alone. Every build adds each source directory to the include path, so two layers must never use the same header name. The script fails when they do.

| Requirement | Check |
| --- | --- |
| [LINK: SWR-ARC-001] | The `ALLOWED` table in `tools/check_layers.py` |
| [LINK: SWR-DET-001] | The forbidden-word scan in `tools/check_layers.py` |

## What the check does not cover

The script skips every include, and every forbidden-word match, in files under `src/hal/port/`. A port has to include vendor headers, and the host port uses `double` for its motor model, which [ADR-0004](../adr/0004-fixed-point-arithmetic.md) allows. The script also reads nothing under `tests/`.

The host port uses that freedom beyond the HAL headers:

| File | Includes | Why |
| --- | --- | --- |
| `src/hal/port/host/hal_host.c` | `board_config.h` from bsp | To know which pin, channel and encoder ID it simulates |
| `src/hal/port/host/host_scenario.c` | `app.h` from app | To call `app_status` and print telemetry |
| `hal_host.c`, `host_plant.c` | `<math.h>` | Floating-point motor model and ADC encoding |
| `host_scenario.c` | `<stdio.h>`, `<stdlib.h>` | CSV output, and `exit` at the end of the scenario |

A target port needs only the HAL headers, its vendor headers and the C library. Nothing in the build enforces that limit, so a reviewer checks it.
