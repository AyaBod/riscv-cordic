// core_top: single-cycle rv32i core + cordic as a second execution unit
// one instruction per clock, except custom-0 (cordic) which parks the pc until the unit says done

module core_top #(
    parameter IMEM_INIT_FILE = ""
) (
    input  logic clk,
    input  logic rst_n            //active low, everything resets to 0
);

    localparam logic [6:0] OPC_LUI     = 7'b0110111;
    localparam logic [6:0] OPC_AUIPC   = 7'b0010111;
    localparam logic [6:0] OPC_JAL     = 7'b1101111;
    localparam logic [6:0] OPC_JALR    = 7'b1100111;
    localparam logic [6:0] OPC_LOAD    = 7'b0000011;
    localparam logic [6:0] OPC_CUSTOM0 = 7'b0001011;  //spec reserves custom-0 for vendor extensions, so cordic lives here

    // ------------------------------------------------------------------
    // pc
    // ------------------------------------------------------------------
    logic [31:0] pc_current;
    logic [31:0] pc_next;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            pc_current <= 32'h0000_0000;
        else
            pc_current <= pc_next;          //pc_next comes from the mux at the bottom
    end

    logic [31:0] pc_plus4;
    assign pc_plus4 = pc_current + 32'd4;   //default path + jal/jalr link value

    // ------------------------------------------------------------------
    // fetch
    // ------------------------------------------------------------------
    logic [31:0] instruction;

    imem #(
        .INIT_FILE (IMEM_INIT_FILE)
    ) u_imem (
        .addr(pc_current),                  //pc indexes imem directly, no cache
        .instruction(instruction)
    );

    // ------------------------------------------------------------------
    // decode: just slicing fields, every format puts them in the same spot
    // ------------------------------------------------------------------
    logic [6:0] opcode;
    logic [4:0] rd_addr, rs1_addr, rs2_addr;
    logic [2:0] funct3;
    logic [6:0] funct7;

    assign opcode   = instruction[6:0];
    assign rd_addr  = instruction[11:7];
    assign funct3   = instruction[14:12];
    assign rs1_addr = instruction[19:15];
    assign rs2_addr = instruction[24:20];
    assign funct7   = instruction[31:25];

    // ------------------------------------------------------------------
    // control + immediates
    // ------------------------------------------------------------------
    logic reg_write, alu_src, mem_read, mem_write, mem_to_reg, is_branch, is_jump;
    logic [3:0] alu_op;

    control u_control (
        .opcode(opcode),
        .funct3(funct3),
        .funct7(funct7),
        .reg_write(reg_write),
        .alu_src(alu_src),
        .alu_op(alu_op),
        .mem_read(mem_read),
        .mem_write(mem_write),
        .mem_to_reg(mem_to_reg),
        .is_branch(is_branch),
        .is_jump(is_jump)
    );

    logic [31:0] imm;
    imm_gen u_imm_gen (
        .instruction(instruction),          //imm_gen looks at opcode itself to pick the format
        .imm_out(imm)
    );

    // ------------------------------------------------------------------
    // register file
    // ------------------------------------------------------------------
    logic [31:0] rs1_data, rs2_data;
    logic        rd_we;
    logic [31:0] rd_wdata;                  //driven by the writeback mux

    regfile u_regfile (
        .clk(clk),
        .rst(~rst_n),                       //regfile wants active high, flip it here
        .we(rd_we),
        .rs1_addr(rs1_addr),
        .rs2_addr(rs2_addr),
        .rd_addr(rd_addr),
        .rd_data(rd_wdata),
        .rs1_data(rs1_data),
        .rs2_data(rs2_data)
    );

    // ------------------------------------------------------------------
    // cordic: second execution unit, sits next to the alu
    // ------------------------------------------------------------------
    // custom-0 encoding (r-type, funct7 = 0):
    //   funct3[0] picks the mode:   1 = rotation (angle in rs1)   0 = vectoring (x = rs1, y = rs2)
    //   funct3[1] picks the output: 0 = primary (cos / mag)       1 = secondary (sin / atan2)
    //
    //   000  cordic.mag   rd, rs1, rs2    -> x_out
    //   001  cordic.cos   rd, rs1         -> x_out
    //   010  cordic.atan2 rd, rs1, rs2    -> z_out   (rs1 = x, rs2 = y)
    //   011  cordic.sin   rd, rs1         -> y_out
    //
    // all values are q3.13 in the low 16 bits of the register, results come back sign-extended
    logic cordic_op;
    assign cordic_op = (opcode == OPC_CUSTOM0);

    logic cordic_rot, cordic_sel;
    assign cordic_rot = funct3[0];          //mode bit goes straight into the unit
    assign cordic_sel = funct3[1];          //output bit only matters at writeback

    logic cordic_busy, cordic_done;
    logic signed [15:0] cordic_x_out, cordic_y_out, cordic_z_out;

    logic cordic_start;
    assign cordic_start = cordic_op && !cordic_busy;  //busy goes high the cycle after, so start is a one-cycle pulse

    logic core_stall;
    assign core_stall = cordic_op && !cordic_done;    //freezes the pc for the whole op, drops on the done cycle
    //without this the pc moves every clock, the instruction word (and its rd/rs fields) changes under the
    //unit, and the next ~12 instructions run while cordic is still mid-calculation

    localparam logic signed [15:0] CORDIC_ONE  = 16'sh2000;   //1.0 in q3.13
    localparam logic signed [15:0] CORDIC_ZERO = 16'sh0000;

    cordic u_cordic (
        .clk(clk),
        .rst_n(rst_n),
        .start(cordic_start),
        .mode_in(cordic_rot),
        .x_in(cordic_rot ? CORDIC_ONE  : rs1_data[15:0]),     //rotation starts from the unit vector (1, 0)
        .y_in(cordic_rot ? CORDIC_ZERO : rs2_data[15:0]),     //vectoring takes (x, y) from rs1/rs2
        .z_in(cordic_rot ? rs1_data[15:0] : CORDIC_ZERO),     //rotation: rs1 is the angle, vectoring accumulates from 0
        .x_out(cordic_x_out),
        .y_out(cordic_y_out),
        .z_out(cordic_z_out),
        .done(cordic_done),
        .busy(cordic_busy)
    );

    logic signed [15:0] cordic_result;      //one result per instruction, funct3 picks which
    always_comb begin
        case ({cordic_rot, cordic_sel})
            2'b10:   cordic_result = cordic_x_out;   //cordic.cos
            2'b11:   cordic_result = cordic_y_out;   //cordic.sin
            2'b00:   cordic_result = cordic_x_out;   //cordic.mag
            default: cordic_result = cordic_z_out;   //cordic.atan2
        endcase
    end

    //cordic ops ignore control's reg_write (it's 0 for custom-0) and only write on the done cycle
    assign rd_we = cordic_op ? cordic_done : reg_write;

    // ------------------------------------------------------------------
    // alu
    // ------------------------------------------------------------------
    logic [31:0] operand_a, operand_b;

    always_comb begin
        case (opcode)
            OPC_LUI:   operand_a = 32'b0;       //0 + imm = imm, reuses add instead of a new alu op
            OPC_AUIPC: operand_a = pc_current;  //pc + imm
            default:   operand_a = rs1_data;
        endcase
    end

    assign operand_b = alu_src ? imm : rs2_data;   //alu_src from control picks imm vs rs2

    logic [31:0] alu_result;
    logic        alu_zero;

    alu u_alu (
        .operand_a(operand_a),
        .operand_b(operand_b),
        .alu_op(alu_op),
        .result(alu_result),
        .zero(alu_zero)
    );

    // ------------------------------------------------------------------
    // branches: alu does the compare, this just reads the flag
    // ------------------------------------------------------------------
    logic branch_taken;

    always_comb begin
        branch_taken = 1'b0;
        if (is_branch) begin
            case (funct3)
                3'b000:  branch_taken =  alu_zero;       //beq  (sub == 0)
                3'b001:  branch_taken = ~alu_zero;       //bne
                3'b100:  branch_taken =  alu_result[0];  //blt  (slt == 1)
                3'b101:  branch_taken = ~alu_result[0];  //bge
                3'b110:  branch_taken =  alu_result[0];  //bltu (sltu == 1)
                3'b111:  branch_taken = ~alu_result[0];  //bgeu
                default: branch_taken = 1'b0;
            endcase
        end
    end

    // ------------------------------------------------------------------
    // next pc
    // ------------------------------------------------------------------
    logic [31:0] pc_branch_target, pc_jal_target, pc_jalr_target;
    assign pc_branch_target = pc_current + imm;
    assign pc_jal_target    = pc_current + imm;
    assign pc_jalr_target   = alu_result & ~32'h1;   //rs1 + imm with the lsb cleared, per spec

    always_comb begin
        if (core_stall)
            pc_next = pc_current;                    //stall wins over everything, instruction stays put
        else if (is_jump && opcode == OPC_JALR)
            pc_next = pc_jalr_target;
        else if (is_jump)
            pc_next = pc_jal_target;
        else if (is_branch && branch_taken)
            pc_next = pc_branch_target;
        else
            pc_next = pc_plus4;
    end

    // ------------------------------------------------------------------
    // data memory (harvard: separate from imem, both start at address 0)
    // ------------------------------------------------------------------
    logic [31:0] mem_read_data;

    dmem u_dmem (
        .clk(clk),
        .addr(alu_result),                  //address = rs1 + imm from the alu
        .write_data(rs2_data),
        .mem_read(mem_read),
        .mem_write(mem_write),
        .funct3(funct3),                    //funct3 tells dmem byte/half/word + signed/unsigned
        .read_data(mem_read_data)
    );

    // ------------------------------------------------------------------
    // writeback
    // ------------------------------------------------------------------
    always_comb begin
        case (opcode)
            OPC_JAL,
            OPC_JALR:    rd_wdata = pc_plus4;                                    //link address
            OPC_LOAD:    rd_wdata = mem_read_data;                               //already extended by dmem
            OPC_CUSTOM0: rd_wdata = {{16{cordic_result[15]}}, cordic_result};    //sign-extend the q3.13 result
            default:     rd_wdata = alu_result;                                  //alu ops, lui, auipc
        endcase
    end

endmodule
