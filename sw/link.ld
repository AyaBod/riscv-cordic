/* link.ld: code goes in imem at 0, nothing is allowed in data memory
 * the core is harvard (imem and dmem both start at 0) and dmem has no init file,
 * so any global or constant table would silently read back as 0. fail the link instead. */

ENTRY(_start)

MEMORY {
    IMEM (rx) : ORIGIN = 0x00000000, LENGTH = 1K
    DMEM (rw) : ORIGIN = 0x20000000, LENGTH = 1K   /* fake address, only here so the assert below can see it */
}

SECTIONS {
    .text : { KEEP(*(.text.init)) *(.text*) } > IMEM          /* crt0 first so _start is at 0 */
    .data : { *(.data*) *(.sdata*) *(.rodata*) *(.srodata*) *(.bss*) *(.sbss*) *(COMMON) } > DMEM
    ASSERT(SIZEOF(.data) == 0, "globals/constants in memory are not supported: use locals and immediates")
    /DISCARD/ : { *(.comment) *(.riscv.attributes) *(.eh_frame*) }
}
