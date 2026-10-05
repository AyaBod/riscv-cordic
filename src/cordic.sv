// cordic: iterative shift-add unit, 12 micro-rotations, q3.13 fixed point
// rotation (mode 1): start at (x, y), rotate by z until z hits 0 -> x = cos, y = sin (when started at (1, 0))
// vectoring (mode 0): rotate (x, y) until y hits 0 -> x = magnitude, z = atan2(y, x)
// no multipliers anywhere: the iterations are shifts + adds and the gain fix is a fixed shift-add sum too

module cordic #(
    parameter int WIDTH = 16, // fixed-point width, total bits
    parameter int FRAC_BITS = 13, //Q format range vs precision tradeoff
    //^^^out of 16 total bits, 1 bit is for the sign, 2 bits are for the whole integer, and 13 bits are dedicated to the fractional precision (q3.13, range about +/-4.0)
    parameter [3:0] ITERATIONS = 12 //iteration count affects precision/latency tradeoff
    //^^Running 12 iterations means it'll run 12 micro-rotations; more iterations equal higher accuracy, but cost more clock cycles
) (
    input logic clk,
    input logic rst_n, //active low
    input logic start, //one-cycle pulse from the core, only looked at in IDLE
    input logic mode_in, //rotation and vectoring, 0,1 so one bit: 1 = rotation, 0 = vectoring
    //rotation = feed an x,y vector and target angle z, rotate until angle z = 0; x = cos, y = sin
    //vector = feed x,y , rotated until y = 0 basc align it with x axis; x = hypotenuse/magntitude, accumlated z = arctan(y/x)
    input logic signed [WIDTH-1:0] x_in,
    input logic signed [WIDTH-1:0] y_in,
    input logic signed [WIDTH-1:0] z_in,
    output logic signed [WIDTH-1:0] x_out,
    output logic signed [WIDTH-1:0] y_out,
    output logic signed [WIDTH-1:0] z_out,
    output logic done, //high for exactly one cycle when outputs are valid
    output logic busy //high from the cycle after start through done
);

    logic signed [WIDTH-1:0] reg_x, reg_y, reg_z; //hold output: working vector + angle accumulator
    logic mode; //latched at start so the core can't change it mid-op

    logic [$clog2(ITERATIONS)-1:0] index; //counter, also the shift amount

    //only 12 entries so localpararm good enough
    //Q3.13 pre-scaled angle lookup table for atan(2^-i) in radians (value * 8192)
    //each step rotates by exactly one of these, so z tracks how far we've turned
    localparam logic signed [WIDTH-1:0] arctan_table [0:ITERATIONS-1] = '{
        16'h1922, // idx=0: atan(1) = 0.7854 rad
        16'h0ED6, // idx=1: atan(0.5) = 0.4636 rad
        16'h07D7, // idx=2: atan(0.25) = 0.2450 rad
        16'h03FB, // idx=3: atan(0.125) = 0.1244 rad
        16'h01FF, // idx=4: atan(0.0625) = 0.0624 rad
        16'h0100, // idx=5: atan(0.03125) = 0.0312 rad
        16'h0080, // idx=6: atan(2^-6) = 0.0156 rad
        16'h0040, // idx=7: atan(2^-7) = 0.0078 rad
        16'h0020, // idx=8: atan(2^-8) = 0.0039 rad
        16'h0010, // idx=9: atan(2^-9) = 0.0020 rad
        16'h0008, // idx=10: atan(2^-10) = 0.0010 rad
        16'h0004 // idx=11: atan(2^-11) = 0.0005 rad
    };

    typedef enum logic [1:0] {
        IDLE = 2'b00,
        ITERATE = 2'b01,
        DONE = 2'b10
    } states;

    states state, next_state;

    ///direction is based on mode
    //cw or ccw5
    //which way to turn this step
    //rotation: z still positive -> turn ccw (and subtract the angle from z)
    //vectoring: y negative -> turn ccw (pushes y back up toward 0)
    logic shift_dir;
    assign shift_dir = (mode == 1'b1) ? (reg_z[WIDTH-1] == 1'b0) : (reg_y[WIDTH-1] == 1'b1);
    //rotate(1): want reg_z to be 0, check if reg_z is positive using MSB, if too high then must subtract to get to zero
    //shift_dir = 1 is needing to go more left (be less)
    //vecoring(0): reg_y should be zero, check if reg_y is negative, if so then must rotate ccw/left to bring it to zero
    //1 means too positive so cw/right

    // Continuous arithmetic right shifts based on the current index
    //multiplying by 2^-i is just an arithmetic right shift, this is the whole trick
    logic signed [WIDTH-1:0] shifted_x, shifted_y;
    assign shifted_x = reg_x >>> index;
    assign shifted_y = reg_y >>> index;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            reg_x <= '0;
            reg_y <= '0;
            reg_z <= '0;
            index <= '0;
            mode <= '0; //default??
            state <= IDLE;
        end else begin
            state <= next_state;
            case (state)
                IDLE: begin
                    if (start) begin //grab operands once, core's regs can do whatever after this
                        reg_x <= x_in;
                        reg_y <= y_in;
                        reg_z <= z_in;
                        index <= '0;
                        mode <= mode_in;
                    end
                end

                ITERATE: begin
                    index <= index + 1'b1;
                    if (shift_dir) begin //ccw micro-rotation
                        reg_x <= reg_x - shifted_y;
                        reg_y <= reg_y + shifted_x;
                        reg_z <= reg_z - arctan_table[index];
                    end else begin //cw micro-rotation
                        reg_x <= reg_x + shifted_y;
                        reg_y <= reg_y - shifted_x;
                        reg_z <= reg_z + arctan_table[index];
                    end
                end

                default: ; //DONE just holds the result for one cycle
            endcase
        end
    end

    always_comb begin //handles what state to chnage to
        case (state)
            IDLE: next_state = start ? ITERATE : IDLE;
            ITERATE: next_state = (index == ITERATIONS-1) ? DONE : ITERATE;
            DONE: next_state = IDLE;
            default: next_state = IDLE;
        endcase
    end

    assign done = (state == DONE);
    assign busy = (state != IDLE); //stall must hold through done too, includes DONE so the core can't re-start on the done cycle

    // ------------------------------------------------------------------
    // gain compensation, shift-add only (assignments with post scale gain compensation)
    // ------------------------------------------------------------------
    //every micro-rotation stretches the vector by sqrt(1 + 2^-2i); after 12 steps that's K = 1.6468
    //so x/y come out K times too big and we multiply by 1/K = 0.60725 at the end
    //1/K ~= 1/2 + 1/8 - 1/64 - 1/512 - 1/4096 = 0.60718 (5 terms, error 7.5e-5, below 1 lsb of q3.13)
    //found by searching signed power-of-two combos (csd style) for the fewest terms within 1e-4
    localparam int GUARD = 4; //extra low bits so the 5 truncated shifts don't each eat an lsb

    function automatic logic signed [WIDTH-1:0] gain_comp(input logic signed [WIDTH-1:0] v);
        logic signed [WIDTH+GUARD-1:0] e, t;
        begin
            e = {v, {GUARD{1'b0}}}; //widen with guard bits
            t = (e >>> 1) + (e >>> 3) - (e >>> 6) - (e >>> 9) - (e >>> 12);
            gain_comp = t[GUARD +: WIDTH]; //drop guard bits, same as t >>> GUARD
        end
    endfunction

    always_comb begin
        if (mode == 1'b1) begin
            //rotation mode: both X (cos) and Y (sin) grow and must be scaled down (stretched by K)
            x_out = gain_comp(reg_x);
            y_out = gain_comp(reg_y);
            z_out = reg_z; //z converges to 0, no scaling needed
        end else begin
            //vectoring mode: only X (Magnitude) grows; Y becomes 0; Z (arctan) is unscaled.
            x_out = gain_comp(reg_x);
            y_out = reg_y; //will naturally be about 0
            z_out = reg_z; //rawunscaled angle output
        end
    end

endmodule
