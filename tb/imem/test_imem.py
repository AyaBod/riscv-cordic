import cocotb
from cocotb.triggers import Timer


@cocotb.test()
async def test_word_0(dut):
    """addr=0 should return the first instruction in the hex file."""
    dut.addr.value = 0
    await Timer(1, unit="ns")
    assert dut.instruction.value == 0x00500093, f"expected 0x00500093, got {dut.instruction.value}"
    pass


@cocotb.test()
async def test_word_1(dut):
    """addr=4 (byte address!) should return the SECOND instruction."""
    dut.addr.value = 4 #address are by 4s
    await Timer(1, unit="ns")
    assert dut.instruction.value == 0x00A00113, f"expected 0x00A00113, got {dut.instruction.value}"
    pass


@cocotb.test()
async def test_word_2(dut):
    """addr=8 should return the third instruction."""
    dut.addr.value = 8 #address are by 4s
    await Timer(1, unit="ns")
    assert dut.instruction.value == 0x002081B3, f"expected 0x002081B3, got {dut.instruction.value}"
    pass


@cocotb.test()
async def test_misaligned_or_unused_addr(dut):
    """An address past your loaded program (but still in range) should read
    whatever $readmemh left there -- typically 0 or X, since you only
    initialized 3 of 256 words. Decide what you expect and assert it."""
    # TODO: drive addr = 12 (word index 3, unloaded)
    # what does your array contain there? think about $readmemh behavior
    # for array entries the hex file didn't specify
    dut.addr.value = 12 #address are by 4s
    await Timer(1, unit="ns")
    assert dut.instruction.value == 0, f"expected nothing, got {dut.instruction.value}"
    pass