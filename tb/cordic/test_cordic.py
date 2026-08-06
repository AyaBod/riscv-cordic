import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles
import math

WIDTH = 16
FRAC_BITS = 13
ITERATIONS = 12
TOLERANCE = 0.002  


def to_fixed(val: float) -> int:
    """Convert a float to Q3.13 fixed-point, as a signed 16-bit int."""
    scaled = int(round(val * (1 << FRAC_BITS)))
    return scaled & 0xFFFF


def from_fixed(val: int) -> float:
    """Convert a signed 16-bit Q3.13 value back to float."""
    val = val & 0xFFFF
    if val & 0x8000:
        val -= 0x10000
    return val / (1 << FRAC_BITS)


async def reset_dut(dut):
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 3)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


async def run_cordic(dut, mode: int, x: float, y: float, z: float):
    """
    Drives one CORDIC operation and returns (x_out, y_out, z_out) as floats.
    mode=1 -> rotation mode, mode=0 -> vectoring mode.
    Shared by both rotation and vectoring tests since the handshake is identical --
    only the interpretation of inputs/outputs differs by mode.
    """
    dut.mode_in.value = mode
    dut.x_in.value = to_fixed(x)
    dut.y_in.value = to_fixed(y)
    dut.z_in.value = to_fixed(z)

    dut.start.value = 1
    await RisingEdge(dut.clk)   # this edge carries IDLE -> ITERATE transition
    dut.start.value = 0

    # Poll for done with a generous watchdog window. We already proved the exact
    # cycle count (ITERATIONS + 1) in the earlier debugging pass, so a loose
    # timeout here is just a safety net, not the primary correctness check.
    for _ in range(ITERATIONS + 5):
        await RisingEdge(dut.clk)
        if dut.done.value == 1:
            break
    else:
        assert False, f"done never asserted (mode={mode}, x={x}, y={y}, z={z})"

    x_out = from_fixed(dut.x_out.value.signed_integer)
    y_out = from_fixed(dut.y_out.value.signed_integer)
    z_out = from_fixed(dut.z_out.value.signed_integer)
    return x_out, y_out, z_out


@cocotb.test()
async def test_rotation_multiple_angles(dut):
    """
    Rotation mode across several angles, including negative (exercises the
    other shift_dir branch) and 0 (edge case -- should converge almost trivially).
    Kept within -80..80 degrees: CORDIC's arctan table sums to ~99.7 degrees max,
    so staying well inside that range avoids running near the convergence boundary.
    """
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)

    test_angles_deg = [-60, -30, 0, 30, 45, 80]

    for angle_deg in test_angles_deg:
        angle_rad = math.radians(angle_deg)

        # Rotation mode: x_in = 1.0 (DUT's INV_GAIN compensates the CORDIC
        # gain internally), y_in = 0, z_in = target angle
        x_out, y_out, _ = await run_cordic(dut, mode=1, x=1.0, y=0.0, z=angle_rad)

        expected_x = math.cos(angle_rad)
        expected_y = math.sin(angle_rad)

        assert abs(x_out - expected_x) < TOLERANCE, \
            f"[{angle_deg}deg] x_out={x_out}, expected {expected_x}"
        assert abs(y_out - expected_y) < TOLERANCE, \
            f"[{angle_deg}deg] y_out={y_out}, expected {expected_y}"

        dut._log.info(f"[PASS] rotation {angle_deg}deg: "
                       f"x_out={x_out:.5f} (exp {expected_x:.5f}), "
                       f"y_out={y_out:.5f} (exp {expected_y:.5f})")


@cocotb.test()
async def test_vectoring_multiple_vectors(dut):
    """
    Vectoring mode: feed (x, y), expect x_out ~ magnitude, z_out ~ atan2(y, x).
    Inputs kept x > 0 -- standard CORDIC vectoring only converges directly for
    vectors within -90..90 degrees of the positive x-axis; x < 0 needs a
    pre-rotation step this core doesn't implement, so we stay in the valid range.
    """
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)

    # (x, y) pairs -- includes a negative y (exercises the other shift_dir branch)
    test_vectors = [(1.0, 1.0), (1.0, -0.5), (0.5, 1.5), (2.0, 0.1)]

    for x, y in test_vectors:
        # z_in = 0: no pre-existing angle offset, we just want the raw atan2(y, x)
        x_out, y_out, z_out = await run_cordic(dut, mode=0, x=x, y=y, z=0.0)

        expected_mag = math.sqrt(x**2 + y**2)
        expected_angle = math.atan2(y, x)

        assert abs(x_out - expected_mag) < TOLERANCE, \
            f"[x={x},y={y}] x_out={x_out}, expected magnitude {expected_mag}"
        assert abs(z_out - expected_angle) < TOLERANCE, \
            f"[x={x},y={y}] z_out={z_out}, expected angle {expected_angle}"
        # y should converge near 0 -- looser tolerance since it's whatever's
        # "left over" after ITERATIONS steps, not a directly gain-compensated output
        assert abs(y_out) < TOLERANCE * 3, \
            f"[x={x},y={y}] y_out={y_out}, expected ~0"

        dut._log.info(f"[PASS] vectoring x={x},y={y}: "
                       f"mag={x_out:.5f} (exp {expected_mag:.5f}), "
                       f"angle={z_out:.5f} (exp {expected_angle:.5f})")