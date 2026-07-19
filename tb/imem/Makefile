SIM ?= verilator
TOPLEVEL_LANG ?= verilog

VERILOG_SOURCES = /home/ayanna/projects/riscv-cordic/src/imem.sv
TOPLEVEL = imem
MODULE = test_imem
COMPILE_ARGS += -GINIT_FILE=\"$(PWD)/test_prog.hex\"

include $(shell cocotb-config --makefiles)/Makefile.sim