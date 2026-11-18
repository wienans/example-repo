CC        ?= gcc
PYTHON    ?= python3
CEEDLING  ?= ceedling
DOXYGEN   ?= doxygen
STRICTDOC ?= $(if $(wildcard /opt/sdvenv/bin/strictdoc),/opt/sdvenv/bin/strictdoc,strictdoc)

SIM_DIR   := build/sim
SIM_BIN   := $(SIM_DIR)/motor_sim
SIM_CSV   := $(SIM_DIR)/telemetry.csv
SIM_DIRS  := src/app src/domain src/middleware src/bsp src/hal src/hal/port/host
SIM_SRCS  := $(foreach d,$(SIM_DIRS),$(wildcard $(d)/*.c))
SIM_FLAGS := -std=c99 -Wall -Wextra -Wconversion -Werror -O2 $(addprefix -I,$(SIM_DIRS))

.PHONY: all lint test trace sim docs clean

all: lint test trace sim

lint:
	$(PYTHON) tools/check_layers.py

trace:
	$(PYTHON) tools/check_trace.py

test:
	$(CEEDLING) test:all

$(SIM_BIN): $(SIM_SRCS) $(wildcard $(addsuffix /*.h,$(SIM_DIRS)))
	@mkdir -p $(SIM_DIR)
	$(CC) $(SIM_FLAGS) $(SIM_SRCS) -o $@ -lm

sim: $(SIM_BIN)
	$(SIM_BIN) > $(SIM_CSV)
	@echo "telemetry: $(SIM_CSV) ($$(wc -l < $(SIM_CSV)) lines)"

docs:
	$(DOXYGEN) docs/Doxyfile && $(STRICTDOC) export . --output-dir build/strictdoc

clean:
	rm -rf build
