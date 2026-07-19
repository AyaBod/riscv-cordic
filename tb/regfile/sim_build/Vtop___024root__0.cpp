// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vtop.h for the primary calling header

#include "Vtop__pch.h"

bool Vtop___024root___trigger_anySet__ico(const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___trigger_anySet__ico\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        if (in[n]) {
            return (1U);
        }
        n = ((IData)(1U) + n);
    } while ((1U > n));
    return (0U);
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vtop___024root___dump_triggers__ico(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag);
#endif  // VL_DEBUG

bool Vtop___024root___eval_phase__ico(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_phase__ico\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VicoExecute;
    // Body
    {
        // Inlined CFunc: _eval_triggers_vec__ico
        vlSelfRef.__VicoTriggered[0U] = ((0xfffffffffffffffeULL 
                                          & vlSelfRef.__VicoTriggered[0U]) 
                                         | (IData)((IData)(vlSelfRef.__VicoFirstIteration)));
    }
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vtop___024root___dump_triggers__ico(vlSelfRef.__VicoTriggered, "ico"s);
    }
#endif
    __VicoExecute = Vtop___024root___trigger_anySet__ico(vlSelfRef.__VicoTriggered);
    if (__VicoExecute) {
        {
            // Inlined CFunc: _eval_ico
            if ((1ULL & vlSelfRef.__VicoTriggered[0U])) {
                {
                    // Inlined CFunc: _ico_sequent__TOP__0
                    vlSelfRef.regfile__DOT__clk = vlSelfRef.clk;
                    vlSelfRef.regfile__DOT__rst = vlSelfRef.rst;
                    vlSelfRef.regfile__DOT__we = vlSelfRef.we;
                    vlSelfRef.regfile__DOT__rd_addr 
                        = vlSelfRef.rd_addr;
                    vlSelfRef.regfile__DOT__rd_data 
                        = vlSelfRef.rd_data;
                    vlSelfRef.regfile__DOT__rs1_addr 
                        = vlSelfRef.rs1_addr;
                    vlSelfRef.regfile__DOT__rs2_addr 
                        = vlSelfRef.rs2_addr;
                    vlSelfRef.regfile__DOT__rs1_data 
                        = vlSelfRef.regfile__DOT__regs
                        [vlSelfRef.regfile__DOT__rs1_addr];
                    if ((0U == (IData)(vlSelfRef.regfile__DOT__rs1_addr))) {
                        vlSelfRef.regfile__DOT__rs1_data = 0U;
                    }
                    vlSelfRef.regfile__DOT__rs2_data 
                        = vlSelfRef.regfile__DOT__regs
                        [vlSelfRef.regfile__DOT__rs2_addr];
                    if ((0U == (IData)(vlSelfRef.regfile__DOT__rs2_addr))) {
                        vlSelfRef.regfile__DOT__rs2_data = 0U;
                    }
                    vlSelfRef.rs1_data = vlSelfRef.regfile__DOT__rs1_data;
                    vlSelfRef.rs2_data = vlSelfRef.regfile__DOT__rs2_data;
                }
            }
        }
    }
    return (__VicoExecute);
}

bool Vtop___024root___trigger_anySet__act(const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___trigger_anySet__act\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        if (in[n]) {
            return (1U);
        }
        n = ((IData)(1U) + n);
    } while ((1U > n));
    return (0U);
}

void Vtop___024root___trigger_orInto__act_vec_vec(VlUnpacked<QData/*63:0*/, 1> &out, const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___trigger_orInto__act_vec_vec\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        out[n] = (out[n] | in[n]);
        n = ((IData)(1U) + n);
    } while ((0U >= n));
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vtop___024root___dump_triggers__act(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag);
#endif  // VL_DEBUG

bool Vtop___024root___eval_phase__act(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_phase__act\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    {
        // Inlined CFunc: _eval_triggers_vec__act
        vlSelfRef.__VactTriggered[0U] = (QData)((IData)(
                                                        ((IData)(vlSelfRef.regfile__DOT__clk) 
                                                         & (~ (IData)(vlSelfRef.__Vtrigprevexpr___TOP__regfile__DOT__clk__0)))));
        vlSelfRef.__Vtrigprevexpr___TOP__regfile__DOT__clk__0 
            = vlSelfRef.regfile__DOT__clk;
    }
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vtop___024root___dump_triggers__act(vlSelfRef.__VactTriggered, "act"s);
    }
#endif
    Vtop___024root___trigger_orInto__act_vec_vec(vlSelfRef.__VnbaTriggered, vlSelfRef.__VactTriggered);
    return (0U);
}

