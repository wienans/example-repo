# Containers

One source tree builds three executables. The target firmware and the host simulator compile the same `app`, `domain`, `middleware` and `bsp` sources. They differ only in the HAL port that stands behind the HAL headers. The simulator is therefore the evidence for the portability requirement {need}`SYS-006`. The unit test runners compile one module at a time against CMock mocks.

This overview diagram shows the three executables and who runs each one. The second line of each box names the C4 element type and how the executable is built. Arrows point the way a command or data travels.

```mermaid
flowchart TB
  accTitle: Executables built from the firmware sources
  accDescr: The repository builds three executables. The target firmware links an MCU HAL port, which the repo does not contain yet, and drives the motor control board. The developer runs the host simulator, which links the host HAL port and a motor model and writes a telemetry file. The developer also runs the unit test runners, which link CMock mocks.
  classDef boundary fill:#FFFFFF,stroke:#666666,stroke-width:1px,stroke-dasharray:5 5,color:black
  classDef person fill:#FFE4B5,stroke:#FF8C00,stroke-width:2px,color:black
  classDef firmware fill:#90EE90,stroke:#2E7D2E,stroke-width:2px,color:darkgreen
  classDef hardware fill:#F0F0F0,stroke:#333333,stroke-width:2px,color:black
  classDef tooling fill:#FFD700,stroke:#B8860B,stroke-width:2px,color:black

  dev["👤 Developer<br/>[Person]<br/>Builds, tests and simulates"]

  subgraph repo [example-repo]
    target["⚙️ Target firmware<br/>[Container: MCU image]<br/>Links src/hal/port/&lt;mcu&gt;, not written yet"]
    sim["⚙️ Host simulator<br/>[Container: Linux executable]<br/>Links src/hal/port/host and a motor model"]
    tests["🛠️ Unit test runners<br/>[Container: Ceedling, Unity, CMock]<br/>One runner per test file"]
  end

  board["🔩 Motor control board<br/>[Hardware]<br/>MCU, H-bridge, encoder, buttons"]

  dev -->|"Runs<br/>make sim"| sim
  sim -->|"Writes<br/>build/sim/telemetry.csv"| dev
  dev -->|"Runs<br/>make test"| tests
  target -->|"Drives<br/>PWM, GPIO, ADC, timer"| board

  class repo boundary
  class dev person
  class target,sim firmware
  class tests tooling
  class board hardware
  style target fill:#90EE90,stroke:#2E7D2E,stroke-width:2px,stroke-dasharray:5 5,color:darkgreen
```

The dashed border marks the target firmware as planned work, because no MCU port exists yet. [Port the firmware to a new MCU](06_porting_guide.md) lists the files that a port needs. Source sets and HAL ports are not containers, because none of them is deployed on its own. They appear on the [component page](03_components.md).

| Container | Command | Compiles | HAL behind the headers | Purpose |
| --- | --- | --- | --- | --- |
| Target firmware | The vendor toolchain for the chosen MCU | `src/app`, `src/domain`, `src/middleware`, `src/bsp`, `src/hal/port/<mcu>/` | The MCU port | The product |
| Host simulator | `make sim` | `src/app`, `src/domain`, `src/middleware`, `src/bsp`, `src/hal/port/host/` | `hal_host.c`, which steps the motor model in `host_plant.c` once per millisecond | Closed-loop check of {need}`SYS-001` and {need}`SYS-004` without hardware |
| Unit test runners | `make test` | One test file, the module under test, and the real modules or mocks that the test includes. `project.yml` excludes `src/app/main.c` and `src/hal/port/` | CMock mocks of `src/hal/*.h` in the `bsp` tests, a mock of `src/bsp/bsp.h` in the `app` test | Behavior of each module, see {need}`SYS-008` |

The simulator runs a fixed scenario from `src/hal/port/host/host_scenario.c`. It presses start at 10 ms, locks the rotor at 1500 ms, and exits at 2500 ms. Every 10 ms it prints one CSV row to standard output, and `make sim` redirects that output to `build/sim/telemetry.csv`.

`make docs` also builds the Doxygen API reference in `build/doxygen/` and the Sphinx site in `build/sphinx/html/`. These are documentation outputs, not executables, so the diagram leaves them out.

[ADR-0007](../adr/0007-c4-views-as-flowcharts.md) explains why this C4 view is a flowchart and not a native `C4Container` diagram.
