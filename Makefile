CC        ?= gcc
PYTHON    ?= python3
CEEDLING  ?= ceedling
DOXYGEN   ?= doxygen
STRICTDOC ?= $(if $(wildcard /opt/sdvenv/bin/strictdoc),/opt/sdvenv/bin/strictdoc,strictdoc)
PUPPETEER_EXECUTABLE_PATH ?= $(shell command -v chromium 2>/dev/null)
export PUPPETEER_EXECUTABLE_PATH

SIM_DIR   := build/sim
SIM_BIN   := $(SIM_DIR)/motor_sim
SIM_CSV   := $(SIM_DIR)/telemetry.csv
SIM_DIRS  := src/app src/domain src/middleware src/bsp src/hal src/hal/port/host
SIM_SRCS  := $(foreach d,$(SIM_DIRS),$(wildcard $(d)/*.c))
SIM_FLAGS := -std=c99 -Wall -Wextra -Wconversion -Werror -O2 $(addprefix -I,$(SIM_DIRS))

.PHONY: all lint test trace sim diagrams docs clean

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

# make docs runs the unit tests once, under gcov, and publishes the results:
# - A red test does not stop the site: the leading - lets make carry on and
#   the result shows red. make trace is the gate that fails on it.
# - The gcov build and its reports start from scratch. Leftover .gcda
#   counters would merge into this run, and a stale report would outlive a
#   build that no longer compiles.
# - StrictDoc only rewrites a page whose own inputs changed, so a requirement
#   page would keep stale result links: the site starts from scratch too.
# - The generated documents live in build/, which StrictDoc's .gitignore
#   filter skips, so they are passed as input paths of their own.
docs: diagrams
	rm -rf build/ceedling/gcov build/ceedling/artifacts/gcov build/strictdoc
	-$(CEEDLING) gcov:all
	$(PYTHON) tools/test_results_to_sdoc.py
	$(PYTHON) tools/coverage_to_sdoc.py
	$(DOXYGEN) docs/Doxyfile
	$(STRICTDOC) export . build/test_results/test_results.sdoc build/coverage/coverage.sdoc --output-dir build/strictdoc
	mkdir -p build/strictdoc/html/coverage/gcovr
	-cp build/ceedling/artifacts/gcov/gcovr/GcovCoverageResults* build/strictdoc/html/coverage/gcovr/

clean:
	rm -rf build
