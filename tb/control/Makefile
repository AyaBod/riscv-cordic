SIM ?= verilator
TOPLEVEL_LANG ?= verilog

TB_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
SRC_DIR := $(TB_DIR)/../../src

VERILOG_SOURCES = $(SRC_DIR)/control.sv
TOPLEVEL = control
MODULE = test_control

include $(shell cocotb-config --makefiles)/Makefile.sim
