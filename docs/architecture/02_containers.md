# Containers

One source tree builds three executables. They share the same `app`, `domain`, `middleware` and `bsp` sources and differ only in what stands behind the HAL headers. That shared code is the evidence for the portability requirement [LINK: SYS-006].

This overview diagram answers one question: which executable links which HAL implementation. Arrows point from the source code to the executable built from it. The arrow into the **Executables** box means all three executables compile the shared sources.

```mermaid
flowchart TB
  accTitle: Executables built from the shared firmware sources
  accDescr: The shared firmware sources are compiled into all three executables. Each executable links one HAL implementation. The target firmware links an MCU HAL port, which the repo does not contain yet. The host simulator links the host HAL port. The unit test runners link CMock mocks generated from the HAL headers. The target firmware drives the motor control board.
  classDef boundary fill:#FFFFFF,stroke:#666666,stroke-width:1px,stroke-dasharray:5 5,color:black
  classDef firmware fill:#90EE90,stroke:#2E7D2E,stroke-width:2px,color:darkgreen
  classDef platform fill:#E6E6FA,stroke:#8A2BE2,stroke-width:2px,color:darkblue
  classDef hardware fill:#F0F0F0,stroke:#333333,stroke-width:2px,color:black
  classDef tooling fill:#FFD700,stroke:#B8860B,stroke-width:2px,color:black

  shared["⚙️ Shared firmware sources<br/>[C99]<br/>src/app, src/domain, src/middleware, src/bsp"]

  subgraph hals [HAL implementations]
    direction LR
    mcuport["🔧 MCU HAL port<br/>[C99]<br/>src/hal/port/&lt;mcu&gt;, not written yet"]
    hostport["🔧 Host HAL port<br/>[C99]<br/>src/hal/port/host, with a motor plant model"]
    mocks["🛠️ HAL mocks<br/>[CMock]<br/>Generated from src/hal/*.h"]
  end

  subgraph outputs [Executables]
    direction LR
    target["⚙️ Target firmware<br/>[Container: MCU image]<br/>Runs on the board"]
    sim["⚙️ Host simulator<br/>[Container: Linux executable]<br/>make sim"]
    tests["🛠️ Unit test runners<br/>[Container: Ceedling, Unity]<br/>make test"]
  end

  board["🔩 Motor control board<br/>[Hardware]"]

  mcuport -->|"linked into"| target
  hostport -->|"linked into"| sim
  mocks -->|"linked into"| tests
  shared -->|"compiled into"| outputs
  target -->|"PWM, GPIO, ADC, timer"| board

  class hals,outputs boundary
  class shared,target,sim firmware
  class hostport platform
  class mocks,tests tooling
  class board hardware
  style mcuport fill:#E6E6FA,stroke:#8A2BE2,stroke-width:2px,stroke-dasharray:5 5,color:darkblue
```

The dashed border marks the MCU port as planned work. [Port the firmware to a new MCU](06_porting_guide.md) lists the files it needs.

| Container | Command | HAL implementation | Purpose |
| --- | --- | --- | --- |
| Target firmware | The vendor toolchain for the chosen MCU | `src/hal/port/<mcu>/` | The product |
| Host simulator | `make sim` | `src/hal/port/host/` | Closed-loop check of [LINK: SYS-001] and [LINK: SYS-004] without hardware |
| Unit test runners | `make test` | CMock mocks of `src/hal/*.h` and `src/bsp/bsp.h` | Behavior of each module, see [LINK: SYS-008] |
| Documentation site | `make docs` | None | Requirements, architecture, ADRs and the API reference in `build/strictdoc` and `build/doxygen` |
