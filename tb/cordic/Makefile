# standalone cordic unit tests, no cpu involved
SIM ?= verilator
TOPLEVEL_LANG = verilog

TB_DIR  := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
SRC_DIR := $(TB_DIR)/../../src

VERILOG_SOURCES = $(SRC_DIR)/cordic.sv
TOPLEVEL = cordic
MODULE   = test_cordic

export PYTHONPATH := $(TB_DIR)/../common:$(PYTHONPATH)

include $(shell cocotb-config --makefiles)/Makefile.sim
