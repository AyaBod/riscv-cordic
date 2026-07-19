module regfile (
    input logic clk,
    input logic rst,
    input logic we,  //write en
    input logic [4:0] rs1_addr,    //source reg
    input logic [4:0] rs2_addr,     //source reg
    input logic [4:0] rd_addr,    //destination register
    input logic [31:0] rd_data,    //data to write
    output logic [31:0] rs1_data,   //read data
    output logic [31:0] rs2_data    //read data
);

    //32x32 reg array, 32 reg that are each 32 bits wide
    logic [31:0] regs [0:31]; //[31:0] 32 bits wide

    always_comb begin
        rs1_data = regs[rs1_addr];
        rs2_data = regs[rs2_addr];
        //data = library[address/index]

        if (rs1_addr == '0) begin
            rs1_data = '0;
        end

        if (rs2_addr == '0) begin
            rs2_data = '0;
        end
    end

    always_ff @ (posedge clk) begin 
        if (rst) begin
        
            for (int i = 0; i < 32; i++) begin
                regs[i] <= '0;
            end
        end else begin
            if (we && rd_addr != 5'b0) begin  //single cycle has no construction overlap
                regs[rd_addr] <= rd_data;
            end
        end
    end


endmodule
