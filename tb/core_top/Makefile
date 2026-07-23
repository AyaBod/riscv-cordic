SIM ?= verilator
TOPLEVEL_LANG ?= verilog

VERILOG_SOURCES = /home/ayanna/projects/riscv-cordic/src/imem.sv \
                  /home/ayanna/projects/riscv-cordic/src/control.sv \
                  /home/ayanna/projects/riscv-cordic/src/imm_gen.sv \
                  /home/ayanna/projects/riscv-cordic/src/regfile.sv \
                  /home/ayanna/projects/riscv-cordic/src/alu.sv \
                  /home/ayanna/projects/riscv-cordic/src/dmem.sv \
                  /home/ayanna/projects/riscv-cordic/src/core_top.sv

TOPLEVEL = core_top
MODULE = test_core_top

include $(shell cocotb-config --makefiles)/Makefile.sim
VERILATOR_FLAGS += -I../../src
