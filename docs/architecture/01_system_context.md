# System context

The firmware holds a brushed DC motor at a commanded speed. It reads the shaft speed from a quadrature encoder and the winding current from a shunt resistor, and it drives the motor through an H-bridge. An operator starts and stops the motor with two buttons. The firmware switches the drive off on overcurrent or stall.

This overview diagram is for a reader new to the project. It shows the firmware as one box and everything it exchanges signals with. Arrows point the way each signal travels.

```mermaid
flowchart LR
  accTitle: System context of the motor control firmware
  accDescr: The operator presses start and stop buttons wired to the firmware. The firmware sets PWM duty, direction and enable on the power stage, and reads winding current back from it over the ADC. The quadrature encoder reports shaft position to the firmware through a timer.
  classDef person fill:#FFE4B5,stroke:#FF8C00,stroke-width:2px,color:black
  classDef firmware fill:#90EE90,stroke:#2E7D2E,stroke-width:2px,color:darkgreen
  classDef hardware fill:#F0F0F0,stroke:#333333,stroke-width:2px,color:black

  operator["👤 Operator<br/>[Person]<br/>Starts, stops and acknowledges faults"]
  fw["⚙️ Motor control firmware<br/>[Software system: C99]<br/>Holds the set speed and trips on faults"]
  bridge["🔩 Power stage<br/>[Hardware]<br/>H-bridge, DC motor, current shunt"]
  encoder["🔩 Quadrature encoder<br/>[Hardware]<br/>Mounted on the motor shaft"]

  operator -->|"Start and stop buttons<br/>GPIO, active low"| fw
  fw -->|"Duty, direction, enable<br/>PWM and GPIO"| bridge
  bridge -->|"Winding current<br/>ADC"| fw
  encoder -->|"Shaft position<br/>Timer in encoder mode"| fw

  class operator person
  class fw firmware
  class bridge,encoder hardware
```

The symbols and colors follow [Diagram conventions](00_diagram_conventions.md).

## What the system promises

| Promise | Requirement |
| --- | --- |
| Speed within 2 % of the setpoint, settled within 1 s | [LINK: SYS-001] |
| Start and stop from the buttons | [LINK: SYS-002] |
| Drive disabled within 1 ms of overcurrent | [LINK: SYS-003] |
| Drive disabled when the rotor stalls | [LINK: SYS-004] |
| Drive stays off until the operator acknowledges a fault | [LINK: SYS-005] |
| Logic above the HAL port runs on any MCU | [LINK: SYS-006] |
| Fixed 1 ms loop with integer arithmetic | [LINK: SYS-007] |
| All logic above the HAL port tests on a PC | [LINK: SYS-008] |

The `[LINK: ...]` tags resolve to the requirement pages in the StrictDoc export. On GitHub they show as plain text.

## Out of scope

The example has no communication interface, no non-volatile parameter storage and no bootloader. Each of those would be a new middleware module behind its own header, and none of them changes the layer rule in [Layering](04_layering.md).