void Vtop___024root___trigger_clear__act(VlUnpacked<QData/*63:0*/, 1> &out) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___trigger_clear__act\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        out[n] = 0ULL;
        n = ((IData)(1U) + n);
    } while ((1U > n));
}

bool Vtop___024root___eval_phase__nba(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_phase__nba\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VnbaExecute;
    // Body
    __VnbaExecute = Vtop___024root___trigger_anySet__act(vlSelfRef.__VnbaTriggered);
    if (__VnbaExecute) {
        {
            // Inlined CFunc: _eval_nba
            if ((1ULL & vlSelfRef.__VnbaTriggered[0U])) {
                {
                    // Inlined CFunc: _nba_sequent__TOP__0
                    CData/*4:0*/ __Vinline_0__eval_nba___Vinline_0__nba_sequent__TOP__0___VdlyDim0__regfile__DOT__regs__v0;
                    __Vinline_0__eval_nba___Vinline_0__nba_sequent__TOP__0___VdlyDim0__regfile__DOT__regs__v0 = 0;
                    IData/*31:0*/ __Vinline_0__eval_nba___Vinline_0__nba_sequent__TOP__0___VdlyVal__regfile__DOT__regs__v1;
                    __Vinline_0__eval_nba___Vinline_0__nba_sequent__TOP__0___VdlyVal__regfile__DOT__regs__v1 = 0;
                    CData/*4:0*/ __Vinline_0__eval_nba___Vinline_0__nba_sequent__TOP__0___VdlyDim0__regfile__DOT__regs__v1;
                    __Vinline_0__eval_nba___Vinline_0__nba_sequent__TOP__0___VdlyDim0__regfile__DOT__regs__v1 = 0;
                    if (vlSelfRef.regfile__DOT__rst) {
                        vlSelfRef.regfile__DOT__unnamedblk1__DOT__i = 0U;
                        while (VL_GTS_III(32, 0x00000020U, vlSelfRef.regfile__DOT__unnamedblk1__DOT__i)) {
                            __Vinline_0__eval_nba___Vinline_0__nba_sequent__TOP__0___VdlyDim0__regfile__DOT__regs__v0 
                                = (0x0000001fU & vlSelfRef.regfile__DOT__unnamedblk1__DOT__i);
                            vlSelfRef.__VdlyCommitQueueregfile__DOT__regs.enqueue(0U, __Vinline_0__eval_nba___Vinline_0__nba_sequent__TOP__0___VdlyDim0__regfile__DOT__regs__v0);
                            vlSelfRef.regfile__DOT__unnamedblk1__DOT__i 
                                = ((IData)(1U) + vlSelfRef.regfile__DOT__unnamedblk1__DOT__i);
                        }
                    } else if (((((IData)(vlSelfRef.regfile__DOT__we) 
                                  & (0U != (IData)(vlSelfRef.regfile__DOT__rd_addr))) 
                                 & ((IData)(vlSelfRef.regfile__DOT__rs1_addr) 
                                    != (IData)(vlSelfRef.regfile__DOT__rd_addr))) 
                                & ((IData)(vlSelfRef.regfile__DOT__rs2_addr) 
                                   != (IData)(vlSelfRef.regfile__DOT__rd_addr)))) {
                        __Vinline_0__eval_nba___Vinline_0__nba_sequent__TOP__0___VdlyVal__regfile__DOT__regs__v1 
                            = vlSelfRef.regfile__DOT__rd_data;
                        __Vinline_0__eval_nba___Vinline_0__nba_sequent__TOP__0___VdlyDim0__regfile__DOT__regs__v1 
                            = vlSelfRef.regfile__DOT__rd_addr;
                        vlSelfRef.__VdlyCommitQueueregfile__DOT__regs.enqueue(__Vinline_0__eval_nba___Vinline_0__nba_sequent__TOP__0___VdlyVal__regfile__DOT__regs__v1, __Vinline_0__eval_nba___Vinline_0__nba_sequent__TOP__0___VdlyDim0__regfile__DOT__regs__v1);
                    }
                    vlSelfRef.__VdlyCommitQueueregfile__DOT__regs.commit(vlSelfRef.regfile__DOT__regs);
                    vlSelfRef.regfile__DOT__rs1_data 
                        = vlSelfRef.regfile__DOT__regs
                        [vlSelfRef.regfile__DOT__rs1_addr];
                    if ((0U == (IData)(vlSelfRef.regfile__DOT__rs1_addr))) {
                        vlSelfRef.regfile__DOT__rs1_data = 0U;
                    }
                    vlSelfRef.regfile__DOT__rs2_data 
                        = vlSelfRef.regfile__DOT__regs
                        [vlSelfRef.regfile__DOT__rs2_addr];
                    if ((0U == (IData)(vlSelfRef.regfile__DOT__rs2_addr))) {
                        vlSelfRef.regfile__DOT__rs2_data = 0U;
                    }
                    vlSelfRef.rs1_data = vlSelfRef.regfile__DOT__rs1_data;
                    vlSelfRef.rs2_data = vlSelfRef.regfile__DOT__rs2_data;
                }
            }
        }
        Vtop___024root___trigger_clear__act(vlSelfRef.__VnbaTriggered);
    }
    return (__VnbaExecute);
}

