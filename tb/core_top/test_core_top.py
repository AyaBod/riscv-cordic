"""core_top rv32i tests: 27 tests covering every rv32i instruction through the full datapath.

each test loads a tiny program into imem, resets, runs a fixed number of cycles and checks
registers / memory. sampling happens on the falling edge so the rising-edge writes have landed.
cordic tests live in tb/core_cordic so this file stays pure rv32i.
"""

import cocotb
from cocotb.triggers import FallingEdge

from rv32i import *

M32 = 0xFFFFFFFF


def golden_alu(op, a, b):
    """reference model: what each alu op should give for 32-bit a, b"""
    sa, sb_ = to_s32(a), to_s32(b)
    sh = b & 0x1F
    return {
        "add": (a + b) & M32, "sub": (a - b) & M32,
        "and": a & b, "or": a | b, "xor": a ^ b,
        "sll": (a << sh) & M32, "srl": a >> sh, "sra": (sa >> sh) & M32,
        "slt": int(sa < sb_), "sltu": int(a < b),
    }[op]


def check(dut, reg, expected, what=""):
    got = get_reg(dut, reg)
    assert got == expected & M32, f"{what} x{reg}: got {got:#010x}, expected {expected & M32:#010x}"


# ---------------------------------------------------------------------------
# basics
# ---------------------------------------------------------------------------

@cocotb.test()
async def test_reset(dut):
    """reset puts the pc at 0 and clears every register"""
    start_clock(dut)
    load_program(dut, [addi(i, 0, i) for i in range(1, 8)])
    await reset_dut(dut)
    await run_cycles(dut, 8) # dirty the regfile first
    await reset_dut(dut)
    assert get_pc(dut) == 0
    for i in range(32):
        assert get_reg(dut, i) == 0, f"x{i} not cleared by reset"


@cocotb.test()
async def test_pc_increment(dut):
    """non-control instructions advance the pc by exactly 4 per clock"""
    start_clock(dut)
    load_program(dut, [NOP] * 8)
    await reset_dut(dut) # returns on the falling edge where reset lets go, pc still 0
    for i in range(6):
        assert get_pc(dut) == 4 * i, f"cycle {i}: pc {get_pc(dut):#x}"
        await FallingEdge(dut.clk)


@cocotb.test()
async def test_lui(dut):
    """lui loads the upper 20 bits and zeroes the low 12"""
    start_clock(dut)
    await boot(dut, [lui(1, 0xABCDE), lui(2, 0x80000), lui(3, 0x00001)], 5)
    check(dut, 1, 0xABCDE000, "lui")
    check(dut, 2, 0x80000000, "lui sign bit")
    check(dut, 3, 0x00001000, "lui small")


@cocotb.test()
async def test_auipc(dut):
    """auipc adds the shifted immediate to the pc of the auipc itself"""
    start_clock(dut)
    await boot(dut, [NOP, auipc(1, 0x12345), auipc(2, 0xFFFFF)], 5)
    check(dut, 1, 0x12345000 + 4, "auipc @4")
    check(dut, 2, (0xFFFFF000 + 8) & M32, "auipc @8 negative")


# ---------------------------------------------------------------------------
# r-type alu ops (rs1 op rs2 -> rd)
# ---------------------------------------------------------------------------
A, B, NEG = 0xF0F0A5A5, 0x00000023, 0xFFFFFFF6 # B = 35 so shifts must mask to shamt 3; NEG = -10

def rtype_program(ops):
    prog = load_const(1, A) + load_const(2, B) + load_const(6, NEG)
    for rd, fn, rs1, rs2 in ops:
        prog.append(fn(rd, rs1, rs2))
    return prog

def regval(r):
    return {1: A, 2: B, 6: NEG}[r]


async def run_rtype(dut, ops, names):
    start_clock(dut)
    await boot(dut, rtype_program(ops), len(ops) + 8)
    for (rd, _, rs1, rs2), name in zip(ops, names):
        check(dut, rd, golden_alu(name, regval(rs1), regval(rs2)), name)


@cocotb.test()
async def test_rtype_add_sub(dut):
    """add/sub including wraparound past 32 bits"""
    await run_rtype(dut, [(3, add, 1, 2), (4, sub, 1, 2), (5, sub, 2, 1), (7, add, 1, 1)],
                    ["add", "sub", "sub", "add"])


@cocotb.test()
async def test_rtype_logic(dut):
    """and/or/xor"""
    await run_rtype(dut, [(3, and_, 1, 2), (4, or_, 1, 2), (5, xor, 1, 2), (7, xor, 1, 6)],
                    ["and", "or", "xor", "xor"])


