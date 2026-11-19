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
# - The generated documents go to docs/generated/, at the depth of
#   docs/requirements/. StrictDoc builds a requirement's links to code from
#   the depth of its own document, so a document at another depth, or a
#   second export input path, gets broken links. Git ignores them through
#   docs/generated/.gitignore; StrictDoc reads only the root .gitignore.
# - StrictDoc puts the documents under a folder named after the checkout.
GENERATED_DOCS := docs/generated
SITE_DOCS      := build/strictdoc/html/$(notdir $(CURDIR))/$(GENERATED_DOCS)
docs: diagrams
	rm -rf build/ceedling/gcov build/ceedling/artifacts/gcov build/strictdoc $(GENERATED_DOCS)/*.sdoc
	-$(CEEDLING) gcov:all
	$(PYTHON) tools/test_results_to_sdoc.py
	$(PYTHON) tools/coverage_to_sdoc.py
	$(DOXYGEN) docs/Doxyfile
	$(STRICTDOC) export . --output-dir build/strictdoc
	mkdir -p $(SITE_DOCS)/gcovr
	-cp build/ceedling/artifacts/gcov/gcovr/GcovCoverageResults* $(SITE_DOCS)/gcovr/

clean:
	rm -rf build $(GENERATED_DOCS)/*.sdoc
