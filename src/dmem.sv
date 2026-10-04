// dmem: 1 KB byte-addressed data memory, little endian
// writes are sync (on the edge), reads are combinational so loads finish in the same cycle
// anything that touches a byte past 1023 is dropped (stores) or reads 0 (loads) instead of aliasing back onto address 0

module dmem (
    input  logic        clk,
    input  logic [31:0] addr,         //rs1 + imm straight from the alu
    input  logic [31:0] write_data,   //rs2
    input  logic        mem_read,
    input  logic        mem_write,
    input  logic [2:0]  funct3,       //[1:0] = size (b/h/w), [2] = unsigned for loads
    output logic [31:0] read_data
);

    localparam int BYTES = 1024;

    logic [7:0] mem [0:BYTES-1];

    //range check covers the last byte too, so a word at 1022 doesn't spill into 0
    logic [31:0] last_byte;
    logic        in_range;
    always_comb begin
        case (funct3[1:0])
            2'b00:   last_byte = addr;
            2'b01:   last_byte = addr + 32'd1;
            default: last_byte = addr + 32'd3;
        endcase
    end
    assign in_range = (addr < BYTES) && (last_byte < BYTES);   //addr check catches addr+3 wrapping past 2^32

    logic [9:0] a;                    //only the low 10 bits index the array once we know it's in range
    assign a = addr[9:0];

    //store: write 1, 2 or 4 bytes starting at addr, low byte at the lowest address
    always_ff @(posedge clk) begin
        if (mem_write && in_range) begin
            case (funct3[1:0])
                2'b00: mem[a] <= write_data[7:0];                                //sb
                2'b01: begin                                                     //sh
                    mem[a]      <= write_data[7:0];
                    mem[a + 10'd1] <= write_data[15:8];
                end
                2'b10: begin                                                     //sw
                    mem[a]      <= write_data[7:0];
                    mem[a + 10'd1] <= write_data[15:8];
                    mem[a + 10'd2] <= write_data[23:16];
                    mem[a + 10'd3] <= write_data[31:24];
                end
                default: ;
            endcase
        end
    end

    //load: grab the bytes and extend based on funct3
    always_comb begin
        if (mem_read && in_range) begin
            case (funct3)
                3'b000:  read_data = {{24{mem[a][7]}}, mem[a]};                                       //lb
                3'b001:  read_data = {{16{mem[a + 10'd1][7]}}, mem[a + 10'd1], mem[a]};               //lh
                3'b010:  read_data = {mem[a + 10'd3], mem[a + 10'd2], mem[a + 10'd1], mem[a]};        //lw
                3'b100:  read_data = {24'b0, mem[a]};                                                 //lbu
                3'b101:  read_data = {16'b0, mem[a + 10'd1], mem[a]};                                 //lhu
                default: read_data = 32'b0;
            endcase
        end else begin
            read_data = 32'b0;
        end
    end

endmodule
