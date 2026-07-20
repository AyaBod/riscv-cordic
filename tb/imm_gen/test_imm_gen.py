import cocotb
from cocotb.triggers import Timer


@cocotb.test()
async def test_itype_addi_positive(dut):
    """addi x1, x0, 5 - imm[11:0] = 000000000101, positive, no sign-extend needed."""
    dut.instruction.value = 0x00500093
    await Timer(1, unit="ns")
    assert dut.imm_out.value == 5, f"expected 5, got {dut.imm_out.value}"
    pass


@cocotb.test()
async def test_itype_addi_negative(dut):
    """addi x1, x0, -1 - imm[11:0] = all 1s. This is the sign-extension proof for I-type."""
    # opcode=0010011, funct3=000, rd=00001, rs1=00000, imm=111111111111 (-1 in 12-bit two's complement)
    # imm[11:0] | rs1 | funct3 | rd | opcode)
    # 1111 1111 1111 0000 0000 0000 1001 0011
    dut.instruction.value = 0xFFF00093
    await Timer(1, unit="ns")
    assert dut.imm_out.value == 0xFFFFFFFF, f"expected 0xFFFFFFFF, got {dut.imm_out.value}"
    #expected imm_out = first 12 bits with sign extension
    pass


@cocotb.test()
async def test_stype_negative_offset(dut):
    """sw x2, -4(x1) - store with a negative offset, proves S-type reassembly + sign-extend."""
    # -4 (12-bit: 111111111100) 
    dut.instruction.value = 0xFE20AE23
    await Timer(1, unit="ns")
    assert dut.imm_out.value == 0xFFFFFFFC, f"expected 0xFFFFFFFC, got {dut.imm_out.value}" #-4 signed extended to 32 bits
    pass


@cocotb.test()
async def test_btype_negative_offset(dut):
    """A backward branch (negative offset) - proves B-type's scrambled reassembly."""
    dut.instruction.value = 0xFE000CE3
    await Timer(1, units="ns")
    #-8 sign-extended to 32 bits (0xFFFFFFF8)
    assert dut.imm_out.value == 0xFFFFFFF8, f"Expected 0xFFFFFFF8, got {hex(dut.imm_out.value)}"
    pass


@cocotb.test()
async def test_utype_lui(dut):
    """lui x1, 0x12345 - U-type just needs the upper bits placed correctly, no sign-extend logic."""
    # opcode=0110111, imm[31:12]=0x12345, rd=00001
    # 0x12345 00001 0110111
    # 0001 0010 0011 0100 0101 0000 1011 0111
    # expected imm_out = 0x12345000
    dut.instruction.value = 0x123450B7
    await Timer(1, unit="ns")
    assert dut.imm_out.value == 0x12345000, f"expected 0x12345000, got {dut.imm_out.value}"
    pass


@cocotb.test()
async def test_jtype_negative_offset(dut):
    """A backward jump - proves J-type's scrambled reassembly"""
    dut.instruction.value = 0xFF5FF0EF
    await Timer(1, units="ns")
    #12 sign-extended to 32 bits (0xFFFFFFF4)
    assert dut.imm_out.value == 0xFFFFFFF4, f"Expected 0xFFFFFFF4, got {hex(dut.imm_out.value)}"
    pass


@cocotb.test()
async def test_rtype_no_immediate(dut):
    """R-type has no immediate field -- module correctly outputs 0."""
    dut.instruction.value = 0x003100B3
    await Timer(1, units="ns")
    assert dut.imm_out.value == 0, f"Expected 0, got {dut.imm_out.value}"

    pass


@cocotb.test()
async def test_default_unused_opcode(dut):
    """Unused/unimplemented opcode should hit default branch, not produce garbage."""
    dut.instruction.value = 0xFFFFFFFF
    await Timer(1, units="ns")
    assert dut.imm_out.value == 0, f"Expected 0 from default branch, got {dut.imm_out.value}"
    pass