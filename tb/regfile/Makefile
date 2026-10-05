SIM ?= verilator
TOPLEVEL_LANG ?= verilog

TB_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
SRC_DIR := $(TB_DIR)/../../src

VERILOG_SOURCES = $(SRC_DIR)/regfile.sv
TOPLEVEL = regfile
MODULE = test_regfile

include $(shell cocotb-config --makefiles)/Makefile.sim
