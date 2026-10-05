"""runs the compiled c program (sw/build/prog.hex) on core_top and checks what it left in dmem.
this is the end-to-end check: c -> gcc .insn -> binary -> imem -> decode -> cordic -> writeback -> sw"""

import math
import os

import cocotb
from cocotb.triggers import FallingEdge

from rv32i import *

HEX = os.path.join(os.path.dirname(__file__), "..", "..", "sw", "build", "prog.hex")
HALT_PC = 0x8 # crt0's jump-to-self
OUT = 0x100
DONE_MAGIC = 0xC0DE
TOL = 0.006


def out_word(dut, i):
    return to_s32(read_dmem_word(dut, OUT + 4 * i))


@cocotb.test()
async def test_c_program(dut):
    assert os.path.exists(HEX), f"{HEX} missing, run `make -C sw` first"
    words = [int(l, 16) for l in open(HEX) if l.strip()]

    start_clock(dut)
    load_program(dut, words, halt=False) # crt0 already has its own halt loop
    clear_dmem(dut)
    await reset_dut(dut)

    # run until the pc has been parked on halt for a few cycles (main returned)
    parked, cycles = 0, 0
    while parked < 5:
        await FallingEdge(dut.clk)
        cycles += 1
        parked = parked + 1 if get_pc(dut) == HALT_PC else 0
        assert cycles < 3000, f"never reached halt, pc stuck at {get_pc(dut):#x}"
    dut._log.info(f"main returned after {cycles - 5} cycles")

    assert out_word(dut, 15) == DONE_MAGIC, "finished flag not written"

    expected = {
        0: ("cos(0.5)", math.cos(0.5)),
        1: ("sin(0.5)", math.sin(0.5)),
        2: ("mag(0.3, 0.4)", math.hypot(0.3, 0.4)),
        3: ("atan2(0.4, 0.3)", math.atan2(0.4, 0.3)),
        12: ("|(cos 1, sin 1)|", 1.0),
    }
    for k in range(8):
        a = to_fixed(-1.4) + k * to_fixed(0.4) # same fixed-point stepping the c loop does
        expected[4 + k] = (f"sin({from_fixed(a):+.2f})", math.sin(from_fixed(a)))

    for idx, (name, ref) in sorted(expected.items()):
        got = from_fixed(out_word(dut, idx))
        err = abs(got - ref)
        dut._log.info(f"  {name:<18} hw {got:+.4f}  ref {ref:+.4f}  err {err:.4f}")
        assert err < TOL, f"{name}: got {got}, expected {ref}"
