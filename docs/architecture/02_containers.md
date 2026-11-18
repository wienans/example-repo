# Containers

One source tree builds three executables. All three compile the same `app`, `domain`, `middleware` and `bsp` sources. They differ only in what stands behind the HAL headers. That shared code is the evidence for the portability requirement [LINK: SYS-006].

This overview diagram shows the three executables and who runs each one. The second line of each box names the HAL implementation that the executable links. Arrows point the way a command or signal travels.

```mermaid
flowchart TB
  accTitle: Executables built from the firmware sources
  accDescr: The repository builds three executables. The target firmware links an MCU HAL port, which the repo does not contain yet, and drives the motor control board. The developer runs the host simulator, which links the host HAL port, and the unit test runners, which link CMock mocks of the HAL headers.
  classDef boundary fill:#FFFFFF,stroke:#666666,stroke-width:1px,stroke-dasharray:5 5,color:black
  classDef person fill:#FFE4B5,stroke:#FF8C00,stroke-width:2px,color:black
  classDef firmware fill:#90EE90,stroke:#2E7D2E,stroke-width:2px,color:darkgreen
  classDef hardware fill:#F0F0F0,stroke:#333333,stroke-width:2px,color:black
  classDef tooling fill:#FFD700,stroke:#B8860B,stroke-width:2px,color:black

  dev["👤 Developer<br/>[Person]<br/>Builds, tests and simulates"]

  subgraph repo [example-repo]
    target["⚙️ Target firmware<br/>[Container: MCU image]<br/>Links src/hal/port/&lt;mcu&gt;, not written yet"]
    sim["⚙️ Host simulator<br/>[Container: Linux executable]<br/>Links src/hal/port/host and a motor model"]
    tests["🛠️ Unit test runners<br/>[Container: Ceedling, Unity, CMock]<br/>Link CMock mocks of src/hal/*.h"]
  end

  board["🔩 Motor control board<br/>[Hardware]<br/>MCU, H-bridge, encoder, buttons"]

  dev -->|"Runs<br/>make sim"| sim
  dev -->|"Runs<br/>make test"| tests
  target -->|"Drives<br/>PWM, GPIO, ADC, timer"| board

  class repo boundary
  class dev person
  class target,sim firmware
  class tests tooling
  class board hardware
  style target fill:#90EE90,stroke:#2E7D2E,stroke-width:2px,stroke-dasharray:5 5,color:darkgreen
```

The dashed border marks the target firmware as planned work. Its MCU port does not exist yet. [Port the firmware to a new MCU](06_porting_guide.md) lists the files the port needs. The source sets and HAL ports are not containers, because none of them is deployed on its own. They appear on the [component page](03_components.md).

| Container | Command | HAL implementation | Purpose |
| --- | --- | --- | --- |
| Target firmware | The vendor toolchain for the chosen MCU | `src/hal/port/<mcu>/` | The product |
| Host simulator | `make sim` | `src/hal/port/host/` | Closed-loop check of [LINK: SYS-001] and [LINK: SYS-004] without hardware |
| Unit test runners | `make test` | CMock mocks of `src/hal/*.h` and `src/bsp/bsp.h` | Behavior of each module, see [LINK: SYS-008] |
| Documentation site | `make docs` | None | Requirements, architecture, ADRs and the API reference in `build/strictdoc` and `build/doxygen` |

[ADR-0007](../adr/0007-c4-views-as-flowcharts.md) explains why this C4 view is a flowchart and not a native `C4Container` diagram.
