# Layering

This page lists the layers, what each may include, and how the rule is enforced.

```mermaid
flowchart TD
  app["app<br/>src/app"]
  mw["middleware<br/>src/middleware"]
  dom["domain<br/>src/domain"]
  bsp["bsp<br/>src/bsp"]
  hal["hal interfaces<br/>src/hal/*.h"]
  port["hal port<br/>src/hal/port/&lt;mcu&gt;"]
  vendor["MCU vendor library"]

  app --> mw
  app --> dom
  app --> bsp
  bsp --> dom
  bsp --> hal
  port -. implements .-> hal
  port --> vendor
```

## Include rule

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

`make lint` runs `tools/check_layers.py`. The script reads every `#include` under `src/` and fails with `file:line` on an include that breaks the table above. It also fails on `malloc`, `calloc`, `realloc`, `free`, `float` or `double` outside `src/hal/port/`.

| Requirement | Check |
| --- | --- |
| [LINK: SWR-ARC-001] | `tools/check_layers.py` include table |
| [LINK: SWR-DET-001] | `tools/check_layers.py` forbidden tokens |