void Vtop___024root___eval(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __VicoIterCount;
    IData/*31:0*/ __VnbaIterCount;
    // Body
    __VicoIterCount = 0U;
    vlSelfRef.__VicoFirstIteration = 1U;
    do {
        if (VL_UNLIKELY(((0x00002710U < __VicoIterCount)))) {
#ifdef VL_DEBUG
            Vtop___024root___dump_triggers__ico(vlSelfRef.__VicoTriggered, "ico"s);
#endif
            VL_FATAL_MT("/home/ayanna/projects/riscv-cordic/src/regfile.sv", 1, "", "DIDNOTCONVERGE: Input combinational region did not converge after '--converge-limit' of 10000 tries");
        }
        __VicoIterCount = ((IData)(1U) + __VicoIterCount);
        vlSelfRef.__VicoPhaseResult = Vtop___024root___eval_phase__ico(vlSelf);
        vlSelfRef.__VicoFirstIteration = 0U;
    } while (vlSelfRef.__VicoPhaseResult);
    __VnbaIterCount = 0U;
    do {
        if (VL_UNLIKELY(((0x00002710U < __VnbaIterCount)))) {
#ifdef VL_DEBUG
            Vtop___024root___dump_triggers__act(vlSelfRef.__VnbaTriggered, "nba"s);
#endif
            VL_FATAL_MT("/home/ayanna/projects/riscv-cordic/src/regfile.sv", 1, "", "DIDNOTCONVERGE: NBA region did not converge after '--converge-limit' of 10000 tries");
        }
        __VnbaIterCount = ((IData)(1U) + __VnbaIterCount);
        vlSelfRef.__VactIterCount = 0U;
        do {
            if (VL_UNLIKELY(((0x00002710U < vlSelfRef.__VactIterCount)))) {
#ifdef VL_DEBUG
                Vtop___024root___dump_triggers__act(vlSelfRef.__VactTriggered, "act"s);
#endif
                VL_FATAL_MT("/home/ayanna/projects/riscv-cordic/src/regfile.sv", 1, "", "DIDNOTCONVERGE: Active region did not converge after '--converge-limit' of 10000 tries");
            }
            vlSelfRef.__VactIterCount = ((IData)(1U) 
                                         + vlSelfRef.__VactIterCount);
            vlSelfRef.__VactPhaseResult = Vtop___024root___eval_phase__act(vlSelf);
        } while (vlSelfRef.__VactPhaseResult);
        vlSelfRef.__VnbaPhaseResult = Vtop___024root___eval_phase__nba(vlSelf);
    } while (vlSelfRef.__VnbaPhaseResult);
}

#ifdef VL_DEBUG
void Vtop___024root___eval_debug_assertions(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_debug_assertions\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if (VL_UNLIKELY(((vlSelfRef.clk & 0xfeU)))) {
        Verilated::overWidthError("clk");
    }
    if (VL_UNLIKELY(((vlSelfRef.rst & 0xfeU)))) {
        Verilated::overWidthError("rst");
    }
    if (VL_UNLIKELY(((vlSelfRef.we & 0xfeU)))) {
        Verilated::overWidthError("we");
    }
    if (VL_UNLIKELY(((vlSelfRef.rs1_addr & 0xe0U)))) {
        Verilated::overWidthError("rs1_addr");
    }
    if (VL_UNLIKELY(((vlSelfRef.rs2_addr & 0xe0U)))) {
        Verilated::overWidthError("rs2_addr");
    }
    if (VL_UNLIKELY(((vlSelfRef.rd_addr & 0xe0U)))) {
        Verilated::overWidthError("rd_addr");
    }
}
#endif  // VL_DEBUG
