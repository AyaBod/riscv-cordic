#!/usr/bin/env python3
"""hexgen: flat .bin -> one little-endian 32-bit word per line, the format imem's $readmemh wants"""
import struct
import sys

IMEM_WORDS = 256

def main(src, dst):
    data = open(src, "rb").read()
    data += b"\x00" * (-len(data) % 4)                      # pad to a whole word
    words = struct.unpack(f"<{len(data) // 4}I", data)      # riscv is little endian
    assert len(words) <= IMEM_WORDS, f"program is {len(words)} words, imem only holds {IMEM_WORDS}"
    with open(dst, "w") as f:
        for w in words:
            f.write(f"{w:08x}\n")
    print(f"{dst}: {len(words)} words ({len(words) * 100 // IMEM_WORDS}% of imem)")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
