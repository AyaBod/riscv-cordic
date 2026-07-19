import cocotb
from cocotb.triggers import Timer


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
async def test_add(dut):
    """Basic ADD, including a case that overflows 32 bits (check wraparound)."""
    dut.operand_a.value = 0b0001
    dut.operand_b.value = 0b0001
    dut.alu_op.value = ALU_ADD
    await Timer(1, unit="ns")
    assert int(dut.result.value) == 2, f"expected 2, got {dut.result.value.integer}"

    pass


@cocotb.test()
async def test_sub_producing_negative(dut):
    """SUB where result is negative -- check two's complement representation."""
    dut.operand_a.value = 5
    dut.operand_b.value = 10
    dut.alu_op.value = ALU_SUB
    await Timer(1, unit="ns")
    assert dut.result.value.to_signed() == -5, f"expected -5, got {dut.result.value.to_signed()}"
    pass


@cocotb.test()
async def test_bitwise_ops(dut):
    """AND, OR, XOR with a pattern that would catch a logical/bitwise mixup."""
    dut.operand_a.value = 0b0101
    dut.operand_b.value = 0b0011
    
    dut.alu_op.value = ALU_AND
    await Timer(1, unit="ns")
    assert dut.result.value == 0b0001, f"expected 0b0001, got {dut.result.value.binstr}" #.binstr to get binary value
    
    dut.alu_op.value = ALU_OR
    await Timer(1, unit="ns")
    assert dut.result.value == 0b0111, f"expected 0b0111, got {dut.result.value.binstr}" #.binstr to get binary value
    
    dut.alu_op.value = ALU_XOR
    await Timer(1, unit="ns")
    assert dut.result.value == 0b0110, f"expected 0b0110, got {dut.result.value.binstr}" #.binstr to get binary value

    pass


@cocotb.test()
async def test_shifts(dut):
    """SLL, SRL, SRA include shift-by-0, shift-by-31, and shift amount > 31 in operand_b."""
    dut.operand_a.value = 0x80000003 #0011
    dut.operand_b.value = 0xFFFFFFE0 #zero shift
    dut.alu_op.value = ALU_SLL
    await Timer(1, unit="ns")
    assert dut.result.value == 0x80000003, f"expected 0x80000003, got {dut.result.value.binstr}"

    dut.operand_b.value = 0xFFFFFFE1 #1 shift 1111 1111 1111 1111 1111 1111 1110 [0001] only care abt last 4
    dut.alu_op.value = ALU_SLL  #0110
    await Timer(1, unit="ns")
    assert dut.result.value == 0x00000006, f"expected 0x00000006, got {dut.result.value.binstr}"

    dut.alu_op.value = ALU_SRL  #0001
    await Timer(1, unit="ns")
    assert dut.result.value == 0x40000001, f"expected 0x40000001, got {dut.result.value.binstr}"

    dut.alu_op.value = ALU_SRA  #0001
    await Timer(1, unit="ns")
    assert dut.result.value == 0xC0000001, f"expected 0xC0000001, got {dut.result.value.binstr}"
    pass


@cocotb.test()
async def test_sra_sign_extension(dut):
    """SRA specifically needs a NEGATIVE operand_a to prove sign-extension works."""
    dut.operand_a.value = 0x80000000
    dut.operand_b.value = 0xFFFFFFE1
    dut.alu_op.value = ALU_SRA
    await Timer(1, unit="ns")
    assert dut.result.value == 0xC0000000, f"expected 0xC0000000 got {dut.result.value.binstr}"

    dut.alu_op.value = ALU_SRL
    await Timer(1, unit="ns")
    assert dut.result.value == 0x40000000, f"expected 0x40000000 got {dut.result.value.binstr}" 

    pass


@cocotb.test()
async def test_slt_vs_sltu(dut):
    """SLT and SLTU must diverge on this input."""
    dut.operand_a.value = 0xFFFFFFFF
    dut.operand_b.value = 0x00000001

    dut.alu_op.value = ALU_SLT
    await Timer(1, units="ns")  # Wait for combinational logic settling
    assert dut.result.value == 1, f"expected 1, got {dut.result.value.integer}"

    dut.alu_op.value = ALU_SLTU
    await Timer(1, units="ns")
    assert dut.result.value == 0, f"expected 0, got {dut.result.value.integer}"

    pass


@cocotb.test()
async def test_zero_flag(dut):
    """Confirm the zero output correctly reflects result == 0."""
    dut.operand_a.value = 5
    dut.operand_b.value = 5
    dut.alu_op.value = ALU_SUB
    await Timer(1, unit="ns")
    assert dut.zero.value == 1, f"expected zero to be true (1), got {dut.zero.value}"

    dut.alu_op.value = ALU_ADD
    await Timer(1, unit="ns")
    assert dut.zero.value == 0, f"expected zero to be true (1), got {dut.zero.value}"

    pass


@cocotb.test()
async def test_default_case(dut):
    """Undefined alu_op encoding should hit your default branch, not latch."""
    dut.operand_a.value = 5
    dut.operand_b.value = 5
    dut.alu_op.value = 0b1111
    await Timer(1, unit="ns")
    assert dut.result.value.integer == 0, f"expected 0, got {dut.result.value.integer}"

    
    pass