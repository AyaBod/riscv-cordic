"""standalone cordic unit tests: handshake timing, rotation (sin/cos), vectoring (mag/atan2), documented limits"""

import math

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge

from rv32i import to_fixed, from_fixed, to_s16

ITER = 12
ROT, VEC = 1, 0


async def setup(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.start.value = 0
    dut.mode_in.value = 0
    dut.x_in.value = dut.y_in.value = dut.z_in.value = 0
    dut.rst_n.value = 0
    await FallingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst_n.value = 1


async def run_op(dut, mode, x, y, z):
    """pulse start for one cycle, wait for done, return (x, y, z) as floats and the cycle count"""
    dut.mode_in.value = mode
    dut.x_in.value = to_fixed(x) & 0xFFFF
    dut.y_in.value = to_fixed(y) & 0xFFFF
    dut.z_in.value = to_fixed(z) & 0xFFFF
    dut.start.value = 1
    await FallingEdge(dut.clk)
    dut.start.value = 0
    cycles = 1
    while not int(dut.done.value):
        await FallingEdge(dut.clk)
        cycles += 1
        assert cycles < 50, "done never came"
    out = tuple(from_fixed(to_s16(int(s.value))) for s in (dut.x_out, dut.y_out, dut.z_out))
    await FallingEdge(dut.clk)                 # let it drop back to IDLE
    return out, cycles


@cocotb.test()
async def test_handshake_timing(dut):
    """busy rises the cycle after start, done is a single pulse after ITERATIONS steps, then back to idle"""
    await setup(dut)
    assert int(dut.busy.value) == 0 and int(dut.done.value) == 0
    dut.mode_in.value = ROT
    dut.x_in.value = to_fixed(1.0)
    dut.z_in.value = to_fixed(0.5)
    dut.start.value = 1
    await FallingEdge(dut.clk)
    dut.start.value = 0
    busy_cycles, done_cycles = 0, 0
    for _ in range(ITER + 1):
        busy_cycles += int(dut.busy.value)
        done_cycles += int(dut.done.value)
        await FallingEdge(dut.clk)
    assert busy_cycles == ITER + 1, f"busy for {busy_cycles} cycles"   # 12 iterate + 1 done
    assert done_cycles == 1, "done should pulse exactly once"
    assert int(dut.busy.value) == 0, "didn't return to idle"


@cocotb.test()
async def test_rotation_sin_cos(dut):
    """start at (1, 0), rotate by theta -> (cos, sin) across the whole usable range"""
    await setup(dut)
    worst = 0.0
    for k in range(-15, 16):
        theta = k * 0.1
        (c, s, z), _ = await run_op(dut, ROT, 1.0, 0.0, theta)
        err = max(abs(c - math.cos(theta)), abs(s - math.sin(theta)))
        worst = max(worst, err)
        assert err < 0.002, f"theta={theta:+.2f}: cos {c:.4f} sin {s:.4f}"
        assert abs(z) < 0.002, f"residual angle {z} didn't converge"
    dut._log.info(f"rotation worst error {worst:.5f}")


@cocotb.test()
async def test_vectoring_mag_atan2(dut):
    """rotate (x, y) onto the x axis -> x = magnitude, z = atan2(y, x)"""
    await setup(dut)
    cases = [(0.5, 0.0), (0.5, 0.5), (0.5, -0.5), (1.0, 0.25), (0.3, -0.9), (1.5, 1.5), (0.1, 0.1), (2.0, -1.0)]
    for x, y in cases:
        (m, yr, a), _ = await run_op(dut, VEC, x, y, 0.0)
        assert abs(m - math.hypot(x, y)) < 0.002, f"mag({x},{y}) = {m:.4f}"
        assert abs(a - math.atan2(y, x)) < 0.006, f"atan2({y},{x}) = {a:.4f}"
        assert abs(yr) < 0.01, f"y didn't go to 0: {yr}"


@cocotb.test()
async def test_documented_limits(dut):
    """pins the limits listed in the readme: 1.5 rad is fine, 2.0 rad is past the ~1.74 rad convergence range"""
    await setup(dut)
    (c, s, _), _ = await run_op(dut, ROT, 1.0, 0.0, 1.5)
    assert abs(s - math.sin(1.5)) < 0.002 and abs(c - math.cos(1.5)) < 0.002
    (c, s, _), _ = await run_op(dut, ROT, 1.0, 0.0, 2.0)
    assert abs(c - math.cos(2.0)) > 0.1, "2.0 rad unexpectedly converged, update the readme limits"
    # vectoring needs x > 0: a left-half-plane vector comes back with the wrong angle
    (_, _, a), _ = await run_op(dut, VEC, -0.5, 0.5, 0.0)
    assert abs(a - math.atan2(0.5, -0.5)) > 0.3, "negative x unexpectedly worked, update the readme limits"
