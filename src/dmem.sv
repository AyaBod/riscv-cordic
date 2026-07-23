module dmem (
    input  logic clk,
    input  logic [31:0] addr,
    input  logic [31:0] write_data,
    input  logic mem_read,
    input  logic mem_write,
    input  logic [2:0]  funct3, //tells width and signed or nto
    output logic [31:0] read_data
);


    logic [7:0] mem [0:1023]; //1024 bytes that are 8 bits long (standard)

    // TODO: write logic (always_ff @ posedge clk, gated by mem_write) --
    // needs to write 1, 2, or 4 bytes depending on funct3[1:0], starting at addr

    always_ff @(posedge clk) begin
        if (mem_write) begin
            case (funct3[1:0])
                2'b00: begin
                    //store one byte
                    mem[addr] <= write_data[7:0]; //one byte is one index in mem
                end
                2'b01: begin
                    //store two bytes
                    mem[addr] <= write_data[7:0];
                    mem[addr+1] <=write_data[15:8];
                end
                2'b10: begin
                    //store 4 bytes
                    mem[addr] <= write_data[7:0];
                    mem[addr+1] <=write_data[15:8];
                    mem[addr+2] <=write_data[23:16];
                    mem[addr+3] <= write_data[31:24];
                end
                default: ;//nothing
            endcase
        end
    end


    always_comb begin
        if (mem_read) begin
            case (funct3)
                3'b000: read_data = {{24{mem[addr][7]}}, mem[addr]}; //byte signed
                3'b001: read_data = {{16{mem[addr+1][7]}}, mem[addr+1], mem[addr]};//halfword signed 
                3'b010: read_data = {mem[addr+3], mem[addr+2], mem[addr+1], mem[addr]};//word
                3'b100: read_data = {{24{1'b0}}, mem[addr]};//byte unsigned
                3'b101: read_data = {{16{1'b0}}, mem[addr+1], mem[addr]};//halfword unsigned
                default: read_data =  32'b0;
            endcase
        end else begin
            read_data = 32'b0;
        end
    end



endmodule