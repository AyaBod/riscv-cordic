# riscv-cordic

A single-cycle RV32I CPU in SystemVerilog with a CORDIC unit bolted on as a second execution unit.
Four custom instructions (`cordic.cos`, `cordic.sin`, `cordic.mag`, `cordic.atan2`) live in the
RISC-V custom-0 opcode space, and a small C header turns them into normal-looking function calls
via inline assembly. Everything is verified with cocotb on Verilator, including a compiled C
program running on the core.

```
            +--------+   instr   +---------+  ctrl   +-----------------------------+
  pc ------>|  imem  |---------->| decode  |-------->|  alu (1 cycle)              |---+
   ^        +--------+           | control |         |                             |   |
   |                             +---------+         |  cordic (12 iters, shift/add)|---+--> writeback --> regfile
   |                                  |              +-----------------------------+   |
   |   core_stall = cordic_op && !cordic_done          start / busy / done              |
   +--- pc_next = stall ? pc : (branch/jump/pc+4)                                       |
                                                     dmem (1 KB, byte addressed) <------+
```

## Custom instructions

R-type, opcode `0001011` (custom-0), `funct7 = 0`. All values are Q3.13 fixed point
(1.0 = `0x2000`) in the low 16 bits of a register; results come back sign-extended to 32 bits.

| funct3 | mnemonic | mode | operands | result |
|---|---|---|---|---|
| `000` | `cordic.mag rd, rs1, rs2` | vectoring | x = rs1, y = rs2 | √(x² + y²) |
| `001` | `cordic.cos rd, rs1` | rotation | angle = rs1 | cos(angle) |
| `010` | `cordic.atan2 rd, rs1, rs2` | vectoring | x = rs1, y = rs2 | atan2(y, x) |
| `011` | `cordic.sin rd, rs1` | rotation | angle = rs1 | sin(angle) |

`funct3[0]` picks the mode (1 = rotation, 0 = vectoring) and `funct3[1]` picks the output
(primary vs secondary), so decode is two wires.

From C (`sw/cordic.h`):

```c
int32_t c = cordic_cos(Q13(0.5));          // one .insn line each, compiler picks the registers
int32_t a = cordic_atan2(Q13(0.3), Q13(0.4));
```

## Why the core stalls

The core is single-cycle, so normally the PC moves every clock. A CORDIC op takes 12+ cycles.
If the PC kept moving:

* **instruction overwrite:** the instruction word changes, so `rd` and the source register
  fields are gone before the CORDIC result is ready to write back
* **state corruption:** ~12 unrelated instructions execute while CORDIC is still computing

`core_stall = cordic_op && !cordic_done` forces `pc_next = pc_current`, which freezes the
instruction word (and its register fields) until the op finishes. Writeback is gated on
`cordic_done`, so `rd` is written exactly once, on the last cycle. This is the same idea as a
structural hazard in a pipelined core: when one execution unit breaks the one-cycle assumption,
the rest of the datapath has to wait for it.

Timing (measured in `test_cordic_stall_and_commit_timing`): 13 stalled cycles + 1 commit cycle
= 14 cycles per CORDIC instruction; everything else is 1 cycle.

## CORDIC unit

Iterative, 12 micro-rotations, Q3.13. Each iteration is two shifts, three add/subtracts and a
table lookup. The 1/K gain correction (1/1.6468 = 0.60725) is also shift-add only:

```
1/K ≈ 1/2 + 1/8 − 1/64 − 1/512 − 1/4096 = 0.60718   (error 7.5e-5, below 1 LSB)
```

found by searching signed power-of-two combinations for the fewest terms within 1e-4.
There's no `*` anywhere in `src/cordic.sv`.

## Running it

Tested with Python 3.12, cocotb 2.0.1, Verilator 5.050, riscv64-unknown-elf-gcc 13.2 (WSL Ubuntu 24.04).

```bash
sudo apt install verilator gcc-riscv64-unknown-elf
pip install cocotb==2.0.1
make test          # builds sw/, then runs every testbench
```

Or one at a time: `make -C sw`, `make -C tb/core_top`, etc.

## Results

| Testbench | What it covers | Tests |
|---|---|---|
| `tb/core_top` | every RV32I instruction through the full core: R-type and I-type ALU ops, LUI/AUIPC, all six branches, JAL/JALR, all loads/stores, FENCE/ECALL/EBREAK, x0, out-of-range memory, load-use, a small integration program | 27 |
| `tb/cordic` | standalone unit: handshake timing, sin/cos sweep over ±1.5 rad, mag/atan2, documented limits | 4 |
| `tb/core_cordic` | all four instructions in the core, stall/commit timing, back-to-back + dependent ops, rd = x0, negative operands | 8 |
| `tb/c_program` | compiled C program using all four instructions, results checked against Python `math` | 1 |
| `tb/alu` | unit: add/sub, bitwise ops, shifts incl. SRA sign fill, SLT vs SLTU, zero flag, default case | 8 |
| `tb/control` | unit: control lines for R-type, SRAI vs SRLI, load, store, branch, JAL, unused opcode | 9 |
| `tb/dmem` | unit: word/half/byte stores and loads with sign/zero extension, neighbour bytes untouched, read/write enables | 8 |
| `tb/imem` | unit: word fetch from a hex file, unused address | 4 |
| `tb/imm_gen` | unit: I/S/B/U/J immediates incl. negative offsets, R-type and unused opcodes give 0 | 8 |
| `tb/regfile` | unit: reset, x0 reads 0, write/read, dual read ports, write enable | 5 |

`sw/check_encoding.py` also checks that every custom-0 word gcc emitted re-encodes bit-for-bit
with the Python encoder the testbenches use (15 instructions in the current build).

Accuracy: sin/cos within 0.0007 over ±1.5 rad, mag within 0.002, atan2 within 0.005.

## Limitations

| Limit | Value | Why |
|---|---|---|
| Rotation range | \|angle\| ≤ ~1.74 rad (≈100°) | sum of the 12 table angles; past that it can't rotate far enough |
| Vectoring range | x > 0 | no quadrant pre-rotation, left-half-plane vectors give the wrong angle |
| Magnitude | input magnitude < ~2.43 | x grows by K = 1.6468 internally and has to stay under 4.0 in Q3.13 |
| ECALL / EBREAK | decoded as no-ops | no trap / privileged support (FENCE is a legal no-op on one in-order hart) |
| Memory | 1 KB imem + 1 KB dmem, Harvard | no initialized data: the linker script fails the build if C code needs globals or `.rodata` |
| C code | no `*` or `/` | RV32I only, no M extension and no libgcc |
