// main.c: exercises all four cordic instructions from c and leaves the results in dmem
// the testbench (tb/c_program) reads them back and checks them against python's math module
// rules for this core: no * or / (no m extension), no initialized globals, no constant arrays

#include "cordic.h"

#define OUT ((volatile int32_t *)0x100) // results live at dmem 0x100, volatile so stores aren't optimized out
#define DONE_MAGIC 0xC0DE

int main(void) {
    // one call per instruction
    OUT[0] = cordic_cos(Q13(0.5));
    OUT[1] = cordic_sin(Q13(0.5));
    OUT[2] = cordic_mag(Q13(0.3), Q13(0.4));
    OUT[3] = cordic_atan2(Q13(0.3), Q13(0.4)); // atan2(y = 0.4, x = 0.3)

    // sine sweep from -1.4 to +1.4 rad in 0.4 steps, plain c loop feeding the hardware
    int32_t angle = Q13(-1.4);
    for (int i = 0; i < 8; i++) {
        OUT[4 + i] = cordic_sin(angle);
        angle += Q13(0.4);
    }

    // chain hardware into hardware: |(cos t, sin t)| should come back as 1.0
    int32_t c = cordic_cos(Q13(1.0));
    int32_t s = cordic_sin(Q13(1.0));
    OUT[12] = cordic_mag(c, s);

    OUT[15] = DONE_MAGIC; // last store, testbench uses it as the finished flag
    return 0;
}
