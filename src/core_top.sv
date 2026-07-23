module core_top #(
    parameter IMEM_INIT_FILE = ""
) (
    input  logic clk,
    input  logic rst_n
);

    localparam logic [6:0] OPC_LUI = 7'b0110111;
    localparam logic [6:0] OPC_AUIPC = 7'b0010111;
    localparam logic [6:0] OPC_JAL   = 7'b1101111;
    localparam logic [6:0] OPC_JALR  = 7'b1100111;


    // pc registers
    logic [31:0] pc_current;
    logic [31:0] pc_next;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) //active low
            pc_current <= 32'h0000_0000;
        else
            pc_current <= pc_next;
    end

    //pc+4 is default path
    logic [31:0] pc_plus4;
    assign pc_plus4 = pc_current + 32'd4;

    // next pc mux placeholder 
    //stage 3 will add branch/jump targets here.
    //assign pc_next = pc_plus4;

    //instruction fetch
    logic [31:0] instruction;   //when will we assgin if instr is from init file

    imem #(
        .INIT_FILE (IMEM_INIT_FILE)
    ) u_imem (
        .addr(pc_current),
        .instruction(instruction)
    );

    //decode for field extractin
    logic [6:0] opcode;
    logic [4:0] rd_addr, rs1_addr, rs2_addr;
    logic [2:0] funct3;
    logic [6:0] funct7;

    assign opcode = instruction[6:0];
    assign rd_addr = instruction[11:7];
    assign rs1_addr = instruction[19:15];
    assign rs2_addr = instruction[24:20];
    assign funct3 = instruction[14:12];
    assign funct7 = instruction[31:25];


    //control
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

    //imm gen
    logic [31:0] imm;
    imm_gen u_imm_gen (
        .instruction(instruction),
        .imm_out(imm)
    );

    //reg file read
    logic [31:0] rs1_data, rs2_data;
    logic rd_we;
    logic [31:0] rd_wdata; //drive in writeback

    regfile u_regfile (
        .clk(clk),
        .rst(~rst_n), //convert polaristy to match
        .we(rd_we),
        .rs1_addr(rs1_addr),
        .rs2_addr(rs2_addr),
        .rd_addr(rd_addr),
        .rd_data(rd_wdata),
        .rs1_data(rs1_data),
        .rs2_data(rs2_data)
    );

    assign rd_we = reg_write; //place holder for writeback

    //alu op muxing
    logic [31:0] operand_a, operand_b;

    always_comb begin
        case (opcode)
            OPC_LUI: operand_a = 32'b0; //0 + imm = imm using existing ADD 
            OPC_AUIPC: operand_a = pc_current; //pc + imm
            default: operand_a = rs1_data;
        endcase
    end

    assign operand_b = alu_src ? imm : rs2_data;

    logic [31:0] alu_result;
    logic alu_zero;

    alu u_alu (
        .operand_a(operand_a),
        .operand_b(operand_b),
        .alu_op(alu_op),
        .result(alu_result),
        .zero(alu_zero)
    );

    //branch conditions
    logic branch_taken;

    always_comb begin
        branch_taken = 1'b0;
        if (is_branch) begin
            case (funct3)
                3'b000: branch_taken = alu_zero; // BEQ (Zero == 1)
                3'b001: branch_taken = ~alu_zero; // BNE (Zero == 0)
                3'b100: branch_taken = alu_result[0]; // BLT (SLT result is 1)
                3'b101: branch_taken = ~alu_result[0]; // BGE (Inverse of SLT)
                3'b110: branch_taken = alu_result[0]; // BLTU (SLTU result is 1)
                3'b111: branch_taken = ~alu_result[0]; // BGEU (Inverse of SLTU)
                default: branch_taken = 1'b0;
            endcase
        end
    end

    //next pc mux
    logic [31:0] pc_branch_target, pc_jal_target, pc_jalr_target;
    assign pc_branch_target = pc_current + imm;
    assign pc_jal_target = pc_current + imm;
    assign pc_jalr_target = alu_result & ~32'h1; //clear LSB per spec

    always_comb begin
        if (is_jump && opcode == OPC_JALR)
            pc_next = pc_jalr_target;
        else if (is_jump) //jal
            pc_next = pc_jal_target;
        else if (is_branch && branch_taken)
            pc_next = pc_branch_target;
        else 
            pc_next = pc_plus4;
    end

    // data memory
    logic [31:0] mem_read_data;
    
    dmem u_dmem (
        .clk(clk),
        .addr(alu_result),
        .write_data(rs2_data),
        .mem_read(mem_read),
        .mem_write(mem_write),
        .funct3(funct3),
        .read_data(mem_read_data)
    );

    //writeback mux
    always_comb begin
    case (opcode)
        //JAL and JALR explicitly write back the sequential link target (PC+4)
        7'b1101111, 
        7'b1100111: begin
            rd_wdata = pc_plus4;
        end
        
        //load instructions explicitly write back aligned memory data
        7'b0000011: begin
            rd_wdata = mem_read_data;
        end
        
        //regular ALU ops, LUI, and AUIPC write back the ALU math stream
        default: begin
            rd_wdata = alu_result;
        end
    endcase
end
endmodule