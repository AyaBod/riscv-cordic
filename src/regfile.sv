// regfile: 32 x 32-bit, two async read ports, one sync write port
// x0 is hardwired to 0 on both the read side and the write side

module regfile (
    input logic clk,
    input logic rst, //active high, core_top flips rst_n into this
    input logic we, //write en from core_top (reg_write or cordic_done)
    input logic [4:0] rs1_addr, //source reg
    input logic [4:0] rs2_addr, //source reg
    input logic [4:0] rd_addr, //destination register
    input logic [31:0] rd_data, //data to write
    output logic [31:0] rs1_data, //read data
    output logic [31:0] rs2_data //read data
);

    //32x32 reg array, 32 reg that are each 32 bits wide
    logic [31:0] regs [0:31]; //[31:0] 32 bits wide

    //reads are combinational so the same-cycle alu can use them
    always_comb begin
        //data = library[address/index]
        rs1_data = (rs1_addr == 5'd0) ? 32'd0 : regs[rs1_addr];
        rs2_data = (rs2_addr == 5'd0) ? 32'd0 : regs[rs2_addr];
    end

    //write lands on the clock edge that ends the instruction
    always_ff @(posedge clk) begin
        if (rst) begin
            for (int i = 0; i < 32; i++)
                regs[i] <= '0;
        end else if (we && rd_addr != 5'd0) begin //writes to x0 just disappear, single cycle has no construction overlap
            regs[rd_addr] <= rd_data;
        end
    end

endmodule
