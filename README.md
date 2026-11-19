# Motor control example

Example firmware for closed-loop speed control of a brushed DC motor. It holds the motor at a set speed, and it switches the drive off on overcurrent or stall. The code targets no particular MCU. Everything above `src/hal/` builds for any MCU that implements the HAL headers, and the repo ships a host port that runs the firmware against a simulated motor.

## Repository layout

| Path | Contents |
| --- | --- |
| `src/app/` | Entry point `main.c`, task wiring in `app.c`, tuning in `app_config.h` |
| `src/domain/` | PI controller, motor state machine, fault monitor, motor control step. Pure C, no I/O |
| `src/middleware/` | Cooperative fixed-period scheduler |
| `src/bsp/` | Board pin map and unit conversion, written against the HAL headers |
| `src/hal/` | HAL interface headers. `src/hal/port/<mcu>/` holds one implementation per MCU |
| `tests/unit/` | Ceedling unit tests, one directory per layer |
| `docs/requirements/` | System and software requirements in StrictDoc `.sdoc`. `software_requirements.sdoc` includes one file per domain from `software/` |
| `docs/architecture/` | Diagram conventions, C4 context, container and component views, layering, runtime, porting guide |
| `docs/adr/` | Architecture decision records |
| `tools/` | `check_layers.py`, `check_trace.py` and `check_diagrams.py`, the checks behind `make lint`, `make trace` and `make diagrams` |

## Prerequisites

- GCC and GNU Make
- Ruby and Ceedling 1.x: `gem install ceedling`
- Python 3.10 or later
- StrictDoc: `pip install strictdoc`
- Doxygen 1.9 or later and Graphviz
- Node.js and Mermaid CLI: `npm install -g @mermaid-js/mermaid-cli`. Set `PUPPETEER_EXECUTABLE_PATH` if Chromium is not where Puppeteer expects it

## Build and check

Run each check from the repo root.

| Command | What it does |
| --- | --- |
| `make lint` | Fails if a file includes a header from a layer it may not depend on, or uses heap or floating point above the HAL port |
| `make test` | Builds and runs every Ceedling unit test |
| `make trace` | Fails if a software requirement has no test or check that names it |
| `make sim` | Builds the firmware with the host HAL port, runs a 2.5 s scenario, writes `build/sim/telemetry.csv` |
| `make diagrams` | Checks every Mermaid diagram in `docs/` against `docs/architecture/00_diagram_conventions.md` and renders it to `build/diagrams/` |
| `make docs` | Runs `make diagrams`, then builds the Doxygen API reference and the StrictDoc site, and fails on a broken requirement link |
| `make all` | Runs `lint`, `test`, `trace` and `sim` |

Open `build/strictdoc/html/index.html` for requirements, architecture and ADRs. Open `build/doxygen/html/index.html` for the API reference.

## The simulator scenario

`make sim` presses the start button at 10 ms, with a setpoint of 1500 rpm. The motor settles within 1 s. At 1500 ms the simulator locks the rotor. The fault monitor detects the stall, and the firmware switches the drive off and enters `FAULT`. Each line of `telemetry.csv` holds `t_ms,setpoint_rpm,speed_rpm,current_ma,duty,state`.

## How the documentation connects

Each function that implements a requirement, and each test that checks one, names it in its Doxygen comment:

	/**
	 * @brief Advance the controller by one sample.
	 * @relation(SWR-PI-001, scope=function)
	 */

StrictDoc reads these markers and links each requirement to its code and tests. `make docs` fails when a marker or a `[LINK: UID]` tag in a Markdown page names an unknown requirement. `make trace` fails when a requirement has no test. `docs/adr/0006-documentation-toolchain.md` explains the setup.

## Port to a new MCU

Follow the porting guide in `docs/architecture/06_porting_guide.md`. A port adds `src/hal/port/<mcu>/` and may edit `src/bsp/board_config.h`. It changes nothing in `src/app`, `src/domain` or `src/middleware`.
