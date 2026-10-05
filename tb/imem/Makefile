SIM ?= verilator
TOPLEVEL_LANG ?= verilog

TB_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
SRC_DIR := $(TB_DIR)/../../src

VERILOG_SOURCES = $(SRC_DIR)/imem.sv
TOPLEVEL = imem
MODULE = test_imem
COMPILE_ARGS += -GINIT_FILE=\"$(TB_DIR)/test_prog.hex\"

include $(shell cocotb-config --makefiles)/Makefile.sim
