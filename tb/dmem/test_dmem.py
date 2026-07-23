import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


# input  logic clk,
# input  logic [31:0] addr,
# input  logic [31:0] write_data,
# input  logic mem_read,
# input  logic mem_write,
# input  logic [2:0]  funct3, //tells width and signed or nto
# output logic [31:0] read_data


@cocotb.test()
async def test_sw_then_lw(dut):
    """Store a word, read it back."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    dut.addr.value = 4
    dut.write_data.value = 0x12345678
    dut.mem_read.value = 0
    dut.funct3.value = 0b010 #store word
    dut.mem_write.value = 1

    #write is in always ff
    await RisingEdge(dut.clk)

    dut.mem_write.value = 0 

    #bc of gating
    dut.mem_read.value = 1 #addr and funct3 should  stay the same no chnages
    await Timer(1, unit="ns") #bc comb not ff
    assert dut.read_data.value == 0x12345678, f"expected 0x12345678, got {dut.read_data.value}"

    pass


@cocotb.test()
async def test_sb_then_lb_positive(dut):
    """Store a small positive byte, load it back signed with top bit 0"""

    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    dut.addr.value = 5
    dut.write_data.value = 23
    dut.mem_read.value = 0
    dut.funct3.value = 0b000  #store byte and load byte signed
    dut.mem_write.value = 1

    #write is in always ff
    await RisingEdge(dut.clk)

    dut.mem_write.value = 0 

    #bc of gating
    dut.mem_read.value = 1 #addr and funct3 should  stay the same no chnages
    await Timer(1, unit="ns") #bc comb not ff
    assert dut.read_data.value == 23, f"expected 23, got {dut.read_data.value}"

    pass


@cocotb.test()
async def test_sb_then_lb_negative(dut):
    """Store a byte with the top bit set to 1 load signed."""
    #sign extention test
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    dut.addr.value = 6
    dut.write_data.value = 0x80
    dut.mem_read.value = 0
    dut.funct3.value = 0b000  #store byte and load byte signed
    dut.mem_write.value = 1

    #write is in always ff
    await RisingEdge(dut.clk)

    dut.mem_write.value = 0 

    #bc of gating
    dut.mem_read.value = 1 #addr and funct3 should  stay the same no chnages
    await Timer(1, unit="ns") #bc comb not ff
    assert dut.read_data.value == 0xFFFFFF80, f"expected 0x80, got {dut.read_data.value}"


    pass


@cocotb.test()
async def test_sb_then_lbu(dut):
    """Same negative-looking byte as above but load unsigned"""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    dut.addr.value = 7
    dut.write_data.value = 0xFF #another neg byte
    dut.mem_read.value = 0
    dut.funct3.value = 0b000  #store byte and load byte signed
    dut.mem_write.value = 1

    #write is in always ff
    await RisingEdge(dut.clk)

    dut.mem_write.value = 0 

    #bc of gating
    dut.funct3.value = 0b100 #load unsigned byte
    dut.mem_read.value = 1 #addr should  stay the same no chnages
    await Timer(1, unit="ns") #bc comb not ff
    assert dut.read_data.value == 0x000000FF, f"expected 0xFF, got {dut.read_data.value}"
    pass


@cocotb.test()
async def test_sh_then_lh_negative(dut):
    """Halfword version of the sign-extension test."""

    #sign extention test
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    dut.addr.value = 8
    dut.write_data.value = 65000
    dut.mem_read.value = 0
    dut.funct3.value = 0b001  #store halfword and load halfword signed
    dut.mem_write.value = 1

    #write is in always ff
    await RisingEdge(dut.clk)

    dut.mem_write.value = 0 

    #bc of gating
    dut.mem_read.value = 1 #addr and funct3 should  stay the same no chnages
    await Timer(1, unit="ns") #bc comb not ff
    assert dut.read_data.value == 0xFFFFFDE8, f"expected 0xFFFFFDE8, got {dut.read_data.value}"
    pass


@cocotb.test()
async def test_byte_doesnt_disturb_neighbors(dut):
    """Store a full word, then store a SINGLE byte somewhere in the middle like addr+1, then read the word back, confirm the
    OTHER three bytes are untouched."""

    #sign extention test
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    dut.addr.value = 14
    dut.write_data.value = 0x12345678
    dut.mem_read.value = 0
    dut.funct3.value = 0b010  #store word
    dut.mem_write.value = 1

    #write is in always ff
    await RisingEdge(dut.clk)

    dut.mem_write.value = 0 

    await RisingEdge(dut.clk)

    dut.addr.value = 15
    dut.write_data.value = 5
    dut.funct3.value = 0b000
    dut.mem_write.value = 1

    await RisingEdge(dut.clk)

    dut.mem_write.value = 0

    #bc of gating
    dut.addr.value = 14
    dut.funct3.value = 0b010 #read corrupted word
    dut.mem_read.value = 1 
    await Timer(1, unit="ns") #bc comb not ff
    assert dut.read_data.value == 0x12340578 , f"expected 0x12340578 , got {dut.read_data.value}"

    pass


@cocotb.test()
async def test_mem_write_disabled(dut):
    """mem_write=0 where an attempted store should NOT change memory."""

    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    dut.addr.value = 31
    dut.write_data.value = 0x12345678
    dut.mem_read.value = 0
    dut.funct3.value = 0b010 #store word
    dut.mem_write.value = 0 #test if itll still write if mem write is off

    #write is in always ff
    await RisingEdge(dut.clk)

    dut.mem_write.value = 0 

    #bc of gating
    dut.mem_read.value = 1 #addr and funct3 should  stay the same no chnages
    await Timer(1, unit="ns") #bc comb not ff
    assert dut.read_data.value == 0, f"expected 0, got {dut.read_data.value}"


    pass


@cocotb.test()
async def test_mem_read_disabled(dut):
    """mem_read=0 where read_data should be 0."""

    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    dut.addr.value = 4
    dut.write_data.value = 0x12345678
    dut.mem_read.value = 0
    dut.funct3.value = 0b010 #store word
    dut.mem_write.value = 1

    #write is in always ff
    await RisingEdge(dut.clk)

    dut.mem_write.value = 0 

    #bc of gating
    dut.mem_read.value = 0 #test if itll still read if mem read is off
    await Timer(1, unit="ns") #bc comb not ff
    assert dut.read_data.value == 0, f"expected 0, got {dut.read_data.value}"

    pass