@cocotb.test()
async def test_rtype_shifts(dut):
    """sll/srl/sra, only the low 5 bits of rs2 count, sra keeps the sign"""
    await run_rtype(dut, [(3, sll, 1, 2), (4, srl, 1, 2), (5, sra, 1, 2), (7, sra, 6, 2)],
                    ["sll", "srl", "sra", "sra"])


@cocotb.test()
async def test_rtype_compare(dut):
    """slt is signed, sltu is unsigned: -10 < 35 signed but not unsigned"""
    await run_rtype(dut, [(3, slt, 6, 2), (4, sltu, 6, 2), (5, slt, 2, 6), (7, sltu, 2, 6)],
                    ["slt", "sltu", "slt", "sltu"])


# ---------------------------------------------------------------------------
# i-type alu ops (rs1 op imm -> rd)
# ---------------------------------------------------------------------------

@cocotb.test()
async def test_itype_addi(dut):
    """addi with positive, negative and edge-of-range immediates"""
    start_clock(dut)
    prog = load_const(1, A) + [addi(2, 1, -37), addi(3, 0, 2047), addi(4, 0, -2048), addi(5, 3, 1)]
    await boot(dut, prog, 10)
    check(dut, 2, A - 37, "addi -37")
    check(dut, 3, 2047, "addi max")
    check(dut, 4, -2048, "addi min")
    check(dut, 5, 2048, "addi chain")


@cocotb.test()
async def test_itype_logic(dut):
    """xori/ori/andi, immediates sign-extend before the op (xori -1 = not)"""
    start_clock(dut)
    prog = load_const(1, A) + [xori(2, 1, -1), ori(3, 1, 0x00F), andi(4, 1, -37), andi(5, 1, 0x7FF)]
    await boot(dut, prog, 10)
    check(dut, 2, ~A, "xori -1")
    check(dut, 3, A | 0xF, "ori")
    check(dut, 4, A & (-37 & M32), "andi negative")
    check(dut, 5, A & 0x7FF, "andi positive")


@cocotb.test()
async def test_itype_shifts(dut):
    """slli/srli/srai by 5, srai on a negative value fills with ones"""
    start_clock(dut)
    prog = load_const(1, A) + [slli(2, 1, 5), srli(3, 1, 5), srai(4, 1, 5), srai(5, 1, 31)]
    await boot(dut, prog, 10)
    check(dut, 2, golden_alu("sll", A, 5), "slli")
    check(dut, 3, golden_alu("srl", A, 5), "srli")
    check(dut, 4, golden_alu("sra", A, 5), "srai")
    check(dut, 5, M32, "srai 31")


@cocotb.test()
async def test_itype_compare(dut):
    """slti signed, sltiu unsigned (sltiu rd, rs, 1 is seqz, and -1 means 0xFFFFFFFF)"""
    start_clock(dut)
    prog = load_const(1, NEG) + [slti(2, 1, 0), sltiu(3, 1, 5), sltiu(4, 0, 1), sltiu(5, 1, -1), slti(7, 1, -20)]
    await boot(dut, prog, 10)
    check(dut, 2, 1, "slti -10 < 0")
    check(dut, 3, 0, "sltiu big < 5")
    check(dut, 4, 1, "seqz 0")
    check(dut, 5, 1, "sltiu < 0xffffffff")
    check(dut, 7, 0, "slti -10 < -20")


# ---------------------------------------------------------------------------
# branches: each case either skips (taken) or runs (not taken) a marker addi
# ---------------------------------------------------------------------------

async def run_branch_cases(dut, a, b, cases):
    """cases: list of (branch_fn, should_take). marker regs 10.. get 1 only if the branch fell through"""
    prog = load_const(1, a) + load_const(2, b)
    for k, (fn, _) in enumerate(cases):
        prog += [fn(1, 2, 8), addi(10 + k, 0, 1)] # taken -> jumps over the marker
    await boot(dut, prog, len(prog) + 4)
    for k, (fn, take) in enumerate(cases):
        assert get_reg(dut, 10 + k) == (0 if take else 1), f"{fn.__name__}({a:#x},{b:#x}) taken={not take}"


@cocotb.test()
async def test_beq_bne(dut):
    start_clock(dut)
    await run_branch_cases(dut, 5, 5, [(beq, True), (bne, False)])
    await run_branch_cases(dut, 5, 6, [(beq, False), (bne, True)])


