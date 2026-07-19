// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design internal header
// See Vtop.h for the primary calling header

#ifndef VERILATED_VTOP___024ROOT_H_
#define VERILATED_VTOP___024ROOT_H_  // guard

#include "verilated.h"


class Vtop__Syms;

class alignas(VL_CACHE_LINE_BYTES) Vtop___024root final {
  public:

    // DESIGN SPECIFIC STATE
    VL_IN8(clk,0,0);
    VL_IN8(rst,0,0);
    VL_IN8(we,0,0);
    VL_IN8(rs1_addr,4,0);
    VL_IN8(rs2_addr,4,0);
    VL_IN8(rd_addr,4,0);
    CData/*0:0*/ regfile__DOT__clk;
    CData/*0:0*/ regfile__DOT__rst;
    CData/*0:0*/ regfile__DOT__we;
    CData/*4:0*/ regfile__DOT__rs1_addr;
    CData/*4:0*/ regfile__DOT__rs2_addr;
    CData/*4:0*/ regfile__DOT__rd_addr;
    CData/*0:0*/ __VstlFirstIteration;
    CData/*0:0*/ __VstlPhaseResult;
    CData/*0:0*/ __VicoFirstIteration;
    CData/*0:0*/ __VicoPhaseResult;
    CData/*0:0*/ __Vtrigprevexpr___TOP__regfile__DOT__clk__0;
    CData/*0:0*/ __VactPhaseResult;
    CData/*0:0*/ __VnbaPhaseResult;
    VL_IN(rd_data,31,0);
    VL_OUT(rs1_data,31,0);
    VL_OUT(rs2_data,31,0);
    IData/*31:0*/ regfile__DOT__rd_data;
    IData/*31:0*/ regfile__DOT__rs1_data;
    IData/*31:0*/ regfile__DOT__rs2_data;
    IData/*31:0*/ regfile__DOT__unnamedblk1__DOT__i;
    IData/*31:0*/ __VactIterCount;
    VlUnpacked<IData/*31:0*/, 32> regfile__DOT__regs;
    VlUnpacked<QData/*63:0*/, 1> __VstlTriggered;
    VlUnpacked<QData/*63:0*/, 1> __VicoTriggered;
    VlUnpacked<QData/*63:0*/, 1> __VactTriggered;
    VlUnpacked<QData/*63:0*/, 1> __VnbaTriggered;
    VlNBACommitQueue<VlUnpacked<IData/*31:0*/, 32>, false, IData/*31:0*/, 1> __VdlyCommitQueueregfile__DOT__regs;

    // INTERNAL VARIABLES
    Vtop__Syms* vlSymsp;
    const char* vlNamep;

    // CONSTRUCTORS
    Vtop___024root(Vtop__Syms* symsp, const char* namep);
    ~Vtop___024root();
    VL_UNCOPYABLE(Vtop___024root);

    // INTERNAL METHODS
    void __Vconfigure(bool first);
};


#endif  // guard
