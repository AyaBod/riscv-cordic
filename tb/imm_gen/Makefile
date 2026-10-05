SIM ?= verilator
TOPLEVEL_LANG ?= verilog

TB_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
SRC_DIR := $(TB_DIR)/../../src

VERILOG_SOURCES = $(SRC_DIR)/imm_gen.sv
TOPLEVEL = imm_gen
MODULE = test_imm_gen

include $(shell cocotb-config --makefiles)/Makefile.sim
