import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb.triggers import ReadOnly  #read is in comb block so happens instantly, wait till bits settle


async def reset_dut(dut):
    """apply reset for a couple of cycles"""
    dut.rst.value = 1
    dut.we.value = 0
    dut.rs1_addr.value = 0
    dut.rs2_addr.value = 0
    dut.rd_addr.value = 0
    dut.rd_data.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)


@cocotb.test()
async def test_reset_clears_all_regs(dut):
    """after reset, every register should read back as 0"""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)

    for i in range(32): #0-31
        dut.rs1_addr.value = i  
        assert int(dut.rs1_data.value) == 0, f"expected 0, got {dut.rs1_data.value}"
    pass


@cocotb.test()
async def test_x0_always_reads_zero(dut):
    """x0 must read 0 even if you attempt to write to it"""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)

    dut.rd_data.value = 0xDEADBEEF #haha
    #rd_addr already set 
    dut.we.value = 1
    await RisingEdge(dut.clk)
    dut.rs1_addr.value = 0
    assert int(dut.rs1_data.value) == 0, f"expected 0, got {dut.rs1_data.value}"

    pass


@cocotb.test()
async def test_write_then_read(dut):
    """basic write, then read back the same register"""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)


    dut.rd_data.value = 0x12345678
    dut.rd_addr.value = 5
    dut.we.value = 1
    await RisingEdge(dut.clk)
    dut.we.value = 0
    dut.rs1_addr.value = 5
    await ReadOnly()
    assert dut.rs1_data.value == 0x12345678, f"expected 0x12345678, got {dut.rs1_data.value}"
    
    pass


@cocotb.test()
async def test_two_reads_simultaneously(dut):
    """confirm both read ports work independently and combinationally"""
    dut = dut
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)


    dut.rd_addr.value = 3
    dut.rd_data.value = 0xAAAA
    dut.we.value = 1
    await RisingEdge(dut.clk)   #write
    dut.we.value = 0
    dut.rd_addr.value = 7
    dut.rd_data.value = 0xBBBB
    dut.we.value = 1
    await RisingEdge(dut.clk)   #write
    dut.we.value = 0

    dut.rs1_addr.value = 3
    dut.rs2_addr.value = 7

    await ReadOnly()

    assert (
        dut.rs1_data.value == 0xAAAA and dut.rs2_data.value == 0xBBBB
    ), f"expected 0xAAAA and 0xBBBB, got {dut.rs1_data.value} and {dut.rs2_data.value}"


    pass


@cocotb.test()
async def test_write_disabled_when_we_low(dut):
    """if we=0, a write attempt should NOT change the register"""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)

    dut.we.value = 0
    dut.rd_addr.value = 10
    dut.rd_data.value = 0xFFFFFFFF
    await RisingEdge(dut.clk)
    dut.rs1_addr.value = 10

    assert dut.rs1_data.value == 0, f"expected 0, got {dut.rs1_data.value}"
    pass