@cocotb.test()
async def test_blt_bge(dut):
    """signed: -10 < 3"""
    start_clock(dut)
    await run_branch_cases(dut, NEG, 3, [(blt, True), (bge, False)])
    await run_branch_cases(dut, 3, 3, [(blt, False), (bge, True)])


@cocotb.test()
async def test_bltu_bgeu(dut):
    """unsigned: 0xFFFFFFF6 is huge, so it is not below 3"""
    start_clock(dut)
    await run_branch_cases(dut, NEG, 3, [(bltu, False), (bgeu, True)])
    await run_branch_cases(dut, 3, NEG, [(bltu, True), (bgeu, False)])


@cocotb.test()
async def test_branch_backward_loop(dut):
    """negative branch offset: count x1 up to 5"""
    start_clock(dut)
    prog = [addi(2, 0, 5), # 0x0
            addi(1, 1, 1), # 0x4 <- loop
            bne(1, 2, -4), # 0x8
            addi(3, 0, 99)] # 0xC runs once after the loop
    await boot(dut, prog, 20)
    check(dut, 1, 5, "loop counter")
    check(dut, 3, 99, "after loop")


# ---------------------------------------------------------------------------
# jumps
# ---------------------------------------------------------------------------

@cocotb.test()
async def test_jal(dut):
    """jal skips forward and writes pc+4 into rd"""
    start_clock(dut)
    prog = [NOP, jal(1, 8), addi(2, 0, 1), addi(3, 0, 7)] # jal at 0x4 -> 0xC
    await boot(dut, prog, 5)
    check(dut, 1, 0x8, "jal link")
    check(dut, 2, 0, "skipped instruction ran")
    check(dut, 3, 7, "target")


@cocotb.test()
async def test_jalr(dut):
    """jalr jumps to rs1+imm with the lsb cleared and writes pc+4"""
    start_clock(dut)
    prog = [addi(5, 0, 0x11), # 0x0 odd base on purpose
            jalr(1, 5, 3), # 0x4 0x11 + 3 = 0x14 (lsb already clear)
            addi(2, 0, 1), # 0x8 skipped
            addi(2, 0, 2), # 0xC skipped
            addi(2, 0, 3), # 0x10 skipped
            jalr(4, 5, 0), # 0x14 0x11 -> 0x10 once the lsb is cleared, so it bounces back
            ]
    await boot(dut, prog, 6)
    check(dut, 1, 0x8, "jalr link")
    check(dut, 4, 0x18, "second jalr link")
    check(dut, 2, 3, "lsb-cleared target")


# ---------------------------------------------------------------------------
# loads / stores
# ---------------------------------------------------------------------------

@cocotb.test()
async def test_sw_lw(dut):
    """word store/load with a negative offset"""
    start_clock(dut)
    clear_dmem(dut)
    prog = load_const(1, 0xDEADBEEF) + [addi(2, 0, 0x104), sw(1, 2, -4), lw(3, 0, 0x100)]
    await boot(dut, prog, 8)
    check(dut, 3, 0xDEADBEEF, "lw")
    assert read_dmem_word(dut, 0x100) == 0xDEADBEEF


@cocotb.test()
async def test_sb_lb_lbu(dut):
    """bytes land little-endian, lb sign-extends, lbu zero-extends"""
    start_clock(dut)
    clear_dmem(dut)
    prog = load_const(1, 0x12345680) + [sb(1, 0, 0x40), sb(1, 0, 0x41), lb(2, 0, 0x40), lbu(3, 0, 0x40), lw(4, 0, 0x40)]
    await boot(dut, prog, 10)
    check(dut, 2, 0xFFFFFF80, "lb")
    check(dut, 3, 0x00000080, "lbu")
    check(dut, 4, 0x00008080, "two bytes only")


@cocotb.test()
async def test_sh_lh_lhu(dut):
    """halfwords: lh sign-extends, lhu zero-extends"""
    start_clock(dut)
    clear_dmem(dut)
    prog = load_const(1, 0x1234C001) + [sh(1, 0, 0x80), lh(2, 0, 0x80), lhu(3, 0, 0x80), lw(4, 0, 0x80)]
    await boot(dut, prog, 9)
    check(dut, 2, 0xFFFFC001, "lh")
    check(dut, 3, 0x0000C001, "lhu")
    check(dut, 4, 0x0000C001, "upper half untouched")


