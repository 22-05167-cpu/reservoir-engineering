"""
MBE Solver - Material Balance Equation math engine.
Defines the General MBE using SymPy and provides a unified solver
that can calculate any missing variable.
"""

import sympy as sp
import numpy as np
from config import (
    SYMBOLS,
    N,
    Np,
    Bo,
    Boi,
    Rp,
    Rsi,
    Rs,
    Bg,
    Bgi,
    We,
    Wp,
    Bw,
    m,
    Swi,
    cw,
    cf,
    deltaP,
    G,
    Gp,
)
from config import OIL_VARS, GAS_VARS

numerator = Np * (Bo + (Rp - Rs) * Bg) - (We - Wp * Bw)
base_denominator = (Bo - Boi) + (Rsi - Rs) * Bg + m * Boi * (Bg / Bgi - 1)
expansion_term = Boi * (1 + m) * ((Swi * cw + cf) / (1 - Swi)) * deltaP
denominator = base_denominator + expansion_term

MBE_IMPLICIT = N * denominator - numerator
gas_expansion_term = Bgi * ((Swi * cw + cf) / (1 - Swi)) * deltaP
GAS_MBE_IMPLICIT = G * (Bg - Bgi) + G * gas_expansion_term - Gp * Bg + (We - Wp * Bw)


def _error_response(message):
    return {
        "success": False,
        "result": None,
        "error_message": message,
        "all_values": {},
    }


def _get_target_symbol_and_vars(target_var, fluid_type):
    target_symbol = SYMBOLS.get(target_var)
    if target_symbol is None:
        return None, None, f"Unknown target variable: {target_var}"
    relevant_vars = GAS_VARS if fluid_type == "gas" else OIL_VARS
    return target_symbol, relevant_vars, None


def _build_substitutions(known_values, forced_zeros):
    substitutions = {}
    for var_name in forced_zeros or []:
        sym = SYMBOLS.get(var_name)
        if sym is not None:
            substitutions[sym] = 0.0
    for var_name, val in known_values.items():
        sym = SYMBOLS.get(var_name)
        if sym is not None:
            substitutions[sym] = float(val)
    return substitutions


def _get_missing_variables(substitutions, target_var, relevant_vars):
    missing = []
    for name in relevant_vars:
        if name == target_var:
            continue
        if SYMBOLS[name] not in substitutions:
            missing.append(name)
    return missing


def _has_swi_division_by_zero(substitutions, is_gas):
    if is_gas or Swi not in substitutions:
        return False
    if substitutions[Swi] != 1.0:
        return False
    cw_val = substitutions.get(cw, 0.0)
    cf_val = substitutions.get(cf, 0.0)
    return abs(float(substitutions[Swi]) * cw_val + cf_val) >= 1e-12


def _substitute_expression(implicit_eq, substitutions, is_gas):
    if not is_gas and Swi in substitutions and substitutions[Swi] == 1.0:
        expr = N * base_denominator - numerator
    else:
        expr = implicit_eq
    for sym, val in substitutions.items():
        expr = expr.subs(sym, val)
    return sp.simplify(expr)


def _check_solvability(expr, target_symbol):
    if expr.has(sp.zoo, sp.oo, sp.nan, -sp.oo):
        return False, "Division by zero or undefined expression after substitution"

    derivative = sp.diff(expr, target_symbol)
    if derivative == 0:
        if sp.simplify(expr) == 0:
            return False, f"Target variable cancels out; infinite solutions exist"
        return False, f"Target variable cancels out; equation is inconsistent"

    return True, None


def _solve_algebraically(expr, target_symbol):
    solutions = sp.solve(expr, target_symbol)
    if not solutions:
        return None

    if isinstance(solutions, dict):
        solutions = [solutions.get(target_symbol)]

    for sol in solutions:
        if sol is None:
            continue
        if hasattr(sol, "is_real") and sol.is_real:
            return float(sol)
        if not hasattr(sol, "evalf"):
            continue
        val = complex(sol.evalf())
        if abs(val.imag) < 1e-10 and not (np.isnan(val.real) or np.isinf(val.real)):
            return float(val.real)

    return None


def _solve_numerically(expr, target_symbol):
    guesses = [1e-6, 1e-3, 0.1, 1.0, 10.0, 100.0, 1e3, 1e4, 1e5, 1e6, 1e9]
    for guess in guesses:
        try:
            sol = sp.nsolve(expr, target_symbol, guess, tol=1e-10, maxsteps=100)
            if isinstance(sol, (list, dict, sp.MatrixBase)):
                continue
            candidate = float(sol)
            residual = float(expr.subs({target_symbol: candidate}))
            if abs(residual) < 1e-6:
                return candidate
        except Exception:
            continue
    return None


def _assemble_result(target_var, solved_value, substitutions, fluid_type):
    relevant_vars = GAS_VARS if fluid_type == "gas" else OIL_VARS
    all_values = {}
    for name in relevant_vars:
        sym = SYMBOLS[name]
        if name == target_var:
            all_values[name] = solved_value
        else:
            all_values[name] = substitutions.get(sym, 0.0)
    return all_values


