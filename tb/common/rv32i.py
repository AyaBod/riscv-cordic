"""rv32i + cordic instruction encoders and cocotb helpers.

shared by every testbench and by sw/check_encoding.py, so the python side and the
assembler side are checked against the same encoding table
"""

import math

# ---------------------------------------------------------------------------
# raw formats: fields go in, a 32-bit word comes out
# ---------------------------------------------------------------------------

def _r(funct7, rs2, rs1, funct3, rd, opcode):
    return ((funct7 & 0x7F) << 25) | ((rs2 & 0x1F) << 20) | ((rs1 & 0x1F) << 15) \
        | ((funct3 & 0x7) << 12) | ((rd & 0x1F) << 7) | (opcode & 0x7F)


def _i(imm, rs1, funct3, rd, opcode):
    return ((imm & 0xFFF) << 20) | ((rs1 & 0x1F) << 15) | ((funct3 & 0x7) << 12) \
        | ((rd & 0x1F) << 7) | (opcode & 0x7F)


def _s(imm, rs2, rs1, funct3, opcode):
    imm &= 0xFFF
    return ((imm >> 5) << 25) | ((rs2 & 0x1F) << 20) | ((rs1 & 0x1F) << 15) \
        | ((funct3 & 0x7) << 12) | ((imm & 0x1F) << 7) | (opcode & 0x7F)


def _b(imm, rs2, rs1, funct3, opcode=0b1100011):
    # imm is a byte offset, bit 0 is dropped (always 0)
    imm &= 0x1FFF
    return (((imm >> 12) & 1) << 31) | (((imm >> 5) & 0x3F) << 25) | ((rs2 & 0x1F) << 20) \
        | ((rs1 & 0x1F) << 15) | ((funct3 & 0x7) << 12) | (((imm >> 1) & 0xF) << 8) \
        | (((imm >> 11) & 1) << 7) | (opcode & 0x7F)


def _u(imm20, rd, opcode):
    return ((imm20 & 0xFFFFF) << 12) | ((rd & 0x1F) << 7) | (opcode & 0x7F)


def _j(imm, rd, opcode=0b1101111):
    imm &= 0x1FFFFF
    return (((imm >> 20) & 1) << 31) | (((imm >> 1) & 0x3FF) << 21) | (((imm >> 11) & 1) << 20) \
        | (((imm >> 12) & 0xFF) << 12) | ((rd & 0x1F) << 7) | (opcode & 0x7F)


# ---------------------------------------------------------------------------
# rv32i mnemonics
# ---------------------------------------------------------------------------
OP, OP_IMM, LOAD, STORE = 0b0110011, 0b0010011, 0b0000011, 0b0100011

def add(rd, rs1, rs2):  return _r(0x00, rs2, rs1, 0b000, rd, OP)
def sub(rd, rs1, rs2):  return _r(0x20, rs2, rs1, 0b000, rd, OP)
def sll(rd, rs1, rs2):  return _r(0x00, rs2, rs1, 0b001, rd, OP)
def slt(rd, rs1, rs2):  return _r(0x00, rs2, rs1, 0b010, rd, OP)
def sltu(rd, rs1, rs2): return _r(0x00, rs2, rs1, 0b011, rd, OP)
def xor(rd, rs1, rs2):  return _r(0x00, rs2, rs1, 0b100, rd, OP)
def srl(rd, rs1, rs2):  return _r(0x00, rs2, rs1, 0b101, rd, OP)
def sra(rd, rs1, rs2):  return _r(0x20, rs2, rs1, 0b101, rd, OP)
def or_(rd, rs1, rs2):  return _r(0x00, rs2, rs1, 0b110, rd, OP)
def and_(rd, rs1, rs2): return _r(0x00, rs2, rs1, 0b111, rd, OP)

def addi(rd, rs1, imm):  return _i(imm, rs1, 0b000, rd, OP_IMM)
def slti(rd, rs1, imm):  return _i(imm, rs1, 0b010, rd, OP_IMM)
def sltiu(rd, rs1, imm): return _i(imm, rs1, 0b011, rd, OP_IMM)
def xori(rd, rs1, imm):  return _i(imm, rs1, 0b100, rd, OP_IMM)
def ori(rd, rs1, imm):   return _i(imm, rs1, 0b110, rd, OP_IMM)
def andi(rd, rs1, imm):  return _i(imm, rs1, 0b111, rd, OP_IMM)
def slli(rd, rs1, sh):   return _i(sh & 0x1F, rs1, 0b001, rd, OP_IMM)
def srli(rd, rs1, sh):   return _i(sh & 0x1F, rs1, 0b101, rd, OP_IMM)
def srai(rd, rs1, sh):   return _i(0x400 | (sh & 0x1F), rs1, 0b101, rd, OP_IMM)   # imm[10] marks arithmetic

def lb(rd, rs1, imm):  return _i(imm, rs1, 0b000, rd, LOAD)
def lh(rd, rs1, imm):  return _i(imm, rs1, 0b001, rd, LOAD)
def lw(rd, rs1, imm):  return _i(imm, rs1, 0b010, rd, LOAD)
def lbu(rd, rs1, imm): return _i(imm, rs1, 0b100, rd, LOAD)
def lhu(rd, rs1, imm): return _i(imm, rs1, 0b101, rd, LOAD)

def sb(rs2, rs1, imm): return _s(imm, rs2, rs1, 0b000, STORE)
def sh(rs2, rs1, imm): return _s(imm, rs2, rs1, 0b001, STORE)
def sw(rs2, rs1, imm): return _s(imm, rs2, rs1, 0b010, STORE)

