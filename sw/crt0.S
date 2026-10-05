# crt0: the 3 instructions that run before main
# stack goes at the top of dmem, main gets called, and when it returns the pc parks on halt

    .section .text.init
    .globl _start
_start:
    li sp, 0x400 # top of the 1 KB dmem, stack grows down from here
    jal ra, main # ra = 0x8, so main's ret lands on halt
halt:
    j halt # jump-to-self at 0x8, the testbench waits for the pc to sit here
