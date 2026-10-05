SIM ?= verilator
TOPLEVEL_LANG ?= verilog

TB_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
SRC_DIR := $(TB_DIR)/../../src

VERILOG_SOURCES = $(SRC_DIR)/alu.sv
TOPLEVEL = alu
MODULE = test_alu

include $(shell cocotb-config --makefiles)/Makefile.sim
