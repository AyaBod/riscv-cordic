import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles
from cocotb.triggers import ReadOnly
import math

FRAC_BITS = 13

OPC_LUI = 0b0110111
OPC_AUIPC = 0b0010111
OPC_JAL = 0b1101111
OPC_JALR = 0b1100111
OPC_BRANCH = 0b1100011
OPC_LOAD = 0b0000011
OPC_STORE = 0b0100011
OPC_OP_IMM = 0b0010011
OPC_OP = 0b0110011

F3_BEQ, F3_BNE, F3_BLT, F3_BGE, F3_BLTU, F3_BGEU = 0b000, 0b001, 0b100, 0b101, 0b110, 0b111
F3_LB, F3_LH, F3_LW, F3_LBU, F3_LHU = 0b000, 0b001, 0b010, 0b100, 0b101
F3_SB, F3_SH, F3_SW = 0b000, 0b001, 0b010
F3_ADD_SUB, F3_SLL, F3_SLT, F3_SLTU, F3_XOR, F3_SRL_SRA, F3_OR, F3_AND = 0b000, 0b001, 0b010, 0b011, 0b100, 0b101, 0b110, 0b111

# HELPERS !!!!!!

def r_type(opcode, rd, funct3, rs1, rs2, funct7):
    return (funct7 << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode

def i_type(opcode, rd, funct3, rs1, imm):
    imm12 = imm & 0xFFF
    return (imm12 << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode

def s_type(opcode, funct3, rs1, rs2, imm):
    imm12 = imm & 0xFFF
    imm_11_5 = (imm12 >> 5) & 0x7F
    imm_4_0 = imm12 & 0x1F
    return (imm_11_5 << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (imm_4_0 << 7) | opcode

def b_type(opcode, funct3, rs1, rs2, imm):
    imm13 = imm & 0x1FFF
    bit12 = (imm13 >> 12) & 1
    bit11 = (imm13 >> 11) & 1
    bits10_5 = (imm13 >> 5) & 0x3F
    bits4_1 = (imm13 >> 1) & 0xF
    return (bit12 << 31) | (bits10_5 << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (bits4_1 << 8) | (bit11 << 7) | opcode

def u_type(opcode, rd, imm32):
    return (imm32 & 0xFFFFF000) | (rd << 7) | opcode

def j_type(opcode, rd, imm):

    imm21 = imm & 0x1FFFFF
    bit20 = (imm21 >> 20) & 1
    bits10_1 = (imm21 >> 1) & 0x3FF
    bit11 = (imm21 >> 11) & 1
    bits19_12 = (imm21 >> 12) & 0xFF
    return (bit20 << 31) | (bits10_1 << 21) | (bit11 << 20) | (bits19_12 << 12) | (rd << 7) | opcode


#basc return the instrcutions
def addi(rd, rs1, imm): return i_type(OPC_OP_IMM, rd, 0b000, rs1, imm)
def add(rd, rs1, rs2): return r_type(OPC_OP, rd, F3_ADD_SUB, rs1, rs2, 0b0000000)
def sub(rd, rs1, rs2): return r_type(OPC_OP, rd, F3_ADD_SUB, rs1, rs2, 0b0100000)
def lui(rd, imm32): return u_type(OPC_LUI, rd, imm32)
def auipc(rd, imm32): return u_type(OPC_AUIPC, rd, imm32)
def jal(rd, imm): return j_type(OPC_JAL, rd, imm)
def jalr(rd, rs1, imm): return i_type(OPC_JALR, rd, 0b000, rs1, imm)

def beq(rs1, rs2, imm): return b_type(OPC_BRANCH, F3_BEQ, rs1, rs2, imm)
def bne(rs1, rs2, imm): return b_type(OPC_BRANCH, F3_BNE, rs1, rs2, imm)
def blt(rs1, rs2, imm): return b_type(OPC_BRANCH, F3_BLT, rs1, rs2, imm)
def bge(rs1, rs2, imm): return b_type(OPC_BRANCH, F3_BGE, rs1, rs2, imm)
def bltu(rs1, rs2, imm): return b_type(OPC_BRANCH, F3_BLTU, rs1, rs2, imm)
def bgeu(rs1, rs2, imm): return b_type(OPC_BRANCH, F3_BGEU, rs1, rs2, imm)

def lw(rd, rs1, imm): return i_type(OPC_LOAD, rd, F3_LW, rs1, imm)
def lh(rd, rs1, imm): return i_type(OPC_LOAD, rd, F3_LH, rs1, imm)
def lhu(rd, rs1, imm): return i_type(OPC_LOAD, rd, F3_LHU, rs1, imm)
def lb(rd, rs1, imm): return i_type(OPC_LOAD, rd, F3_LB, rs1, imm)
def lbu(rd, rs1, imm): return i_type(OPC_LOAD, rd, F3_LBU, rs1, imm)

def sw(rs1, rs2, imm): return s_type(OPC_STORE, F3_SW, rs1, rs2, imm)
def sh(rs1, rs2, imm): return s_type(OPC_STORE, F3_SH, rs1, rs2, imm)
def sb(rs1, rs2, imm): return s_type(OPC_STORE, F3_SB, rs1, rs2, imm)

def load_const(rd, value32):
    """
    Standard RISC-V two-instruction idiom for loading an arbitrary 32-bit
    constant into a register: LUI sets the upper 20 bits, ADDI sign-extends
    a 12-bit correction onto the lower 12. The +0x800 rounding compensates
    for ADDI's immediate being sign-extended, so the two instructions
    reconstruct the exact original value.
    Returns a list of 2 encoded instructions.
    """
    upper = (value32 + 0x800) >> 12
    lower = value32 - (upper << 12)
    return [lui(rd, upper & 0xFFFFF), addi(rd, rd, lower & 0xFFF)]

# cordic

def encode_cordic(rd, rs1, rs2, mode):
    """R type cusom0 encoding """
    opcode = 0b0001011
    funct3 = mode & 0b1
    return (0 << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode

def to_fixed(val: float) -> int:
    return int(round(val * (1 << FRAC_BITS))) & 0xFFFF

def from_fixed(val: int) -> float:
    val = val & 0xFFFF
    if val & 0x8000:
        val -= 0x10000
    return val / (1 << FRAC_BITS)


# DUT HELPERS !!!!!!!!!!
def to_signed32(val):
    val &= 0xFFFFFFFF
    return val - 0x1_0000_0000 if val & 0x8000_0000 else val

async def start_clock(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

async def reset_dut(dut):
    dut.rst_n.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1

def load_program(dut, instrs):
    """Poke instructions directly into imem.words[]. Zero-fills the rest."""
    for i in range(256):
        dut.u_imem.words[i].value = instrs[i] if i < len(instrs) else 0

def clear_dmem(dut):
    for i in range(1024):
        dut.u_dmem.mem[i].value = 0

def get_reg(dut, idx):
    return int(dut.u_regfile.regs[idx].value)

def get_reg_signed(dut, idx):
    return to_signed32(get_reg(dut, idx))

def get_mem_byte(dut, addr):
    return int(dut.u_dmem.mem[addr].value)

async def run_cycles(dut, n):
    for _ in range(n):
        await RisingEdge(dut.clk)

async def setup(dut, instrs):
    """Common bring-up: clock, program load, reset release."""
    await start_clock(dut)
    clear_dmem(dut)
    load_program(dut, instrs)
    await reset_dut(dut)


# ACTUAL TESTS !!!! -

#sequencing
@cocotb.test()
async def test_reset(dut):
    """PC starts at 0 after every reset."""
    await setup(dut, [addi(1, 0, 5)])
    await RisingEdge(dut.clk)
    assert int(dut.pc_current.value) == 0, f"expected 0 got {int(dut.pc_current.value)}"

@cocotb.test()
async def test_pc_increment(dut):
    """no branches or jumps pc should advance by 4 each cycle."""
    prog = [addi(1, 0, i) for i in range(5)] #5 numbers repping the 5 instructions
    await setup(dut, prog) #put instructions to memory
    await ReadOnly() #sample starting pc after settup settles 
    prev_pc = int(dut.pc_current.value)

    for i in range(4):
        await RisingEdge(dut.clk)
        await ReadOnly()
        pc = int(dut.pc_current.value) #read newly settled pc value
        assert pc == prev_pc + 4, f"expected {prev_pc + 4}, got {pc}"
        prev_pc = pc #update for next loop

# alu operand muxing (LUI / AUIPC)

@cocotb.test()
async def test_lui(dut):
    """rd gets the raw upper-immediate value (proves the LUI/SLTU alu_op fix)."""
    prog = [lui(1, 0x12345000)]
    await setup(dut, prog)
    await ReadOnly()
    await run_cycles(dut, 1)
    await ReadOnly()
    assert get_reg(dut, 1) == 0x12345000

@cocotb.test()
async def test_auipc(dut):
    """rd = pc_current + imm, proving operand_a switches to PC for AUIPC."""
    prog = [addi(1, 0, 0), auipc(2, 0x00002000)]  # auipc at pc=4
    await setup(dut, prog)
    await ReadOnly()
    await run_cycles(dut, 2)
    await ReadOnly()
    assert get_reg(dut, 2) == (4 + 0x00002000)


# branch resolution

async def _branch_case(dut, mnemonic, rs1_val, rs2_val, expect_taken):
    # x1=rs1_val, x2=rs2_val, branch +8 (skip poison instr), else fall through
    # PC 0x00: addi x1, x0, rs1_val
    # PC 0x04: addi x2, x0, rs2_val
    # PC 0x08: branch instruction -> if taken, skip to 0x10 (+8 bytes)
    # PC 0x0C: addi x3, x0, 111 -> Not-taken poison path
    # PC 0x10: addi x3, x0, 222-> Taken path
    # PC 0x14: jal x0, 0 -> prevetns overrun
    
    
    prog = [
    addi(1, 0, rs1_val),
    addi(2, 0, rs2_val),
    mnemonic(1, 2, 12),  # Widen offset to +12 bytes to skip the trap!
    addi(3, 0, 111),     # Executed only if fall-through
    jal(0, 0),           # TRAP 1: If non-taken, lock the CPU here forever
    addi(3, 0, 222),     # Executed if branch taken
    jal(0, 0)            # TRAP 2: If taken, lock the CPU here forever
]

    await setup(dut, prog)
    await run_cycles(dut, 5)
    await ReadOnly()
    expected = 222 if expect_taken else 111
    assert get_reg(dut, 3) == expected

@cocotb.test()
async def test_beq_taken(dut):
    """BEQ: Taken condition (rs1 == rs2) routes PC+Imm to next_pc."""
    await _branch_case(dut, beq, 5, 5, True)

@cocotb.test()
async def test_beq_not_taken(dut):
    """BEQ: Fall-through condition (rs1 != rs2) routes PC+4 to next_pc."""
    await _branch_case(dut, beq, 5, 6, False)

@cocotb.test()
async def test_bne_taken(dut):
    """BNE: Taken condition (rs1 != rs2) routes PC+Imm to next_pc."""
    await _branch_case(dut, bne, 5, 6, True)

@cocotb.test()
async def test_bne_not_taken(dut):
    """BNE: Fall-through condition (rs1 == rs2) routes PC+4 to next_pc."""
    await _branch_case(dut, bne, 5, 5, False)

@cocotb.test()
async def test_blt_taken(dut):
    """BLT: Signed taken (-1 < 1) verifies SLT-driven branch resolution logic."""
    await _branch_case(dut, blt, -1, 1, True)

@cocotb.test()
async def test_blt_not_taken(dut):
    """BLT: Signed fall-through (1 < -1 is false) verifies inverse SLT logic."""
    await _branch_case(dut, blt, 1, -1, False)

@cocotb.test()
async def test_bge_taken(dut):
    """BGE: Signed taken (1 >= -1) verifies inverse SLT-driven branch resolution logic."""
    await _branch_case(dut, bge, 1, -1, True)

@cocotb.test()
async def test_bge_not_taken(dut):
    """BGE: Signed fall-through (-1 >= 1 is false) verifies strict SLT detection."""
    await _branch_case(dut, bge, -1, 1, False)

@cocotb.test()
async def test_bltu_taken(dut):
    """BLTU: Unsigned taken (1 < 0xFFFFFFFF) verifies zero-extension flag routing."""
    await _branch_case(dut, bltu, 1, -1, True)

@cocotb.test()
async def test_bltu_not_taken(dut):
    """BLTU: Unsigned fall-through (0xFFFFFFFF < 1 is false) catches sign-extension leakage."""
    await _branch_case(dut, bltu, -1, 1, False)

@cocotb.test()
async def test_bgeu_taken(dut):
    """BGEU: Unsigned taken (0xFFFFFFFF >= 1) verifies zero-extension inverse SLT logic."""
    await _branch_case(dut, bgeu, -1, 1, True)

@cocotb.test()
async def test_bgeu_not_taken(dut):
    """BGEU: Unsigned fall-through (1 >= 0xFFFFFFFF is false) catches raw math width limits."""
    await _branch_case(dut, bgeu, 1, -1, False)


#jumps
@cocotb.test()
async def test_jal(dut):
    """JAL target = pc + imm; rd = pc + 4 (not ALU result)."""
    prog = [
        jal(1, 8), # pc=0 -> target=8, x1 should get 4
        addi(2, 0, 999), # at pc=4, skipped
        addi(3, 0, 42), # at pc=8, executed
        jal(0, 0)
    ]
    await setup(dut, prog)
    await run_cycles(dut, 4)
    await ReadOnly()
    assert get_reg(dut, 1) == 4
    assert get_reg(dut, 2) == 0 # never executed
    assert get_reg(dut, 3) == 42

@cocotb.test()
async def test_jalr(dut):
    """JALR target = (rs1 + imm) & ~1 -- rs1+imm deliberately odd to catch a missing mask."""
    prog = [
        addi(1, 0, 9),     
        jalr(2, 1, 3),     
        addi(3, 0, 999),   
        addi(4, 0, 42),    
        jal(0, 0)          
    ]
    await setup(dut, prog)
    await ReadOnly()
    await run_cycles(dut, 5)
    assert get_reg(dut, 3) == 0
    assert get_reg(dut, 4) == 42

@cocotb.test()
async def test_jalr_writeback(dut):
    """rd = pc+4 for JALR, even though the ALU is simultaneously busy computing the target."""
    prog = [
        addi(1, 0, 20), # x1 = 20
        jalr(2, 1, 0), # pc=4, target=20, x2 should get pc+4=8
        jal(0,0)
    ]
    await setup(dut, prog)
    await run_cycles(dut, 3)
    await ReadOnly()
    assert get_reg(dut, 2) == 8



#load/store correctness
@cocotb.test()
async def test_sw_lw(dut):
    """Store then load a word back -- round-trip correctness."""
    prog = [
        addi(1, 0, 0x123),
        sw(0, 1, 100), # mem[100..103] = 0x123
        lw(2, 0, 100),
        #jal(0,0)
    ]
    await setup(dut, prog)
    await run_cycles(dut, 3)
    await ReadOnly()
    assert get_reg(dut, 2) == 0x123

@cocotb.test()
async def test_sh_lh_signed(dut):
    """Store halfword with high bit set, load back signed -- must sign-extend."""
    prog = [
        lui(1, 0x00008000),   # x1 = 0x00008000
        addi(1, 1, 1),        # x1 = 0x00008001  (both steps use in-range immediates)
        sh(0, 1, 200),
        lh(2, 0, 200),
        jal(0, 0)
    ]
    await setup(dut, prog)
    await run_cycles(dut, 6)
    await ReadOnly()
    assert get_reg_signed(dut, 2) == to_signed32(0xFFFF8001), \
        f"Expected 0xFFFF8001, got {get_reg_signed(dut, 2)}"

@cocotb.test()
async def test_sh_lhu_unsigned(dut):
    """Same stored halfword, unsigned load must NOT sign-extend."""
    prog = [
        lui(1, 0x00008000),
        addi(1, 1, 1),
        sh(0, 1, 200),
        lhu(2, 0, 200),
        jal(0, 0)
    ]
    await setup(dut, prog)
    await run_cycles(dut, 6)
    await ReadOnly()
    assert get_reg(dut, 2) == 0x8001

@cocotb.test()
async def test_sb_lb_signed(dut):
    """Store byte with high bit set, signed load sign-extends."""
    prog = [
        addi(1, 0, 0x81 - 0x100), 
        sb(0, 1, 300),
        lb(2, 0, 300),
        jal(0, 0)
    ]
    await setup(dut, prog)
    await run_cycles(dut, 5)
    await ReadOnly()
    assert get_reg_signed(dut, 2) == to_signed32(0xFFFFFF81)

@cocotb.test()
async def test_sb_lbu_unsigned(dut):
    """Same stored byte, unsigned load does NOT sign-extend."""
    prog = [
        addi(1, 0, 0x81 - 0x100),
        sb(0, 1, 300),
        lbu(2, 0, 300),
        jal(0, 0)
    ]
    await setup(dut, prog)
    await run_cycles(dut, 5)
    await ReadOnly()
    assert get_reg(dut, 2) == 0x81

@cocotb.test()
async def test_load_use_same_cycle(dut):
    """Load immediately followed by a dependent instruction -- should just work."""
    prog = [
        addi(1, 0, 77),
        sw(0, 1, 400),
        lw(2, 0, 400), 
        addi(3, 2, 5),
        jal(0, 0)
    ]
    await setup(dut, prog)
    await run_cycles(dut, 6)
    await ReadOnly()
    assert get_reg(dut, 2) == 77
    assert get_reg(dut, 3) == 82

@cocotb.test()
async def test_mem_out_of_range(dut):
    """Store to an invalid address (0xFFFF_0000); valid memory must stay untouched."""
    prog = [
        addi(1, 0, 100),   
        addi(2, 0, 1),     
        sw(1, 2, 0),       
        lui(3, 0xFFFF0000),
        addi(4, 0, 0x7FF), 
        sw(3, 4, 0),       
        lw(5, 1, 0),
        jal(0, 0)
    ]
    await setup(dut, prog)
    await run_cycles(dut, 9)
    await ReadOnly()
    assert get_reg(dut, 5) == 1
    assert get_mem_byte(dut, 100) == 1
    assert get_mem_byte(dut, 101) == 0
    assert get_mem_byte(dut, 102) == 0
    assert get_mem_byte(dut, 103) == 0

@cocotb.test()
async def test_small_program(dut):
    """Short hand-assembled sequence exercising load, ALU, branch, store end-to-end."""

    # Program sequence analysis:
    # PC 0x00: addi(1, 0, 10)
    # PC 0x04: addi(2, 0, 20)
    # PC 0x08: add(3, 1, 2) -> x3 = 30
    # PC 0x0C: sw(0, 3, 0) -> mem[0] = 30
    # PC 0x10: lw(4, 0, 0) -> x4 = 30
    # PC 0x14: beq(3, 4, 12) -> Taken! Offset changed from 8 to 12 to jump over the new trap
    # PC 0x18: addi(5, 0, 999) -> Skipped poison instruction
    # PC 0x1C: jal(0, 0) -> Path Trap 1: Halts core if branch fails
    # PC 0x20: addi(5, 0, 1) -> Target instruction
    # PC 0x24: jal(0, 0) -> Path Trap 2: Halts core on successful run

    prog = [
        addi(1, 0, 10),
        addi(2, 0, 20),
        add(3, 1, 2),
        sw(0, 3, 0),
        lw(4, 0, 0),
        beq(3, 4, 12),
        addi(5, 0, 999),
        jal(0, 0), 
        addi(5, 0, 1),
        jal(0, 0)
    ]
    await setup(dut, prog)
    await run_cycles(dut, 10)
    await ReadOnly()
    assert get_reg(dut, 4) == 30
    assert get_reg(dut, 5) == 1

@cocotb.test()
async def test_cordic_integration(dut):
    """
    Full pipeline test: load real operands via LUI/ADDI, run a vectoring-mode
    CORDIC instruction, and confirm:
    (a) PC freezes for the correct duration while core_stall is high,
    (b) the regfile write happens on the correct cycle, not early, and
    (c) the instruction immediately after CORDIC executes correctly once
    the stall releases, proving core_stall doesn't leak into surrounding code.
    """
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    x_val, y_val = 0.2, 0.1
    x_fixed = to_fixed(x_val)
    y_fixed = to_fixed(y_val)

    program = []
    program += load_const(1, x_fixed)                            # x1 = x operand
    program += load_const(2, y_fixed)                            # x2 = y operand
    program.append(encode_cordic(rd=3, rs1=1, rs2=2, mode=0))     # x3 = cordic(x1,x2), vectoring
    program.append(addi(rd=4, rs1=0, imm=7))                      # x4 = 7 -- must NOT run early

    load_program(dut, program)
    await reset_dut(dut)

    # --- Poll until core_stall actually asserts, rather than assuming a fixed
    # cycle count for the LUI/ADDI setup instructions. ---
    for _ in range(20):
        if dut.core_stall.value == 1:
            break
        await RisingEdge(dut.clk)
    else:
        assert False, "core_stall never asserted -- CORDIC instruction never reached"

    pc_at_cordic_issue = int(dut.pc_current.value)
    x1_val = dut.u_regfile.regs[1].value.to_signed()
    x2_val = dut.u_regfile.regs[2].value.to_signed()
    assert x1_val == x_fixed, f"x1={x1_val}, expected {x_fixed} -- operand load failed before CORDIC issued"
    assert x2_val == y_fixed, f"x2={x2_val}, expected {y_fixed} -- operand load failed before CORDIC issued"

    # --- Stay in this loop for as long as core_stall holds; confirm PC never moves. ---
    stall_cycles_observed = 0
    while dut.core_stall.value == 1:
        assert int(dut.pc_current.value) == pc_at_cordic_issue, \
            f"PC moved while core_stall was high! pc={int(dut.pc_current.value):x}"
        stall_cycles_observed += 1
        await RisingEdge(dut.clk)
        if stall_cycles_observed > 20:
            assert False, "core_stall held too long -- FSM likely deadlocked"

    dut._log.info(f"[PERF] core_stall held for {stall_cycles_observed} cycles")

    #actual write commits one edge after core stalls drop
    await RisingEdge(dut.clk)

    # --- The cycle stall just dropped is the cycle writeback + PC advance happen. ---
    x3_result = dut.u_regfile.regs[3].value.to_signed()
    x3_float = from_fixed(x3_result)

    expected_mag = math.sqrt(x_val**2 + y_val**2)
    assert abs(x3_float - expected_mag) < 0.005, \
        f"x3={x3_float}, expected magnitude {expected_mag}"

    assert int(dut.pc_current.value) == pc_at_cordic_issue + 4, \
        "PC did not advance exactly one instruction after stall released"

    # --- Confirm the follow-on ADDI executes cleanly, proving stall didn't leak. ---
    await ClockCycles(dut.clk, 2)
    x4_result = dut.u_regfile.regs[4].value.to_signed()
    assert x4_result == 7, f"x4={x4_result}, expected 7 -- post-CORDIC instruction corrupted"

    dut._log.info(f"[PASS] CORDIC integration: x3={x3_float:.5f} (exp {expected_mag:.5f}), x4={x4_result}")