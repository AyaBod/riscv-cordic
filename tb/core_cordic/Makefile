# runs test_core_cordic.py against core_top with verilator. paths are relative to this file so a fresh clone just works
SIM ?= verilator
TOPLEVEL_LANG = verilog

TB_DIR  := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
SRC_DIR := $(TB_DIR)/../../src

# order doesn't matter to verilator, core_top just has to be the toplevel
VERILOG_SOURCES = $(SRC_DIR)/alu.sv $(SRC_DIR)/regfile.sv $(SRC_DIR)/imm_gen.sv \
                  $(SRC_DIR)/control.sv $(SRC_DIR)/imem.sv $(SRC_DIR)/dmem.sv \
                  $(SRC_DIR)/cordic.sv $(SRC_DIR)/core_top.sv

TOPLEVEL = core_top
MODULE   = test_core_cordic

# shared encoders/helpers live in tb/common
export PYTHONPATH := $(TB_DIR)/../common:$(PYTHONPATH)

include $(shell cocotb-config --makefiles)/Makefile.sim
