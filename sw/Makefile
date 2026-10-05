# sw/Makefile: main.c -> prog.elf -> prog.bin -> prog.hex (what imem loads)
# works with riscv64-unknown-elf-, riscv32-unknown-elf- or riscv-none-elf- toolchains
PREFIX ?= $(shell for p in riscv64-unknown-elf- riscv32-unknown-elf- riscv-none-elf-; do \
            command -v $${p}gcc >/dev/null 2>&1 && echo $$p && break; done)
CC = $(PREFIX)gcc
OBJCOPY = $(PREFIX)objcopy
OBJDUMP = $(PREFIX)objdump

# rv32i only (no m extension -> never write * or /), no libc, no startup files but ours
CFLAGS = -march=rv32i -mabi=ilp32 -O2 -ffreestanding -nostdlib -nostartfiles -fno-builtin \
         -Wall -Wno-array-bounds

BUILD = build

all: $(BUILD)/prog.hex $(BUILD)/prog.dis
	python3 check_encoding.py $(BUILD)/prog.hex

$(BUILD):
	mkdir -p $@

$(BUILD)/prog.elf: crt0.S main.c cordic.h link.ld | $(BUILD)
	$(CC) $(CFLAGS) -T link.ld crt0.S main.c -o $@ -Wl,--no-warn-rwx-segments

$(BUILD)/prog.bin: $(BUILD)/prog.elf
	$(OBJCOPY) -O binary $< $@

$(BUILD)/prog.hex: $(BUILD)/prog.bin
	python3 hexgen.py $< $@

# disassembly for reading along; custom ops show up as .insn since binutils doesn't know them
$(BUILD)/prog.dis: $(BUILD)/prog.elf
	$(OBJDUMP) -d -M no-aliases $< > $@

clean:
	rm -rf $(BUILD)

.PHONY: all clean
