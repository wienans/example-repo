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
| `docs/01_requirements/` | System and software requirements as sphinx-needs directives in reStructuredText. `software_requirements.rst` lists one `software_<domain>.rst` per domain |
| `docs/02_architecture/` | Diagram conventions, C4 context, container and component views, layering, runtime, porting guide |
| `docs/adr/` | Architecture decision records |
| `docs/conf.py`, `docs/index.rst` | Sphinx configuration and the site's table of contents. `docs/api.rst` pulls the C API from Doxygen's XML through Breathe, `docs/traceability.rst` holds the trace tables and the requirement graph |
| `tools/` | `check_layers.py`, `check_trace.py` and `check_diagrams.py`, the checks behind `make lint`, `make trace` and `make diagrams`. `code_to_rst.py`, `test_results_to_rst.py` and `coverage_to_rst.py` write the Code traceability, Test results and Code coverage pages for `make docs`. `source_markers.py` reads the `@relation` markers for all of them |

## Prerequisites

- GCC and GNU Make
- Ruby and Ceedling 1.x: `gem install ceedling`
- Python 3.10 or later
- Python packages for the documentation, Sphinx, sphinx-needs, Breathe, MyST, sphinxcontrib-mermaid, Furo and gcovr, pinned in `docs/requirements.txt`: `python3 -m venv /opt/sphinxvenv && /opt/sphinxvenv/bin/pip install -r docs/requirements.txt`. The Makefile puts `/opt/sphinxvenv/bin` on `PATH`. Set `DOCS_VENV` to use another virtualenv
- Doxygen 1.18 or later and Graphviz. Debian and Ubuntu ship older versions, so install the Linux binary from doxygen.nl and put its `bin/` on `PATH`, or run `make docs DOXYGEN=/path/to/doxygen`
- Node.js and Mermaid CLI: `npm install -g @mermaid-js/mermaid-cli`. Set `PUPPETEER_EXECUTABLE_PATH` if Chromium is not where Puppeteer expects it

## Build and check

Run each check from the repo root.

| Command | What it does |
| --- | --- |
| `make lint` | Fails if a file includes a header from a layer it may not depend on, or uses heap or floating point above the HAL port |
| `make test` | Builds and runs every Ceedling unit test |
| `make trace` | Runs `make test`, then fails if a software requirement has no passing test or check that names it, or no code that implements it, or if a marker has the wrong role for its directory |
| `make sim` | Builds the firmware with the host HAL port, runs a 2.5 s scenario, writes `build/sim/telemetry.csv` |
| `make diagrams` | Checks every Mermaid diagram in `docs/` against `docs/02_architecture/00_diagram_conventions.md` and renders it to `build/diagrams/` |
| `make docs` | Runs `make diagrams`, runs the unit tests once with coverage, then builds the Doxygen XML and HTML and the Sphinx site with the Code traceability, Test results and Code coverage pages. Fails on any Sphinx warning, such as a link to an unknown requirement, but not on a failing test, which shows red |
| `make all` | Runs `lint`, `test`, `trace` and `sim` |
| `make release VERSION=v1.2.3` | Runs `make trace` and `make docs`, tags HEAD, and builds into `build/release/`: one PDF of the whole Sphinx site, including the Code traceability, Test results and Code coverage pages, one PDF of the system and software requirements added, removed or changed since the previous tag, from a diff of the two `needs.json` exports, and `docs-VERSION.zip` with the Sphinx site and the Doxygen reference. Then pushes `main` and the tag, and creates a GitHub release with the three files. `PREVIOUS=v1.2.0` picks the tag to compare with, `PUBLISH=0` stops after the PDFs and removes the tag |

Open `build/sphinx/html/index.html` for requirements, architecture, ADRs, the C API, traceability, test results and coverage. `build/doxygen/html/index.html` has the Doxygen reference with its source browser.

Requirements are plain text. Edit the `.rst` file and run `make docs`. Each requirement is a need with a fixed `:id:`, and every link between needs names that ID, so keep it when you change a title. `make docs` also writes `build/sphinx/html/needs.json`, every need with its fields and links, for other tools to read. `make release` needs Chromium and the GitHub CLI (`gh`), logged in.

## The simulator scenario

`make sim` presses the start button at 10 ms, with a setpoint of 1500 rpm. The motor settles within 1 s. At 1500 ms the simulator locks the rotor. The fault monitor detects the stall, and the firmware switches the drive off and enters `FAULT`. Each line of `telemetry.csv` holds `t_ms,setpoint_rpm,speed_rpm,current_ma,duty,state`.

## How the documentation connects

Each function that implements a requirement, and each test that checks one, names it in its Doxygen comment:

	/**
	 * @brief Advance the controller by one sample.
	 * @relation(SWR-PI-001, scope=function, role=Implementation)
	 */

The role says what the marker is evidence of: `role=Implementation` in `src/`, `role=Test` in `tests/`, and `role=Check` for the static checks in `tools/`. When only part of a function implements a requirement, mark that part instead: `scope=line` for one code line, `scope=range_start` and `scope=range_end` around several. A marker may sit in a `/* */` or `//` comment, but not in a one-line `/* @relation(...) */`, which `make trace` rejects. `tools/code_to_rst.py` turns each `Implementation` and `Check` marker into a need that links to its requirement and shows the marked code. `make docs` fails when a marker or a `{need}` role in a Markdown page names an unknown requirement. `make trace` fails when a requirement has no implementation, or when none of its tests passed in the last run. It reads the results from the JUnit report Ceedling writes to `build/ceedling/artifacts/test/junit_tests_report.xml`, so a failing or ignored test is not evidence.

`make docs` turns the same markers into two more generated pages. Test results lists every test by file with its status, and each requirement lists its tests under "is verified by". Code coverage shows, per requirement, the line and branch coverage of the code its `role=Implementation` markers name, with links to the uncovered lines in gcovr's report. `docs/adr/0008-sphinx-documentation-toolchain.md` explains the setup.

## Port to a new MCU

Follow the porting guide in `docs/02_architecture/06_porting_guide.md`. A port adds `src/hal/port/<mcu>/` and may edit `src/bsp/board_config.h`. It changes nothing in `src/app`, `src/domain` or `src/middleware`.
