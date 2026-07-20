module imm_gen (
    input logic [31:0] instruction,
    output logic [31:0] imm_out
);


    logic [6:0] opcode;
    assign opcode = instruction[6:0];
    

    //turning 12 bit SIGNED numbers into 32 bits so needs sign extension
    always_comb begin
        case (opcode) 
            7'b0110111: imm_out = {instruction[31:12], 12'b0}; 
            //lui U      19 bits+12; keep big number big so stick to left
            7'b0010111: imm_out = {instruction[31:12], 12'b0};
            //auipc U
            7'b1101111: imm_out = {{12{instruction[31]}}, instruction[19:12], instruction[20], instruction[30:21], 1'b0};
            // jal J
            7'b1100111: imm_out = {{20{instruction[31]}}, instruction[31:20]}; 
            //jalr I
            7'b1100011: imm_out = {{20{instruction[31]}}, instruction[7], instruction[30:25], instruction[11:8], 1'b0}; //19 extension + instr[31] at imm[12]    
            //beq/bne/blt/bge/bltu/bgeu B
            7'b0000011: imm_out = {{20{instruction[31]}}, instruction[31:20]}; 
            //lb/lh/lw/lbu/lhu I
            7'b0100011: imm_out = {{20{instruction[31]}}, instruction[31:25], instruction[11:7]}; //12 bits + 19 extenstion bits
            //sb/sh/sw S
            7'b0010011: imm_out = {{20{instruction[31]}}, instruction[31:20]}; 
            //addi/slti/sltiu/xori/ori/andi/slli/srli/srai I
            7'b0110011: imm_out = 32'b0; 
            //add/sub/sll/slt/sltu/xor/srl/sra/or/and R
            default: imm_out = 32'b0; 
            //r type has no immediate :p
        endcase
        
    end 

    
endmodule