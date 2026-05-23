"""Tracy's prediction method for saturated oil reservoirs.

Implements the iterative algorithm from Chapter 12 (Tracy, 1955).
Uses PVT functions Phi_o, Phi_g to predict Np, Gp, GOR, So, Sg
vs pressure for a solution-gas-drive reservoir.
"""

import numpy as np
import pandas as pd

from .saturation import compute_oil_saturation, compute_gas_saturation
from .relative_permeability import RelpermInterpolator


def _interp_table(x_target, x_data, y_data):
    return float(np.interp(x_target, x_data, y_data))


def _sort_ascending(data_dict):
    out = {}
    arr = {k: np.array(v, dtype=float) for k, v in data_dict.items()}
    sort_idx = np.argsort(arr["p"])
    for k in arr:
        out[k] = arr[k][sort_idx]
    return out


def _pvt_at_p(p, pvt):
    Bo = _interp_table(p, pvt["p"], pvt["Bo"])
    Bg = _interp_table(p, pvt["p"], pvt["Bg"])
    Rs = _interp_table(p, pvt["p"], pvt["Rs"])
    return Bo, Bg, Rs


def tracy_pvt_functions(p, pvt, Rsi, Boi, Bgi):
    Bo, Bg, Rs = _pvt_at_p(p, pvt)
    Den = (Bo - Boi) + (Rsi - Rs) * Bg
    if abs(Den) < 1e-15:
        return 0.0, 0.0, Bo, Bg, Rs
    Phi_o = (Bo - Rs * Bg) / Den
    Phi_g = Bg / Den
    return Phi_o, Phi_g, Bo, Bg, Rs


def tracy_predict(
    N,
    Swi,
    pvt_table,
    Sg_krgkro_table,
    pi,
    pb,
    psi_abandonment,
    p_horizons=None,
    mu_table=None,
    relperm_interpolator=None,
    Np_sat_start=0.0,
    Gp_sat_start=0.0,
    tolerance=1.0,
    max_iter=50,
):
    pvt = _sort_ascending(pvt_table)

    if mu_table is not None:
        mu = _sort_ascending(mu_table)
    else:
        mu = None

    unique_p = np.unique(pvt["p"])
    if p_horizons is None:
        pressures = sorted(unique_p, reverse=True)
    else:
        pressures = sorted(p_horizons, reverse=True)
    pressures = [pr for pr in pressures if pr >= psi_abandonment]

    Rsi = float(pvt["Rs"][-1])
    Boi = float(pvt["Bo"][-1])
    Bgi = float(pvt["Bg"][-1])

    if relperm_interpolator is not None:
        relperm = relperm_interpolator
    else:
        Sg_arr = np.array([r[0] for r in Sg_krgkro_table])
        krg_arr = np.array([r[1] for r in Sg_krgkro_table])
        relperm = RelpermInterpolator(Sg_arr, krg_arr)

    rows = []
    Np_frac = Np_sat_start / N if N > 0 else 0.0
    Gp_frac = Gp_sat_start / N if N > 0 else 0.0

    if len(pressures) == 0:
        return pd.DataFrame()

    GOR_prev = Rsi

    for i, p_current in enumerate(pressures):
        if p_current >= pb - 1e-9:
            Bo, Bg, Rs = _pvt_at_p(p_current, pvt)
            rows.append(
                {
                    "p": p_current,
                    "Np": Np_frac * N,
                    "Gp": Gp_frac * N,
                    "GOR": Rsi,
                    "Rp": Rsi if Np_frac > 0 else Rsi,
                    "So": compute_oil_saturation(Np_frac, Bo, Boi, Swi),
                    "Sg": 0.0,
                    "krg_kro": 0.0,
                    "is_saturated": False,
                }
            )
            continue

        Phi_o, Phi_g, Bo, Bg, Rs = tracy_pvt_functions(p_current, pvt, Rsi, Boi, Bgi)

        if abs(Phi_g) < 1e-15 and abs(Phi_o) < 1e-15:
            continue

        if mu is not None:
            mu_o = _interp_table(p_current, mu["p"], mu["mu_o"])
            mu_g = _interp_table(p_current, mu["p"], mu["mu_g"])
        else:
            mu_o = 1.7
            mu_g = 0.023

        if i == 0 or not any(r.get("is_saturated", False) for r in rows):
            GOR_guess = Rs + 10.0
        else:
            GOR_guess = GOR_prev

        if GOR_guess <= Rs:
            GOR_guess = Rs + 10.0

        converged = False
        for iteration in range(max_iter):
            GOR_avg = (GOR_prev + GOR_guess) / 2.0
            GOR_avg = max(GOR_avg, Rs + 1.0)

            denom = Phi_o + GOR_avg * Phi_g
            if abs(denom) < 1e-15:
                GOR_guess = GOR_guess * 1.1
                continue

            delta_Np_frac = (1.0 - Np_frac * Phi_o - Gp_frac * Phi_g) / denom
            if delta_Np_frac < 0:
                delta_Np_frac = 0.0

            new_Np_frac = Np_frac + delta_Np_frac

            So = compute_oil_saturation(new_Np_frac, Bo, Boi, Swi)
            Sg = compute_gas_saturation(So, Swi)

            krg_kro = relperm(Sg)

            GOR_calc = Rs + krg_kro * (mu_o * Bo) / (mu_g * Bg) if mu_g * Bg > 0 else Rs

            residual = abs(GOR_calc - GOR_guess)
            if residual < tolerance:
                GOR_guess = GOR_calc
                converged = True
                break
            GOR_guess = GOR_calc

        GOR_final = GOR_guess
        GOR_avg = (GOR_prev + GOR_final) / 2.0
        GOR_avg = max(GOR_avg, Rs + 1.0)

        denom = Phi_o + GOR_avg * Phi_g
        if abs(denom) > 1e-15:
            delta_Np_frac = (1.0 - Np_frac * Phi_o - Gp_frac * Phi_g) / denom
        else:
            delta_Np_frac = 0.0

        if delta_Np_frac < 0:
            delta_Np_frac = 0.0

        Np_frac += delta_Np_frac
        Gp_frac += delta_Np_frac * GOR_avg

        So = compute_oil_saturation(Np_frac, Bo, Boi, Swi)
        Sg = compute_gas_saturation(So, Swi)
        krg_kro = relperm(Sg)

        Rp = Gp_frac / Np_frac if Np_frac > 0 else Rsi
        GOR_prev = GOR_final

        rows.append(
            {
                "p": p_current,
                "Np": Np_frac * N,
                "Gp": Gp_frac * N,
                "GOR": GOR_final,
                "Rp": Rp,
                "So": So,
                "Sg": Sg,
                "krg_kro": krg_kro,
                "is_saturated": True,
            }
        )

    df = pd.DataFrame(rows)

    if len(df) > 0 and N > 0:
        rf_col = (df["Np"] / N * 100).copy()
        df.loc[:, "RF"] = rf_col

    return df
