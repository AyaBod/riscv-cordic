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
    # TODO: drive operand_a, operand_b, alu_op = ALU_ADD (0b0000)
    dut.operand_a.value = 0b0001
    dut.operand_b.value = 0b0001
    dut.alu_op.value = ALU_ADD
    # TODO: await Timer(1, unit="ns")
    await Timer(1, unit="ns")
    # TODO: assert result == expected sum
    assert int(dut.result.value) == 2, f"expected 2, got {dut.result.value.integer}"
    # bonus: try operand_a = 0xFFFFFFFF, operand_b = 1 -- what SHOULD wrap to?
    pass


@cocotb.test()
async def test_sub_producing_negative(dut):
    """SUB where result is negative -- check two's complement representation."""
    # TODO: e.g. operand_a = 5, operand_b = 10 -- result should be 0xFFFFFFFB (-5 in two's complement)
    dut.operand_a.value = 5
    dut.operand_b.value = 10
    dut.alu_op.value = ALU_SUB
    await Timer(1, unit="ns")
    assert dut.result.value.to_signed() == -5, f"expected -5, got {dut.result.value.to_signed()}"
    pass


@cocotb.test()
async def test_bitwise_ops(dut):
    """AND, OR, XOR with a pattern that would catch a logical/bitwise mixup."""
    # TODO: pick operand_a/b where bitwise vs logical AND/OR would give DIFFERENT
    # results -- e.g. two nonzero values that aren't simply 0/1.
    # if AND used && by mistake, what would result be instead of the correct value?
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
    """SLL, SRL, SRA -- include shift-by-0, shift-by-31, and shift amount > 31 in operand_b."""
    # TODO: SLL/SRL/SRA each need their own check
    # TODO: specifically test operand_b with garbage in bits above [4:0]
    # (e.g. operand_b = 32'hFFFFFFE1 -- lower 5 bits = 1, upper bits garbage)
    # to prove your slicing actually works
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
    # TODO: operand_a = 0x80000000 (most negative 32-bit value), shift right arithmetic
    # by some amount, check the upper bits fill with 1, not 0
    # TODO: also test SRL with the same operand_a -- should fill with 0 instead
    # this pair is the actual proof that your signed cast is doing its job

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
    """The critical case: SLT and SLTU must DIVERGE on this input."""
    # TODO: pick operand_a/b where one is 'negative' as signed but a huge
    # positive number as unsigned -- e.g. operand_a = 0xFFFFFFFF (-1 signed,
    # 4294967295 unsigned), operand_b = 1
    # SLT(operand_a, operand_b) should be TRUE (-1 < 1)
    # SLTU(operand_a, operand_b) should be FALSE (4294967295 is not < 1)
    # if your ALU had the signed-cast bug from earlier, this test would catch it

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
    # TODO: e.g. SUB with operand_a == operand_b -> result 0, zero should be 1
    # TODO: any op producing nonzero -> zero should be 0

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
    # TODO: drive alu_op = 0b1111 (unused encoding)
    # TODO: check result == 0 (or whatever your default produces) --
    # this proves you don't have the latch-inference bug
    dut.operand_a.value = 5
    dut.operand_b.value = 5
    dut.alu_op.value = 0b1111
    await Timer(1, unit="ns")
    assert dut.result.value.integer == 0, f"expected 0, got {dut.result.value.integer}"

    
    pass