def beq(rs1, rs2, off):  return _b(off, rs2, rs1, 0b000)
def bne(rs1, rs2, off):  return _b(off, rs2, rs1, 0b001)
def blt(rs1, rs2, off):  return _b(off, rs2, rs1, 0b100)
def bge(rs1, rs2, off):  return _b(off, rs2, rs1, 0b101)
def bltu(rs1, rs2, off): return _b(off, rs2, rs1, 0b110)
def bgeu(rs1, rs2, off): return _b(off, rs2, rs1, 0b111)

def lui(rd, imm20):   return _u(imm20, rd, 0b0110111)    # imm20 = the upper 20 bits, not pre-shifted
def auipc(rd, imm20): return _u(imm20, rd, 0b0010111)
def jal(rd, off):     return _j(off, rd)
def jalr(rd, rs1, imm): return _i(imm, rs1, 0b000, rd, 0b1100111)

FENCE  = 0x0FF0000F       # fence iorw, iorw
ECALL  = 0x00000073
EBREAK = 0x00100073
NOP    = addi(0, 0, 0)
HALT   = jal(0, 0)        # jump-to-self, parks the pc so programs never run off the end


def load_const(rd, value):
    """any 32-bit constant in two instructions (lui + addi).
    addi sign-extends its 12 bits, so if bit 11 is set the upper part gets +1 to cancel it out"""
    value &= 0xFFFFFFFF
    upper = ((value + 0x800) >> 12) & 0xFFFFF
    lower = value - (upper << 12)
    lower = ((lower + 0x800) & 0xFFF) - 0x800    # wrap into -2048..2047
    return [lui(rd, upper), addi(rd, rd, lower)]


# ---------------------------------------------------------------------------
# cordic custom-0 encoding (must match core_top.sv and sw/cordic.h)
# ---------------------------------------------------------------------------
OPC_CUSTOM0 = 0b0001011
F3_CORDIC_MAG, F3_CORDIC_COS, F3_CORDIC_ATAN2, F3_CORDIC_SIN = 0b000, 0b001, 0b010, 0b011
CORDIC_MNEMONICS = {F3_CORDIC_MAG: "cordic.mag", F3_CORDIC_COS: "cordic.cos",
                    F3_CORDIC_ATAN2: "cordic.atan2", F3_CORDIC_SIN: "cordic.sin"}

def encode_cordic(rd, rs1, rs2, funct3):
    return _r(0, rs2, rs1, funct3, rd, OPC_CUSTOM0)

def cordic_cos(rd, rs1):        return encode_cordic(rd, rs1, 0, F3_CORDIC_COS)
def cordic_sin(rd, rs1):        return encode_cordic(rd, rs1, 0, F3_CORDIC_SIN)
def cordic_mag(rd, rs1, rs2):   return encode_cordic(rd, rs1, rs2, F3_CORDIC_MAG)
def cordic_atan2(rd, rs1, rs2): return encode_cordic(rd, rs1, rs2, F3_CORDIC_ATAN2)   # rs1 = x, rs2 = y


# ---------------------------------------------------------------------------
# fixed point
# ---------------------------------------------------------------------------
FRAC_BITS = 13

def to_fixed(x):
    """float -> q3.13 integer (rounded)"""
    return int(round(x * (1 << FRAC_BITS)))

def from_fixed(v):
    return v / (1 << FRAC_BITS)

def to_s32(v):
    v &= 0xFFFFFFFF
    return v - (1 << 32) if v & 0x80000000 else v

def to_s16(v):
    v &= 0xFFFF
    return v - (1 << 16) if v & 0x8000 else v


# ---------------------------------------------------------------------------
# cocotb dut helpers (imported lazily so sw/check_encoding.py runs without cocotb)
# ---------------------------------------------------------------------------
IMEM_WORDS = 256
DMEM_BYTES = 1024


def load_program(dut, program, halt=True):
    """poke words into imem, zero the rest. a HALT is appended so the pc parks instead of wrapping"""
    words = list(program) + ([HALT] if halt else [])
    assert len(words) <= IMEM_WORDS, f"program is {len(words)} words, imem holds {IMEM_WORDS}"
    words += [0] * (IMEM_WORDS - len(words))
    for i, w in enumerate(words):
        dut.u_imem.words[i].value = w & 0xFFFFFFFF


def clear_dmem(dut):
    for i in range(DMEM_BYTES):
        dut.u_dmem.mem[i].value = 0


async def reset_dut(dut, cycles=2):
    """hold rst_n low across a couple of edges (regfile reset is synchronous), release on a falling edge"""
    from cocotb.triggers import FallingEdge
    dut.rst_n.value = 0
    for _ in range(cycles):
        await FallingEdge(dut.clk)
    dut.rst_n.value = 1


async def run_cycles(dut, n):
    """n rising edges, then park on the falling edge so everything has settled before we sample"""
    from cocotb.triggers import RisingEdge, FallingEdge
    for _ in range(n):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)


def get_reg(dut, i):
    return 0 if i == 0 else int(dut.u_regfile.regs[i].value) & 0xFFFFFFFF

def get_reg_signed(dut, i):
    return to_s32(get_reg(dut, i))

def get_pc(dut):
    return int(dut.pc_current.value)

def read_dmem_word(dut, addr):
    b = [int(dut.u_dmem.mem[addr + k].value) & 0xFF for k in range(4)]
    return b[0] | (b[1] << 8) | (b[2] << 16) | (b[3] << 24)


def start_clock(dut, period_ns=10):
    import cocotb
    from cocotb.clock import Clock
    cocotb.start_soon(Clock(dut.clk, period_ns, units="ns").start())


async def boot(dut, program, cycles):
    """the usual test shape: load, reset, run, sample"""
    load_program(dut, program)
    await reset_dut(dut)
    await run_cycles(dut, cycles)
