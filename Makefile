CC        ?= gcc
PYTHON    ?= python3
CEEDLING  ?= ceedling
DOXYGEN   ?= doxygen
# docs/requirements.txt installs Sphinx and gcovr into one virtualenv.
DOCS_VENV ?= /opt/sphinxvenv
# Ceedling's gcov plugin calls gcovr by name, so the virtualenv must be on PATH.
ifneq ($(wildcard $(DOCS_VENV)/bin),)
export PATH := $(DOCS_VENV)/bin:$(PATH)
endif
SPHINX    ?= sphinx-build
PUPPETEER_EXECUTABLE_PATH ?= $(shell command -v chromium 2>/dev/null)
export PUPPETEER_EXECUTABLE_PATH

SIM_DIR   := build/sim
SIM_BIN   := $(SIM_DIR)/motor_sim
SIM_CSV   := $(SIM_DIR)/telemetry.csv
SIM_DIRS  := src/app src/domain src/middleware src/bsp src/hal src/hal/port/host
SIM_SRCS  := $(foreach d,$(SIM_DIRS),$(wildcard $(d)/*.c))
SIM_FLAGS := -std=c99 -Wall -Wextra -Wconversion -Werror -O2 $(addprefix -I,$(SIM_DIRS))

.PHONY: all lint test trace sim diagrams reports docs release clean

all: lint test trace sim

lint:
	$(PYTHON) tools/check_layers.py

# check_trace reads the JUnit report that the test run writes.
trace: test
	$(PYTHON) tools/check_trace.py

test:
	$(CEEDLING) test:all

$(SIM_BIN): $(SIM_SRCS) $(wildcard $(addsuffix /*.h,$(SIM_DIRS)))
	@mkdir -p $(SIM_DIR)
	$(CC) $(SIM_FLAGS) $(SIM_SRCS) -o $@ -lm

sim: $(SIM_BIN)
	$(SIM_BIN) > $(SIM_CSV)
	@echo "telemetry: $(SIM_CSV) ($$(wc -l < $(SIM_CSV)) lines)"

diagrams:
	python3 tools/check_diagrams.py

# make reports runs the unit tests once, under gcov, and turns the markers
# and results into the Code traceability, Test results and Code coverage
# pages in docs/generated/, which git ignores. make docs publishes them:
# - A red test does not stop the site: the leading - lets make carry on and
#   the result shows red. make trace is the gate that fails on it.
# - The gcov build and its reports start from scratch. Leftover .gcda
#   counters would merge into this run, and a stale report would outlive a
#   build that no longer compiles.
# - Sphinx runs with -W, so a marker or a {need} role that names an unknown
#   requirement fails the build. Breathe does not tell Sphinx when the
#   Doxygen XML changed, so the site starts from scratch.
GENERATED_DOCS := docs/generated
SITE           := build/sphinx/html
reports:
	rm -rf build/ceedling/gcov build/ceedling/artifacts/gcov $(GENERATED_DOCS)/*.rst
	-$(CEEDLING) gcov:all
	$(PYTHON) tools/code_to_rst.py
	$(PYTHON) tools/test_results_to_rst.py
	$(PYTHON) tools/coverage_to_rst.py

docs: diagrams reports
	rm -rf build/sphinx build/doxygen
	$(DOXYGEN) docs/Doxyfile
	$(SPHINX) -W --keep-going -b html docs $(SITE)
	mkdir -p $(SITE)/generated/gcovr
	-cp build/ceedling/artifacts/gcov/gcovr/GcovCoverageResults* $(SITE)/generated/gcovr/

# make release VERSION=v1.2.3 [PREVIOUS=v1.2.2] [PUBLISH=0]
# - make trace runs first, so a release never ships a requirement without a
#   passing test.
# - make docs builds the Sphinx site and the Doxygen reference, and through
#   make reports the Code traceability, Test results and Code coverage pages,
#   so the full PDF ends with them.
# - tools/release.py tags HEAD, builds the site as one page and prints it
#   into one PDF, prints the system and software requirements added, removed
#   or changed since PREVIOUS (default: the latest tag) into a second, zips
#   build/sphinx/html and build/doxygen/html, then pushes main and the tag
#   and creates a GitHub release with the two PDFs and the zip. The generated
#   pages are git-ignored, so the changelog never lists them.
#   PUBLISH=0 builds the files into build/release/ and stops.
ifneq ($(filter release,$(MAKECMDGOALS)),)
ifndef VERSION
$(error usage: make release VERSION=v1.2.3 [PREVIOUS=v1.2.2] [PUBLISH=0])
endif
endif
release: trace docs
	SPHINX=$(SPHINX) $(PYTHON) tools/release.py $(VERSION) \
		$(if $(PREVIOUS),--previous $(PREVIOUS)) $(if $(filter 0,$(PUBLISH)),--no-publish)

clean:
	rm -rf build $(GENERATED_DOCS)/*.rst
