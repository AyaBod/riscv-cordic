SIM ?= verilator
TOPLEVEL_LANG ?= verilog

# Point to your SystemVerilog source file
VERILOG_SOURCES = /home/ayanna/projects/riscv-cordic/src/cordic.sv

# Module name inside your cordic.sv file
TOPLEVEL = cordic
MODULE = test_cordic

# FIX: Waveform tracing flags + ignore minor style/width lint warnings
EXTRA_ARGS += --trace --trace-structs -Wno-WIDTH -Wno-UNUSEDSIGNAL

include $(shell cocotb-config --makefiles)/Makefile.sim
