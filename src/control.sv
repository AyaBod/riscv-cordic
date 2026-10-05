// control: opcode (+ funct3/funct7) in, datapath select lines out
// pure combinational, everything defaults to 0 so unknown opcodes act like a nop

module control (
    input logic [6:0] opcode,
    input logic [2:0] funct3,
    input logic [6:0] funct7,

    output logic reg_write, //write back result to regfile
    output logic alu_src, //alu opernand_b where 0 regfile rs2 and 1 immediate
    output logic [3:0] alu_op, //feeds into alu_op input
    output logic mem_read, //load instruction
    output logic mem_write, //store instruction
    output logic mem_to_reg, //writeback source: 0 = ALU result, 1 = memory data
    output logic is_branch, //any branch instruction (beq/bne/blt/...)
    output logic is_jump //jal/jalr
);

    //alu op codes, same numbering as alu.sv
    localparam logic [3:0] ADD = 4'b0000, SUB = 4'b0001, AND = 4'b0010, OR = 4'b0011,
                           XOR = 4'b0100, SLL = 4'b0101, SRL = 4'b0110, SRA = 4'b0111,
                           SLT = 4'b1000, SLTU = 4'b1001;

    always_comb begin
        //necessary signals get reassined based on case
        reg_write = 0;
        alu_src = 0;
        alu_op = ADD; //defaults to add
        mem_read = 0;
        mem_write = 0;
        mem_to_reg = 0;
        is_branch = 0;
        is_jump = 0;

        case (opcode)
            //lui (U): core forces operand_a = 0, so 0 + imm = imm
            7'b0110111: begin
                reg_write = 1;
                alu_src = 1;
                alu_op = ADD; //custom lui/pass imm op
            end

            //auipc (U): core forces operand_a = pc, so pc + imm
            7'b0010111: begin
                reg_write = 1;
                alu_src = 1;
                alu_op = ADD; //pc + imm (add)
            end

            //jal (J): target is pc + imm (done in core_top), rd gets pc + 4
            7'b1101111: begin
                reg_write = 1;
                is_jump = 1;
            end

            //jalr (I): alu computes rs1 + imm for the target, rd gets pc + 4
            7'b1100111: begin
                reg_write = 1;
                alu_src = 1;
                alu_op = ADD; //rs1 + offset
                is_jump = 1;
            end

            //branches (B): alu compares rs1 vs rs2, core_top reads zero/result[0]
            7'b1100011: begin
                alu_src = 0; //comparing 2 regs not reg+imm
                is_branch = 1;
                case (funct3)
                    3'b000, 3'b001: alu_op = SUB; // subtract for BEQ/BNE, core_top reads the zero flag
                    3'b100, 3'b101: alu_op = SLT; // set less than for BLT/BGE
                    3'b110, 3'b111: alu_op = SLTU; // slt unsigned for BLTU/BGEU
                    default: alu_op = SUB;
                endcase
            end

            //loads (I): address = rs1 + imm, dmem handles width/sign from funct3
            7'b0000011: begin
                reg_write = 1;
                alu_src = 1; //address is rs1 + imm
                alu_op = ADD; //add operation for address
                mem_read = 1;
                mem_to_reg = 1; //pass memory data to register file
            end

            //stores (S): address = rs1 + imm, data = rs2
            7'b0100011: begin
                alu_src = 1; //address is rs1 + imm
                alu_op = ADD; //add operation for address
                mem_write = 1;
            end

            //op-imm (I): addi/slti/sltiu/xori/ori/andi/slli/srli/srai
            7'b0010011: begin
                reg_write = 1;
                alu_src = 1; // operand_b is immediate
                case (funct3)
                    3'b000: alu_op = ADD; //ADDI
                    3'b010: alu_op = SLT; //SLTI
                    3'b011: alu_op = SLTU; //SLTIU
                    3'b100: alu_op = XOR; //XORI
                    3'b110: alu_op = OR; //ORI
                    3'b111: alu_op = AND; //ANDI
                    3'b001: alu_op = SLL; //SLLI
                    3'b101: alu_op = funct7[5] ? SRA : SRL; //SRAI : SRLI, imm[10] is the srai flag
                    default: alu_op = ADD;
                endcase
            end

            //op (R): add/sub/sll/slt/sltu/xor/srl/sra/or/and
            7'b0110011: begin
                reg_write = 1;
                alu_src = 0; //operand b is rs2
                case (funct3)
                    3'b000: alu_op = funct7[5] ? SUB : ADD; //SUB : ADD
                    3'b001: alu_op = SLL; //SLL
                    3'b010: alu_op = SLT; //SLT
                    3'b011: alu_op = SLTU; //SLTU
                    3'b100: alu_op = XOR; //XOR
                    3'b101: alu_op = funct7[5] ? SRA : SRL; //SRA : SRL
                    3'b110: alu_op = OR; //OR
                    3'b111: alu_op = AND; //AND
                    default: alu_op = ADD;
                endcase
            end

            //fence (misc-mem): one hart, in-order, no caches, so ordering is already guaranteed -> nop
            7'b0001111: ;

            //ecall/ebreak (system): no trap/privileged support in this core -> decoded as nop
            7'b1110011: ;

            //custom-0 (cordic): everything stays 0 here, core_top drives rd_we from cordic_done instead
            7'b0001011: ;

            default: ;
        endcase
    end

endmodule
