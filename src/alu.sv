// alu: two 32-bit operands + op select in, result + zero flag out
// branches reuse this: sub for beq/bne (zero flag), slt/sltu for the rest (result[0])

module alu (
    input  logic [31:0] operand_a,
    input  logic [31:0] operand_b,
    input  logic [3:0]  alu_op,        //4 bits, room for 16 ops, 10 used
    output logic [31:0] result,
    output logic        zero
);
    typedef enum logic [3:0] {
        ALU_ADD  = 4'b0000,
        ALU_SUB  = 4'b0001,
        ALU_AND  = 4'b0010,
        ALU_OR   = 4'b0011,
        ALU_XOR  = 4'b0100,
        ALU_SLL  = 4'b0101,
        ALU_SRL  = 4'b0110,
        ALU_SRA  = 4'b0111,
        ALU_SLT  = 4'b1000,
        ALU_SLTU = 4'b1001
    } alu_op_e;

    always_comb begin
        case (alu_op)
            ALU_ADD:  result = operand_a + operand_b;
            ALU_SUB:  result = operand_a - operand_b;
            ALU_AND:  result = operand_a & operand_b;
            ALU_OR:   result = operand_a | operand_b;
            ALU_XOR:  result = operand_a ^ operand_b;
            ALU_SLL:  result = operand_a << operand_b[4:0];                 //only low 5 bits count as shamt
            ALU_SRL:  result = operand_a >> operand_b[4:0];                 //zero fill
            ALU_SRA:  result = signed'(operand_a) >>> operand_b[4:0];       //sign fill
            ALU_SLT:  result = (signed'(operand_a) < signed'(operand_b)) ? 32'd1 : 32'd0;
            ALU_SLTU: result = (operand_a < operand_b) ? 32'd1 : 32'd0;
            default:  result = 32'd0;
        endcase
        zero = (result == 32'd0);    //beq/bne read this off the sub
    end

endmodule
