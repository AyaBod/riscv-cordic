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


    always_comb begin
        //necessary signals get reassined based on case
        reg_write = 0;
        alu_src = 0;
        alu_op = 4'b0000; //defaults to add
        mem_read = 0;
        mem_write = 0;
        mem_to_reg = 0;
        is_branch = 0;
        is_jump = 0;
        case (opcode) 
            7'b0110111: begin
                reg_write = 1;
                alu_src = 1;
                alu_op = 4'b1001; //custom lui/pass imm op
            end
            //lui U     
            7'b0010111: begin
                reg_write = 1;
                alu_src = 1; 
                alu_op = 4'b0000; //pc + imm (add)
            end
            //auipc U
            7'b1101111: begin
                reg_write = 1;
                is_jump = 1;
            end
            // jal J
            7'b1100111: begin
                reg_write = 1;
                alu_src = 1;
                alu_op = 4'b0000; //rs1 + offset
                is_jump = 1;
            end
            //jalr I
            7'b1100011: begin
                reg_write = 0;
                alu_src = 0; //comparing 2 regs not reg+imm
                is_branch = 1;
                case (funct3)
                    3'b000, 3'b001: alu_op = 4'b0001; // subtract for BEQ/BNE
                    3'b100, 3'b101: alu_op = 4'b1000; // set less than for BLT/BGE
                    3'b110, 3'b111: alu_op = 4'b1001; // slt unsigned for BLTU/BGEU
                    default: alu_op = 4'b0001;
                endcase
            end
            //beq/bne/blt/bge/bltu/bgeu B
            7'b0000011: begin
                reg_write = 1;
                alu_src = 1;  //address is rs1 + imm
                alu_op = 4'b0000; //add operation for address
                mem_read = 1;
                mem_to_reg = 1;  //pass memory data to register file
            end
            //lb/lh/lw/lbu/lhu I
            7'b0100011: begin
                alu_src = 1;  //address is rs1 + imm
                alu_op = 4'b0000; //add operation for address
                mem_write  = 1;
            end
            //sb/sh/sw S store
            7'b0010011: begin
                reg_write = 1;
                alu_src = 1;  // operand_b is immediate
                case (funct3)
                    3'b000: alu_op = 4'b0000; //ADDI
                    3'b010: alu_op = 4'b1000; //SLTI
                    3'b011: alu_op = 4'b1001; //SLTIU
                    3'b100: alu_op = 4'b0100; //XORI
                    3'b110: alu_op = 4'b0011; //ORI
                    3'b111: alu_op = 4'b0010; //ANDI
                    3'b001: alu_op = 4'b0101; //SLLI
                    3'b101: alu_op = (funct7[5]) ? 4'b0111 : 4'b0110; //SRAI : SRLI
                    default: alu_op = 4'b0000;
                endcase
            end
            //addi/slti/sltiu/xori/ori/andi/slli/srli/srai I
            7'b0110011: begin
                reg_write = 1;
                alu_src = 0;  //operand b is rs2
                case (funct3)
                    3'b000: alu_op = (funct7[5]) ? 4'b0001 : 4'b0000; //SUB : ADD
                    3'b001: alu_op = 4'b0101; //SLL
                    3'b010: alu_op = 4'b1000; //SLT
                    3'b011: alu_op = 4'b1001; //SLTU
                    3'b100: alu_op = 4'b0100; //XOR
                    3'b101: alu_op = (funct7[5]) ? 4'b0111 : 4'b0110; //SRA : SRL
                    3'b110: alu_op = 4'b0011; //OR
                    3'b111: alu_op = 4'b0010; //AND
                    default: alu_op = 4'b0000;
                endcase
            end

            //add/sub/sll/slt/sltu/xor/srl/sra/or/and R
            default: begin
                reg_write = 0;
                alu_src = 0;
                alu_op = 4'b0000; //defaults to add
                mem_read = 0;
                mem_write = 0;
                mem_to_reg = 0;
                is_branch = 0;
                is_jump = 0;
            end
        endcase
    end

endmodule 