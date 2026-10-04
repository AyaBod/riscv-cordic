// cordic.h: c wrappers for the four custom-0 instructions
// each one is a single .insn line, so the compiler picks the registers and the core does the math
// .insn r <opcode>, <funct3>, <funct7>, rd, rs1, rs2   -> opcode 0x0B = custom-0, funct3 picks the op
// values are q3.13 fixed point in an int32 (1.0 = 8192), results come back sign-extended

#ifndef CORDIC_H
#define CORDIC_H

#include <stdint.h>

// float literal -> q3.13, the compiler folds this at build time so no float code ends up in the binary
#define Q13(x) ((int32_t)((x) >= 0 ? (x) * 8192.0 + 0.5 : (x) * 8192.0 - 0.5))

// funct3 = 001: rotation, x_out  -> cos(angle), angle in radians, |angle| <= ~1.74
static inline int32_t cordic_cos(int32_t angle) {
    int32_t r;
    __asm__ volatile (".insn r 0x0B, 1, 0, %0, %1, x0" : "=r"(r) : "r"(angle));
    return r;
}

// funct3 = 011: rotation, y_out  -> sin(angle)
static inline int32_t cordic_sin(int32_t angle) {
    int32_t r;
    __asm__ volatile (".insn r 0x0B, 3, 0, %0, %1, x0" : "=r"(r) : "r"(angle));
    return r;
}

// funct3 = 000: vectoring, x_out -> sqrt(x^2 + y^2), needs x > 0 and magnitude < ~2.43
static inline int32_t cordic_mag(int32_t x, int32_t y) {
    int32_t r;
    __asm__ volatile (".insn r 0x0B, 0, 0, %0, %1, %2" : "=r"(r) : "r"(x), "r"(y));
    return r;
}

// funct3 = 010: vectoring, z_out -> atan2(y, x). note the argument order: x first (rs1), y second (rs2)
static inline int32_t cordic_atan2(int32_t x, int32_t y) {
    int32_t r;
    __asm__ volatile (".insn r 0x0B, 2, 0, %0, %1, %2" : "=r"(r) : "r"(x), "r"(y));
    return r;
}

#endif
