module cordic #(
    parameter int WIDTH = 16,      // fixed-point width
    parameter int FRAC_BITS = 13,  //Q format range vs precision tradeoff
    //^^^out of 16 total bits, 1 bit is for the sign, 2 bits are for the whole integer, and 13 bits are dedicated to the fractional precision
    parameter [3:0] ITERATIONS = 12  //iteration count affects precision/latency tradeoff
    //^^Running 12 iterations means it'll run 12 micro-rotations; more iterations equal higher accuracy, but cost more clock cycles
) (
    input logic clk,
    input logic rst_n, //active low
    input logic start,
    input logic mode_in, //rotation and vectoring, 0,1 so one bit
    //rotation = feed an x,y vector and target angle z, rotate until angle z = 0; x  = cos, y = sin
    //vector = feed x,y , rotated until y = 0 basc align it with x axis; x = hypotenuse/magntitude, accumlated z = arctan(y/x)
    input logic signed [WIDTH-1:0] x_in,
    input logic signed [WIDTH-1:0] y_in,
    input logic signed [WIDTH-1:0] z_in,
    output logic signed [WIDTH-1:0] x_out,
    output logic signed [WIDTH-1:0] y_out,
    output logic signed [WIDTH-1:0] z_out,
    output logic done,
    output logic busy
);


    
    logic signed [WIDTH-1:0] reg_x; //hold output
    logic signed [WIDTH-1:0] reg_y; //hold output
    logic signed [WIDTH-1:0] reg_z; //hold output
    logic mode;

    logic [$clog2(ITERATIONS)-1:0] index; //counter

    localparam logic signed [WIDTH-1:0] INV_GAIN = 16'h136F; //fix the multiplier gain at the end

    //only 12 entries so localpararm good enough
    //arctan(2^-12) s0 1/2^(0 to 111)
    //Q3.13 pre-scaled angle lookup table for atan(2^-i) in radians
    localparam logic signed [WIDTH-1:0] arctan_table [0:ITERATIONS-1] = '{
        16'h1922, // idx=0:  atan(1)       = 0.7854 rad
        16'h0ED6, // idx=1:  atan(0.5)     = 0.4636 rad
        16'h07D7, // idx=2:  atan(0.25)    = 0.2450 rad
        16'h03FB, // idx=3:  atan(0.125)   = 0.1244 rad
        16'h01FF, // idx=4:  atan(0.0625)  = 0.0624 rad
        16'h0100, // idx=5:  atan(0.03125) = 0.0312 rad
        16'h0080, // idx=6:  atan(2^-6)    = 0.0156 rad
        16'h0040, // idx=7:  atan(2^-7)    = 0.0078 rad
        16'h0020, // idx=8:  atan(2^-8)    = 0.0039 rad
        16'h0010, // idx=9:  atan(2^-9)    = 0.0020 rad
        16'h0008, // idx=10: atan(2^-10)   = 0.0010 rad
        16'h0004  // idx=11: atan(2^-11)   = 0.0005 rad
    };



    typedef enum logic [1:0] { //3 bits
        IDLE = 2'b00,
        ITERATE = 2'b01,
        DONE = 2'b10
    } states;

    states state;
    states next_state;


    ///direction is based on mode
    //cw or ccw5
    logic shift_dir;
    assign shift_dir = (mode == 1'b1) ? (reg_z[WIDTH-1] == 1'b0) : (reg_y[WIDTH-1] == 1'b1);
    //rotate(1): want reg_z to be 0, check if reg_z is positive using MSB, if too high then must subtract to get to zero
    //shift_dir = 1 is needing to go more left (be less)
    //vecoring(0): reg_y should be zero, check if reg_y is negative, if so then must rotate ccw/left to bring it to zero
    //1 means too positive so cw/right

    // Continuous arithmetic right shifts based on the current index
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
                    if (start) begin
                        reg_x <= x_in; 
                        reg_y <= y_in;
                        reg_z <= z_in;
                        index <= '0;
                        mode <= mode_in;
                    end
                end

                ITERATE: begin
                    index <= index + 1'b1; 
                    if (shift_dir) begin
                        reg_x <= reg_x - shifted_y;
                        reg_y <= reg_y + shifted_x;
                        reg_z <= reg_z - arctan_table[index];
                    end else begin
                        reg_x <= reg_x + shifted_y;
                        reg_y <= reg_y - shifted_x;
                        reg_z <= reg_z + arctan_table[index];
                    end
                end

                default: ;
            endcase
        end
    end
    always_comb begin  //handles what state to chnage to
        case (state)
            IDLE: begin 
                if (start) begin 
                    next_state = ITERATE;
                end else begin
                    next_state = IDLE;
                end
            end
            ITERATE : begin
                if (index == ITERATIONS-1) begin
                    next_state = DONE;
                end else begin
                    next_state = ITERATE;
                end
            end
            DONE: begin
                next_state = IDLE;
            end 
            default: next_state = IDLE;
        endcase
    end

    //assignments with post scale gain compensation
    //intermediate 32 bit math buffers hold the sign-extended multiplier product
    logic signed [(2*WIDTH)-1:0] scaled_x_long;
    logic signed [(2*WIDTH)-1:0] scaled_y_long;

    assign scaled_x_long = reg_x * INV_GAIN;
    assign scaled_y_long = reg_y * INV_GAIN;

    assign done = (state == DONE);
    assign busy = (state != IDLE); //stall must hold through done too

    always_comb begin
        if (mode == 1'b1) begin
            //rotation mode: both X (cos) and Y (sin) grow and must be scaled down
            x_out = scaled_x_long[FRAC_BITS +: WIDTH];
            y_out = scaled_y_long[FRAC_BITS +: WIDTH];
            z_out = reg_z; //z converges to 0, no scaling needed
        end else begin
            //vectoring mode: only X (Magnitude) grows; Y becomes 0; Z (arctan) is unscaled.
            x_out = scaled_x_long[FRAC_BITS +: WIDTH];
            y_out = reg_y; //will naturally be about 0
            z_out = reg_z; //rawunscaled angle output
        end
    end
endmodule