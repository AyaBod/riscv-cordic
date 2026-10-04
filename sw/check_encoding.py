#!/usr/bin/env python3
"""check_encoding: every custom-0 word gcc emitted must decode to one of our four ops and
re-encode bit-for-bit with the python encoder the testbenches use. assembler vs python check;
the rtl vs assembler check is tb/c_program actually running the binary."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tb", "common"))
from rv32i import OPC_CUSTOM0, CORDIC_MNEMONICS, encode_cordic   # noqa: E402

def main(hexfile):
    found = 0
    for addr, line in enumerate(open(hexfile)):
        w = int(line, 16)
        if w & 0x7F != OPC_CUSTOM0:
            continue
        rd, f3, rs1, rs2, f7 = (w >> 7) & 0x1F, (w >> 12) & 7, (w >> 15) & 0x1F, (w >> 20) & 0x1F, w >> 25
        assert f7 == 0, f"{4*addr:#06x}: funct7 = {f7}, expected 0"
        assert f3 in CORDIC_MNEMONICS, f"{4*addr:#06x}: funct3 = {f3:03b} isn't a cordic op"
        assert encode_cordic(rd, rs1, rs2, f3) == w, f"{4*addr:#06x}: python re-encode mismatch"
        name = CORDIC_MNEMONICS[f3]
        ops = f"x{rd}, x{rs1}" + ("" if name in ("cordic.cos", "cordic.sin") else f", x{rs2}")
        print(f"  {4*addr:#06x}: {w:08x}  {name:<13} {ops}")
        found += 1
    assert found, "no custom-0 instructions found, did the inline asm get optimized away?"
    print(f"OK: {found} cordic instructions match the python encoding")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "build/prog.hex")
