module imem #(
    parameter INIT_FILE = ""
 ) (
    input logic [31:0] addr, //address for pc value
    output logic [31:0] instruction //fetched instruction
);


    // TODO: array to hold instructions -- how many words do you want to
    // support? pick something reasonable for now (e.g. 256 words = 1KB)

    logic [31:0] words [0:255]; //256 words that are 32 bits long

    // TODO: how do you get program content INTO this array before simulation
    // starts? look into $readmemh -- it loads a hex file into a memory array
    // at time 0. you'll need to hand-write a tiny .hex file with a few
    // instructions to test this against later.
    initial begin
        if (INIT_FILE != "")
                $readmemh(INIT_FILE, words);
    end

    
    // TODO: read logic -- given addr is a byte address (per RV32I convention,
    // PC increments by 4 each instruction), but your array is indexed by
    // WORD (each entry is one 32-bit instruction) -- what's the relationship
    // between a byte address and a word index? think about what happens if
    // you index the array directly with addr vs. addr divided/shifted somehow.

    logic [7:0] word_index;  //256 words counter
    //each instruction uses 4 bytes
    assign word_index = addr[9:2]; //cutting off the last 2 bits gives the actual index
    //dont need anything above 9 since this is for word counter index
    assign instruction = words[word_index];

endmodule