@cocotb.test()
async def test_load_use_same_cycle(dut):
    """the instruction right after a load can use it, no bubble (single cycle has no hazard here)"""
    start_clock(dut)
    clear_dmem(dut)
    prog = [addi(1, 0, 21), sw(1, 0, 0x20), lw(2, 0, 0x20), add(3, 2, 2), sw(3, 0, 0x24), lw(4, 0, 0x24)]
    await boot(dut, prog, 8)
    check(dut, 3, 42, "load-use")
    check(dut, 4, 42, "store-load-store")


@cocotb.test()
async def test_x0_hardwired(dut):
    """writes to x0 vanish no matter which unit writes"""
    start_clock(dut)
    clear_dmem(dut)
    prog = [addi(0, 0, 5), lui(0, 0xFFFFF), jal(0, 4), lw(0, 0, 0), add(1, 0, 0), addi(2, 0, 3)]
    await boot(dut, prog, 8)
    check(dut, 0, 0, "x0")
    check(dut, 1, 0, "read of x0")
    check(dut, 2, 3, "core kept going")


@cocotb.test()
async def test_out_of_range_memory(dut):
    """accesses past the 1 KB dmem don't wrap onto real data and don't stop the core"""
    start_clock(dut)
    clear_dmem(dut)
    prog = (load_const(1, 0xCAFEF00D) + [sw(1, 0, 0x0)]
            + load_const(2, 0x400) # 1024: first byte past the end, aliases to 0 if unchecked
            + [sw(2, 2, 0), lw(3, 2, 0), # out-of-range store + load
               sw(2, 0, 0x3FE), # word that would straddle the end (1022..1025)
               lw(4, 0, 0x0), lw(6, 0, 0x3FC), addi(5, 0, 1)])
    await boot(dut, prog, 14)
    check(dut, 3, 0, "out-of-range load")
    check(dut, 4, 0xCAFEF00D, "in-range word clobbered by out-of-range store")
    check(dut, 6, 0, "straddling store partially landed")
    check(dut, 5, 1, "core stopped after out-of-range access")


# ---------------------------------------------------------------------------
# misc-mem / system
# ---------------------------------------------------------------------------

@cocotb.test()
async def test_fence_ecall_ebreak_nop(dut):
    """fence is a legal nop on a single in-order hart; ecall/ebreak decode as nops (no trap support)"""
    start_clock(dut)
    prog = [addi(1, 0, 1), FENCE, ECALL, EBREAK, addi(2, 0, 2)]
    load_program(dut, prog)
    await reset_dut(dut)
    for i in range(5):
        assert get_pc(dut) == 4 * i, "pc didn't step through fence/ecall/ebreak"
        await FallingEdge(dut.clk)
    check(dut, 1, 1)
    check(dut, 2, 2)
    for r in range(3, 32):
        check(dut, r, 0, "fence/ecall/ebreak wrote a register")


# ---------------------------------------------------------------------------
# programs
# ---------------------------------------------------------------------------

@cocotb.test()
async def test_load_const_full_range(dut):
    """lui + addi builds any 32-bit value, including the bit-11 carry cases"""
    start_clock(dut)
    consts = [0xDEADBEEF, 0x00000800, 0xFFFFF800, 0x7FFFFFFF, 0x80000000, 0x00000FFF, 0x12345678]
    prog = []
    for k, c in enumerate(consts):
        prog += load_const(1 + k, c)
    await boot(dut, prog, len(prog) + 3)
    for k, c in enumerate(consts):
        check(dut, 1 + k, c, f"load_const {c:#x}")


@cocotb.test()
async def test_integration_sum_program(dut):
    """small real program: sum 1..10 in a loop, store it, load it back, compare with a branch"""
    start_clock(dut)
    clear_dmem(dut)
    prog = [addi(1, 0, 0), # 0x00 sum = 0
            addi(2, 0, 1), # 0x04 i = 1
            addi(3, 0, 11), # 0x08 limit
            add(1, 1, 2), # 0x0C <- loop: sum += i
            addi(2, 2, 1), # 0x10 i++
            blt(2, 3, -8), # 0x14 while i < 11
            sw(1, 0, 0x200), # 0x18
            lw(4, 0, 0x200), # 0x1C
            addi(5, 0, 55), # 0x20
            beq(4, 5, 8), # 0x24 skip the fail marker if it matches
            addi(6, 0, -1), # 0x28 fail marker
            addi(7, 0, 1)] # 0x2C pass marker
    await boot(dut, prog, 60)
    check(dut, 1, 55, "sum")
    check(dut, 4, 55, "stored/loaded sum")
    check(dut, 6, 0, "fail marker")
    check(dut, 7, 1, "pass marker")
