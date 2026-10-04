SIM ?= verilator
TOPLEVEL_LANG ?= verilog

TB_DIR  := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
SRC_DIR := $(TB_DIR)/../../src

VERILOG_SOURCES = $(SRC_DIR)/dmem.sv
TOPLEVEL = dmem
MODULE = test_dmem

include $(shell cocotb-config --makefiles)/Makefile.sim