def solve_mbe(target_var, known_values, forced_zeros=None, fluid_type="oil"):
    is_gas = fluid_type == "gas"

    target_symbol, relevant_vars, err = _get_target_symbol_and_vars(
        target_var, fluid_type
    )
    if err:
        return _error_response(err)

    substitutions = _build_substitutions(known_values, forced_zeros)
    substitutions.pop(target_symbol, None)

    missing = _get_missing_variables(substitutions, target_var, relevant_vars)
    if missing:
        return _error_response(
            f"Missing known values for variables: {', '.join(missing)}"
        )

    if _has_swi_division_by_zero(substitutions, is_gas):
        return _error_response(
            "Division by zero: Swi=1 with non-zero rock/fluid expansion term (Swi*cw + cf != 0)"
        )

    implicit_eq = GAS_MBE_IMPLICIT if is_gas else MBE_IMPLICIT
    expr_to_solve = _substitute_expression(implicit_eq, substitutions, is_gas)

    ok, err = _check_solvability(expr_to_solve, target_symbol)
    if not ok:
        return _error_response(err)

    result = _solve_algebraically(expr_to_solve, target_symbol)
    if result is None:
        result = _solve_numerically(expr_to_solve, target_symbol)

    if result is None or np.isnan(result) or np.isinf(result):
        return _error_response("No valid solution found")

    all_values = _assemble_result(target_var, result, substitutions, fluid_type)

    return {
        "success": True,
        "result": result,
        "error_message": None,
        "all_values": all_values,
    }


def compute_mbe_derived_terms(values, fluid_type="oil"):
    is_gas = fluid_type == "gas"

    if is_gas:
        G_val = values.get("G", 0)
        Bg_val = values.get("Bg", 0)
        Bgi_val = values.get("Bgi", 0)
        We_val = values.get("We", 0)
        Wp_val = values.get("Wp", 0)
        Bw_val = values.get("Bw", 0)

        net_water_influx = We_val - Wp_val * Bw_val
        gas_expansion = G_val * (Bg_val - Bgi_val)

        return {
            "gas_expansion": gas_expansion,
            "net_water_influx": net_water_influx,
            "gas_expansion_energy": abs(gas_expansion),
            "water_energy": abs(net_water_influx),
        }

    N_val = values.get("N", 0)
    Np_val = values.get("Np", 0)
    Bo_val = values.get("Bo", 0)
    Boi_val = values.get("Boi", 0)
    Rp_val = values.get("Rp", 0)
    Rsi_val = values.get("Rsi", 0)
    Rs_val = values.get("Rs", 0)
    Bg_val = values.get("Bg", 0)
    Bgi_val = values.get("Bgi", 0)
    We_val = values.get("We", 0)
    Wp_val = values.get("Wp", 0)
    Bw_val = values.get("Bw", 0)
    m_val = values.get("m", 0)
    Swi_val = values.get("Swi", 0)
    cw_val = values.get("cw", 0)
    cf_val = values.get("cf", 0)
    deltaP_val = values.get("deltaP", 0)

    oil_shrinkage = (Bo_val - Boi_val) + (Rsi_val - Rs_val) * Bg_val

    if abs(Bgi_val) < 1e-12:
        gas_cap_expansion = 0.0
    else:
        gas_cap_expansion = m_val * Boi_val * (Bg_val / Bgi_val - 1.0)

    if abs(1.0 - Swi_val) < 1e-12:
        rock_water_expansion = 0.0
    else:
        rock_water_expansion = (
            Boi_val
            * (1.0 + m_val)
            * ((Swi_val * cw_val + cf_val) / (1.0 - Swi_val))
            * deltaP_val
        )

    net_water_influx = We_val - Wp_val * Bw_val

    oil_shrinkage_energy = abs(N_val * oil_shrinkage)
    gas_cap_energy = abs(N_val * gas_cap_expansion)
    rock_water_energy = abs(N_val * rock_water_expansion)
    water_energy = abs(net_water_influx)

    numerator_val = Np_val * (Bo_val + (Rp_val - Rs_val) * Bg_val) - net_water_influx
    denominator_val = oil_shrinkage + gas_cap_expansion + rock_water_expansion

    F = Np_val * (Bo_val + (Rp_val - Rs_val) * Bg_val) + Wp_val * Bw_val
    Et = oil_shrinkage + gas_cap_expansion + rock_water_expansion

    return {
        "oil_shrinkage": oil_shrinkage,
        "gas_cap_expansion": gas_cap_expansion,
        "rock_water_expansion": rock_water_expansion,
        "net_water_influx": net_water_influx,
        "oil_shrinkage_energy": oil_shrinkage_energy,
        "gas_cap_energy": gas_cap_energy,
        "rock_water_energy": rock_water_energy,
        "water_energy": water_energy,
        "numerator": numerator_val,
        "denominator": denominator_val,
        "F": F,
        "Et": Et,
    }


def compute_drive_indices(all_values, fluid_type="oil"):
    terms = compute_mbe_derived_terms(all_values, fluid_type)
    is_gas = fluid_type == "gas"

    if is_gas:
        labels = ["Gas Expansion", "Net Water Influx"]
        raw_values = [terms["gas_expansion_energy"], terms["water_energy"]]
    else:
        labels = [
            "Oil Shrinkage / Solution Gas",
            "Gas Cap Expansion",
            "Rock & Water Expansion",
            "Net Water Influx",
        ]
        raw_values = [
            terms["oil_shrinkage_energy"],
            terms["gas_cap_energy"],
            terms["rock_water_energy"],
            terms["water_energy"],
        ]

    total = sum(raw_values)
    if total > 0:
        percentages = [100.0 * v / total for v in raw_values]
    else:
        percentages = [0.0] * len(raw_values)

    return {"labels": labels, "values": percentages, "raw": raw_values}
