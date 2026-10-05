"""cordic as a second execution unit inside core_top.

covers all four custom instructions, the stall (pc frozen, no phantom instructions, write lands
on the done cycle), back-to-back + dependent instructions, and rd = x0.
"""

import math

import cocotb
from cocotb.triggers import FallingEdge

from rv32i import *

ITER = 12
STALL_CYCLES = ITER + 1 # start cycle + 12 iterate cycles, core_stall high the whole time
OCCUPANCY = STALL_CYCLES + 1 # plus the done cycle where the write commits and the pc moves on

ANGLES = [-1.5, -0.7, 0.0, 0.3, 0.9, 1.5]
VECTORS = [(0.5, 0.0), (0.5, 0.5), (0.5, -0.5), (1.0, 0.25), (0.3, -0.9), (1.5, 1.5), (0.1, 0.1)]


async def run_cordic_case(dut, instr, a_val, b_val=0.0, rd=3):
    """x1 = a, x2 = b, run one cordic instruction into rd, then a marker addi that must run exactly once"""
    program = load_const(1, to_fixed(a_val)) + load_const(2, to_fixed(b_val))
    program += [instr(rd), addi(4, 4, 7)] # addi x4 += 7: phantom re-execution would make it 14+
    load_program(dut, program)
    await reset_dut(dut)
    await run_cycles(dut, 4 + OCCUPANCY + 4)
    assert get_reg_signed(dut, 4) == 7, "instruction after cordic ran the wrong number of times"
    raw = get_reg_signed(dut, rd)
    assert -32768 <= raw <= 32767, "rd isn't a sign-extended 16-bit value"
    return from_fixed(raw)


@cocotb.test()
async def test_cordic_cos(dut):
    start_clock(dut)
    for t in ANGLES:
        got = await run_cordic_case(dut, lambda rd: cordic_cos(rd, 1), t)
        assert abs(got - math.cos(t)) < 0.002, f"cos({t}) = {got:.4f}"


@cocotb.test()
async def test_cordic_sin(dut):
    start_clock(dut)
    for t in ANGLES:
        got = await run_cordic_case(dut, lambda rd: cordic_sin(rd, 1), t)
        assert abs(got - math.sin(t)) < 0.002, f"sin({t}) = {got:.4f}"


@cocotb.test()
async def test_cordic_mag(dut):
    start_clock(dut)
    for x, y in VECTORS:
        got = await run_cordic_case(dut, lambda rd: cordic_mag(rd, 1, 2), x, y)
        assert abs(got - math.hypot(x, y)) < 0.002, f"mag({x},{y}) = {got:.4f}"


@cocotb.test()
async def test_cordic_atan2(dut):
    start_clock(dut)
    for x, y in VECTORS:
        got = await run_cordic_case(dut, lambda rd: cordic_atan2(rd, 1, 2), x, y)
        assert abs(got - math.atan2(y, x)) < 0.006, f"atan2({y},{x}) = {got:.4f}"


@cocotb.test()
async def test_cordic_stall_and_commit_timing(dut):
    """pc parks on the cordic instruction for the whole op, rd stays untouched until the done cycle,
    and the very next cycle the following instruction runs with the result already visible"""
    start_clock(dut)
    prog = load_const(1, to_fixed(0.5)) # 0x0, 0x4
    cordic_pc = 4 * len(prog) # 0x8
    prog += [cordic_cos(3, 1), add(5, 3, 0)] # 0x8, 0xC
    load_program(dut, prog)
    await reset_dut(dut)

    while get_pc(dut) != cordic_pc:
        await FallingEdge(dut.clk)

    for cyc in range(OCCUPANCY):
        assert get_pc(dut) == cordic_pc, f"pc moved during cordic (cycle {cyc})"
        assert get_reg(dut, 3) == 0, f"rd written early (cycle {cyc})"
        assert get_reg(dut, 5) == 0, f"next instruction ran during the stall (cycle {cyc})"
        expect_stall = 1 if cyc < STALL_CYCLES else 0
        assert int(dut.core_stall.value) == expect_stall, f"core_stall={int(dut.core_stall.value)} on cycle {cyc}"
        await FallingEdge(dut.clk)

    assert get_pc(dut) == cordic_pc + 4, "pc didn't move on after done"
    res = from_fixed(get_reg_signed(dut, 3))
    assert abs(res - math.cos(0.5)) < 0.002, f"cos result {res}"
    await FallingEdge(dut.clk)
    assert get_reg(dut, 5) == get_reg(dut, 3), "dependent add didn't see the cordic result"
    dut._log.info(f"cordic occupies {OCCUPANCY} cycles ({STALL_CYCLES} stalled + 1 commit), alu ops take 1")


@cocotb.test()
async def test_cordic_back_to_back_and_dependent(dut):
    """cos then sin with nothing in between, then add both: each one restarts the unit cleanly"""
    start_clock(dut)
    t = 0.6
    prog = load_const(1, to_fixed(t)) + [cordic_cos(3, 1), cordic_sin(4, 1), add(5, 3, 4),
                                         cordic_mag(6, 3, 4)] # chained: mag(cos, sin) should be ~1
    await boot(dut, prog, 2 + 3 * OCCUPANCY + 6)
    c, s = from_fixed(get_reg_signed(dut, 3)), from_fixed(get_reg_signed(dut, 4))
    assert abs(c - math.cos(t)) < 0.002 and abs(s - math.sin(t)) < 0.002
    assert get_reg(dut, 5) == (get_reg(dut, 3) + get_reg(dut, 4)) & 0xFFFFFFFF, "dependent add"
    assert abs(from_fixed(get_reg_signed(dut, 6)) - 1.0) < 0.003, "cos^2 + sin^2 != 1 through the hardware"


@cocotb.test()
async def test_cordic_rd_x0_ignored(dut):
    """cordic.cos x0 still stalls and finishes, but x0 stays 0 and the core keeps going"""
    start_clock(dut)
    prog = load_const(1, to_fixed(0.3)) + [cordic_cos(0, 1), addi(2, 0, 9)]
    await boot(dut, prog, 2 + OCCUPANCY + 3)
    assert get_reg(dut, 0) == 0
    assert get_reg(dut, 2) == 9, "instruction after cordic x0 never ran"


@cocotb.test()
async def test_cordic_negative_operands(dut):
    """negative q3.13 inputs survive the trip through 32-bit registers (only the low 16 bits are used)"""
    start_clock(dut)
    got = await run_cordic_case(dut, lambda rd: cordic_sin(rd, 1), -1.2)
    assert abs(got - math.sin(-1.2)) < 0.002
    got = await run_cordic_case(dut, lambda rd: cordic_atan2(rd, 1, 2), 0.8, -0.6)
    assert abs(got - math.atan2(-0.6, 0.8)) < 0.006
