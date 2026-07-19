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

void Vtop___024root___ico_sequent__TOP__0(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___ico_sequent__TOP__0\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.alu__DOT__operand_a = vlSelfRef.operand_a;
    vlSelfRef.alu__DOT__operand_b = vlSelfRef.operand_b;
    vlSelfRef.alu__DOT__alu_op = vlSelfRef.alu_op;
    vlSelfRef.alu__DOT__result = ((8U & (IData)(vlSelfRef.alu__DOT__alu_op))
                                   ? ((4U & (IData)(vlSelfRef.alu__DOT__alu_op))
                                       ? 0U : ((2U 
                                                & (IData)(vlSelfRef.alu__DOT__alu_op))
                                                ? 0U
                                                : (
                                                   (1U 
                                                    & (IData)(vlSelfRef.alu__DOT__alu_op))
                                                    ? 
                                                   ((vlSelfRef.alu__DOT__operand_a 
                                                     < vlSelfRef.alu__DOT__operand_b)
                                                     ? 1U
                                                     : 0U)
                                                    : 
                                                   (VL_LTS_III(32, vlSelfRef.alu__DOT__operand_a, vlSelfRef.alu__DOT__operand_b)
                                                     ? 1U
                                                     : 0U))))
                                   : ((4U & (IData)(vlSelfRef.alu__DOT__alu_op))
                                       ? ((2U & (IData)(vlSelfRef.alu__DOT__alu_op))
                                           ? ((1U & (IData)(vlSelfRef.alu__DOT__alu_op))
                                               ? VL_SHIFTRS_III(32,32,5, vlSelfRef.alu__DOT__operand_a, 
                                                                (0x0000001fU 
                                                                 & vlSelfRef.alu__DOT__operand_b))
                                               : (vlSelfRef.alu__DOT__operand_a 
                                                  >> 
                                                  (0x0000001fU 
                                                   & vlSelfRef.alu__DOT__operand_b)))
                                           : ((1U & (IData)(vlSelfRef.alu__DOT__alu_op))
                                               ? (vlSelfRef.alu__DOT__operand_a 
                                                  << 
                                                  (0x0000001fU 
                                                   & vlSelfRef.alu__DOT__operand_b))
                                               : (vlSelfRef.alu__DOT__operand_a 
                                                  ^ vlSelfRef.alu__DOT__operand_b)))
                                       : ((2U & (IData)(vlSelfRef.alu__DOT__alu_op))
                                           ? ((1U & (IData)(vlSelfRef.alu__DOT__alu_op))
                                               ? (vlSelfRef.alu__DOT__operand_a 
                                                  | vlSelfRef.alu__DOT__operand_b)
                                               : (vlSelfRef.alu__DOT__operand_a 
                                                  & vlSelfRef.alu__DOT__operand_b))
                                           : ((1U & (IData)(vlSelfRef.alu__DOT__alu_op))
                                               ? (vlSelfRef.alu__DOT__operand_a 
                                                  - vlSelfRef.alu__DOT__operand_b)
                                               : (vlSelfRef.alu__DOT__operand_a 
                                                  + vlSelfRef.alu__DOT__operand_b)))));
    vlSelfRef.alu__DOT__zero = (0U == vlSelfRef.alu__DOT__result);
    vlSelfRef.result = vlSelfRef.alu__DOT__result;
    vlSelfRef.zero = vlSelfRef.alu__DOT__zero;
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
                Vtop___024root___ico_sequent__TOP__0(vlSelf);
            }
        }
    }
    return (__VicoExecute);
}

void Vtop___024root___eval(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __VicoIterCount;
    // Body
    __VicoIterCount = 0U;
    vlSelfRef.__VicoFirstIteration = 1U;
    do {
        if (VL_UNLIKELY(((0x00002710U < __VicoIterCount)))) {
#ifdef VL_DEBUG
            Vtop___024root___dump_triggers__ico(vlSelfRef.__VicoTriggered, "ico"s);
#endif
            VL_FATAL_MT("/home/ayanna/projects/riscv-cordic/src/alu.sv", 1, "", "DIDNOTCONVERGE: Input combinational region did not converge after '--converge-limit' of 10000 tries");
        }
        __VicoIterCount = ((IData)(1U) + __VicoIterCount);
        vlSelfRef.__VicoPhaseResult = Vtop___024root___eval_phase__ico(vlSelf);
        vlSelfRef.__VicoFirstIteration = 0U;
    } while (vlSelfRef.__VicoPhaseResult);
}

#ifdef VL_DEBUG
void Vtop___024root___eval_debug_assertions(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_debug_assertions\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if (VL_UNLIKELY(((vlSelfRef.alu_op & 0xf0U)))) {
        Verilated::overWidthError("alu_op");
    }
}
#endif  // VL_DEBUG
