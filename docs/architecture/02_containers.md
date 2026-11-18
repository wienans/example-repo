# Containers

One source tree builds three executables. They differ only in the HAL port they link and in who calls the code. The same `app`, `domain`, `middleware` and `bsp` sources run in all three, which is the evidence for the portability requirement [LINK: SYS-006].

```mermaid
C4Container
  title Containers: one source tree, three executables

  Person(dev, "Developer")

  System_Boundary(repo, "example-repo") {
    Container(target, "Target firmware", "C99, MCU HAL port", "Runs on the board. Links src/hal/port/<mcu>")
    Container(sim, "Host simulator", "C99, host HAL port", "Runs on a PC. Links src/hal/port/host with a motor plant model")
    Container(tests, "Unit test runners", "Ceedling, Unity, CMock", "One executable per tests/unit/**/test_*.c file")
    ContainerDb(docs, "Documentation site", "StrictDoc and Doxygen HTML", "Requirements, architecture, ADRs and API reference")
  }

  System_Ext(board, "Motor control board", "MCU, H-bridge, encoder, buttons")

  Rel(dev, tests, "make test")
  Rel(dev, sim, "make sim")
  Rel(dev, docs, "make docs")
  Rel(target, board, "Drives")
  Rel(docs, tests, "Traces requirements to", "@relation markers")

  UpdateLayoutConfig($c4ShapeInRow="2", $c4BoundaryInRow="1")
```

| Container | Built by | HAL implementation | Purpose |
| --- | --- | --- | --- |
| Target firmware | The vendor toolchain for the chosen MCU | `src/hal/port/<mcu>/` | The product |
| Host simulator | `make sim` | `src/hal/port/host/` | Closed-loop check of [LINK: SYS-001] and [LINK: SYS-004] without hardware |
| Unit test runners | `make test` | CMock mocks of `src/hal/*.h` and `src/bsp/bsp.h` | Behavior of each module, see [LINK: SYS-008] |
| Documentation site | `make docs` | none | Requirements, design and API in one place |

The repo ships only the host port. [Porting to a new MCU](06_porting_guide.md) lists the files a target port adds.
