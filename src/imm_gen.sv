// imm_gen: pulls the immediate out of the instruction and sign-extends it to 32 bits
// each format scatters the bits differently, the opcode tells us which one

module imm_gen (
    input logic [31:0] instruction,
    output logic [31:0] imm_out
);

    logic [6:0] opcode;
    assign opcode = instruction[6:0];

    always_comb begin
        //turning 12 bit SIGNED numbers into 32 bits so needs sign extension
        case (opcode)
            7'b0110111, //lui (U): 19 bits+12; keep big number big so stick to left
            7'b0010111: imm_out = {instruction[31:12], 12'b0}; //auipc (U): upper 20 bits, low 12 zeroed
            7'b1101111: imm_out = {{12{instruction[31]}}, instruction[19:12], //jal (J): bit 0 is always 0
                                   instruction[20], instruction[30:21], 1'b0};
            7'b1100111, //jalr (I)
            7'b0000011, //loads (I): lb/lh/lw/lbu/lhu
            7'b0010011: imm_out = {{20{instruction[31]}}, instruction[31:20]}; //op-imm (I): addi/slti/sltiu/xori/ori/andi/slli/srli/srai
            7'b1100011: imm_out = {{20{instruction[31]}}, instruction[7], //branches (B) beq/bne/blt/bge/bltu/bgeu: 19 extension + instr[31] at imm[12], bit 0 is always 0
                                   instruction[30:25], instruction[11:8], 1'b0};
            7'b0100011: imm_out = {{20{instruction[31]}}, instruction[31:25], //stores (S) sb/sh/sw: 12 bits + 19 extenstion bits, split around rd's slot
                                   instruction[11:7]};
            default: imm_out = 32'b0; //r type has no immediate :p (custom-0 neither)
        endcase
    end

endmodule
