import cocotb
from cocotb.triggers import Timer

#let tb know alu_ops
ALU_ADD = 0b0000
ALU_SUB = 0b0001
ALU_AND = 0b0010
ALU_OR = 0b0011
ALU_XOR = 0b0100
ALU_SLL = 0b0101
ALU_SRL = 0b0110
ALU_SRA = 0b0111 
ALU_SLT = 0b1000
ALU_SLTU = 0b1001 

@cocotb.test()
async def test_rtype_add(dut):
    """add: opcode=0110011, funct3=000, funct7[5]=0 -> ADD"""
    dut.opcode.value = 0b0110011
    dut.funct3.value = 000
    dut.funct7.value = 0000000

    await Timer(1, unit="ns")
    assert dut.reg_write.value == 1, f"expected reg_write=1, got {dut.reg_write.value}"
    assert dut.alu_src.value == 0, f"expected alu_src=0, got {dut.alu_src.value}"
    assert dut.alu_op.value == ALU_ADD, f"expected alu_op=ADD, got {dut.alu_op.value}"
    assert dut.mem_read.value == 0
    assert dut.mem_write.value == 0
    assert dut.mem_to_reg.value == 0
    assert dut.is_branch.value == 0
    assert dut.is_jump.value == 0
        
    pass


@cocotb.test()
async def test_rtype_sub(dut):
    """sub: same opcode/funct3 as add, but funct7[5]=1 -> SUB."""
    #if add passes but sub fails funct 7 isnt being checked properly
    dut.opcode.value = 0b0110011
    dut.funct3.value = 0b000
    dut.funct7.value = 0b0100000 

    await Timer(1, units="ns")

    assert dut.reg_write.value == 1
    assert dut.alu_src.value == 0
    assert dut.alu_op.value == ALU_SUB, f"expected alu_op=SUB, got {dut.alu_op.value}"
    assert dut.mem_read.value == 0
    assert dut.mem_write.value == 0
    assert dut.is_branch.value == 0
    assert dut.is_jump.value == 0

    pass


@cocotb.test()
async def test_rtype_and(dut):
    """and."""
    dut.opcode.value = 0b0110011
    dut.funct3.value = 0b111
    dut.funct7.value = 0b0000000

    await Timer(1, units="ns")

    assert dut.reg_write.value == 1
    assert dut.alu_src.value == 0
    assert dut.alu_op.value == ALU_AND, f"expected alu_op=AND, got {dut.alu_op.value}"
    assert dut.mem_read.value == 0
    assert dut.mem_write.value == 0
    pass


@cocotb.test()
async def test_itype_srai_vs_srli(dut):
    """srai vs srli: same opcode/funct3(101), differ only by funct7[5]"""

    # srli
    dut.opcode.value = 0b0010011
    dut.funct3.value = 0b101
    dut.funct7.value = 0b0000000
    await Timer(1, units="ns")
    assert dut.alu_op.value == ALU_SRL, f"expected SRL, got {dut.alu_op.value}"
    assert dut.alu_src.value == 1

    # srai
    dut.funct7.value = 0b0100000 #
    await Timer(1, units="ns")
    assert dut.alu_op.value == ALU_SRA, f"expected SRA, got {dut.alu_op.value}"
    assert dut.alu_src.value == 1

    pass


@cocotb.test()
async def test_load(dut):
    """lw: reg_write=1, alu_src=1, mem_read=1, mem_to_reg=1, mem_write=0"""
    dut.opcode.value = 0b0000011
    dut.funct3.value = 0b010  #lw
    dut.funct7.value = 0b0000000

    await Timer(1, units="ns")

    assert dut.reg_write.value == 1
    assert dut.alu_src.value == 1
    assert dut.alu_op.value == ALU_ADD
    assert dut.mem_read.value == 1
    assert dut.mem_write.value == 0
    assert dut.mem_to_reg.value == 1
    assert dut.is_branch.value == 0
    assert dut.is_jump.value == 0 

    pass


@cocotb.test()
async def test_store(dut):
    """sw: reg_write=0 (!), alu_src=1, mem_write=1, mem_read=0"""
    dut.opcode.value = 0b0100011
    dut.funct3.value = 0b010  #sw
    dut.funct7.value = 0b0000000

    await Timer(1, units="ns")

    assert dut.reg_write.value == 0, "stores shouldnt write to the register file :("
    assert dut.alu_src.value == 1
    assert dut.alu_op.value == ALU_ADD
    assert dut.mem_read.value == 0
    assert dut.mem_write.value == 1
    assert dut.is_branch.value == 0
    assert dut.is_jump.value == 0

    pass


@cocotb.test()
async def test_branch_beq(dut):
    """beq: reg_write=0, alu_src=0, is_branch=1, alu_op selects SUB"""
    dut.opcode.value = 0b1100011
    dut.funct3.value = 0b000 #beq
    dut.funct7.value = 0b0000000

    await Timer(1, units="ns")

    assert dut.reg_write.value == 0
    assert dut.alu_src.value == 0
    assert dut.alu_op.value == ALU_SUB, "branches should use SUB/comparison ops"
    assert dut.mem_read.value == 0
    assert dut.mem_write.value == 0
    assert dut.is_branch.value == 1
    assert dut.is_jump.value == 0

    pass


@cocotb.test()
async def test_jal(dut):
    """jal: reg_write=1, is_jump=1"""
    dut.opcode.value = 0b1101111
    dut.funct3.value = 0b000
    dut.funct7.value = 0b0000000

    await Timer(1, units="ns")

    assert dut.reg_write.value == 1
    assert dut.is_jump.value == 1
    assert dut.is_branch.value == 0
    assert dut.mem_write.value == 0
    pass


@cocotb.test()
async def test_default_unused_opcode(dut):
    """Unused opcode -> everything falls back to safe defaults, no latch."""
    dut.opcode.value = 0b1111111 
    dut.funct3.value = 0b111
    dut.funct7.value = 0b1111111
    await Timer(1, units="ns")

    assert dut.reg_write.value == 0
    assert dut.alu_src.value == 0
    assert dut.mem_read.value == 0
    assert dut.mem_write.value == 0
    assert dut.is_branch.value == 0
    assert dut.is_jump.value == 0
    pass