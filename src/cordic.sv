// cordic: iterative shift-add unit, 12 micro-rotations, q3.13 fixed point
// rotation  (mode 1): start at (x, y), rotate by z until z hits 0  -> x = cos, y = sin (when started at (1, 0))
// vectoring (mode 0): rotate (x, y) until y hits 0                 -> x = magnitude, z = atan2(y, x)
// no multipliers anywhere: the iterations are shifts + adds and the gain fix is a fixed shift-add sum too

module cordic #(
    parameter int WIDTH = 16,          //total bits
    parameter int FRAC_BITS = 13,      //q3.13: 1 sign + 2 integer + 13 fraction, range about +/-4.0
    parameter [3:0] ITERATIONS = 12    //more iterations = more accuracy, one more clock each
) (
    input  logic clk,
    input  logic rst_n,                //active low
    input  logic start,                //one-cycle pulse from the core, only looked at in IDLE
    input  logic mode_in,              //1 = rotation, 0 = vectoring
    input  logic signed [WIDTH-1:0] x_in,
    input  logic signed [WIDTH-1:0] y_in,
    input  logic signed [WIDTH-1:0] z_in,
    output logic signed [WIDTH-1:0] x_out,
    output logic signed [WIDTH-1:0] y_out,
    output logic signed [WIDTH-1:0] z_out,
    output logic done,                 //high for exactly one cycle when outputs are valid
    output logic busy                  //high from the cycle after start through done
);

    logic signed [WIDTH-1:0] reg_x, reg_y, reg_z;   //working vector + angle accumulator
    logic mode;                                     //latched at start so the core can't change it mid-op

    logic [$clog2(ITERATIONS)-1:0] index;           //iteration counter, also the shift amount

    //atan(2^-i) in radians, pre-scaled to q3.13 (value * 8192)
    //each step rotates by exactly one of these, so z tracks how far we've turned
    localparam logic signed [WIDTH-1:0] arctan_table [0:ITERATIONS-1] = '{
        16'h1922, // i=0:  atan(1)      = 0.7854
        16'h0ED6, // i=1:  atan(2^-1)   = 0.4636
        16'h07D7, // i=2:  atan(2^-2)   = 0.2450
        16'h03FB, // i=3:  atan(2^-3)   = 0.1244
        16'h01FF, // i=4:  atan(2^-4)   = 0.0624
        16'h0100, // i=5:  atan(2^-5)   = 0.0312
        16'h0080, // i=6:  atan(2^-6)   = 0.0156
        16'h0040, // i=7:  atan(2^-7)   = 0.0078
        16'h0020, // i=8:  atan(2^-8)   = 0.0039
        16'h0010, // i=9:  atan(2^-9)   = 0.0020
        16'h0008, // i=10: atan(2^-10)  = 0.0010
        16'h0004  // i=11: atan(2^-11)  = 0.0005
    };

    typedef enum logic [1:0] {
        IDLE    = 2'b00,
        ITERATE = 2'b01,
        DONE    = 2'b10
    } states;

    states state, next_state;

    //which way to turn this step
    //rotation:  z still positive -> turn ccw (and subtract the angle from z)
    //vectoring: y negative       -> turn ccw (pushes y back up toward 0)
    logic shift_dir;
    assign shift_dir = (mode == 1'b1) ? (reg_z[WIDTH-1] == 1'b0) : (reg_y[WIDTH-1] == 1'b1);

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
            mode  <= '0;
            state <= IDLE;
        end else begin
            state <= next_state;
            case (state)
                IDLE: begin
                    if (start) begin                //grab operands once, core's regs can do whatever after this
                        reg_x <= x_in;
                        reg_y <= y_in;
                        reg_z <= z_in;
                        index <= '0;
                        mode  <= mode_in;
                    end
                end

                ITERATE: begin
                    index <= index + 1'b1;
                    if (shift_dir) begin            //ccw micro-rotation
                        reg_x <= reg_x - shifted_y;
                        reg_y <= reg_y + shifted_x;
                        reg_z <= reg_z - arctan_table[index];
                    end else begin                  //cw micro-rotation
                        reg_x <= reg_x + shifted_y;
                        reg_y <= reg_y - shifted_x;
                        reg_z <= reg_z + arctan_table[index];
                    end
                end

                default: ;                          //DONE just holds the result for one cycle
            endcase
        end
    end

    always_comb begin
        case (state)
            IDLE:    next_state = start ? ITERATE : IDLE;
            ITERATE: next_state = (index == ITERATIONS-1) ? DONE : ITERATE;
            DONE:    next_state = IDLE;
            default: next_state = IDLE;
        endcase
    end

    assign done = (state == DONE);
    assign busy = (state != IDLE);                  //includes DONE so the core can't re-start on the done cycle

    // ------------------------------------------------------------------
    // gain compensation, shift-add only
    // ------------------------------------------------------------------
    //every micro-rotation stretches the vector by sqrt(1 + 2^-2i); after 12 steps that's K = 1.6468
    //so x/y come out K times too big and we multiply by 1/K = 0.60725 at the end
    //1/K ~= 1/2 + 1/8 - 1/64 - 1/512 - 1/4096 = 0.60718  (5 terms, error 7.5e-5, below 1 lsb of q3.13)
    //found by searching signed power-of-two combos (csd style) for the fewest terms within 1e-4
    localparam int GUARD = 4;   //extra low bits so the 5 truncated shifts don't each eat an lsb

    function automatic logic signed [WIDTH-1:0] gain_comp(input logic signed [WIDTH-1:0] v);
        logic signed [WIDTH+GUARD-1:0] e, t;
        begin
            e = {v, {GUARD{1'b0}}};                                     //widen with guard bits
            t = (e >>> 1) + (e >>> 3) - (e >>> 6) - (e >>> 9) - (e >>> 12);
            gain_comp = t[GUARD +: WIDTH];                              //drop guard bits, same as t >>> GUARD
        end
    endfunction

    always_comb begin
        if (mode == 1'b1) begin
            //rotation: x and y both got stretched by K
            x_out = gain_comp(reg_x);
            y_out = gain_comp(reg_y);
            z_out = reg_z;                          //should be ~0, angles aren't scaled
        end else begin
            //vectoring: x is the stretched magnitude, y got driven to ~0, z is the raw angle
            x_out = gain_comp(reg_x);
            y_out = reg_y;
            z_out = reg_z;
        end
    end

endmodule
