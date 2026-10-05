// imem: 256-word (1 KB) instruction rom, read combinationally by the pc
// loaded from a hex file with $readmemh, or poked directly by the cocotb testbenches

module imem #(
    parameter INIT_FILE = ""
) (
    input logic [31:0] addr, //address for pc value (byte address)
    output logic [31:0] instruction //fetched instruction
);

    logic [31:0] words [0:255]; //256 words that are 32 bits long

    initial begin
        if (INIT_FILE != "")
            $readmemh(INIT_FILE, words); //one 32-bit hex word per line, same format sw/hexgen.py writes
    end

    //pc counts bytes, array counts words: drop the low 2 bits to get the word index
    //bits above 9 are ignored, so the pc wraps every 1 KB
    logic [7:0] word_index; //256 words counter
    //each instruction uses 4 bytes
    assign word_index = addr[9:2]; //cutting off the last 2 bits gives the actual index
    //dont need anything above 9 since this is for word counter index
    assign instruction = words[word_index];

endmodule
