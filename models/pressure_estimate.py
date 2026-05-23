"""Average reservoir pressure estimation from MBE (Case 6).

Ch 11 p.802-803.
Given known N and m, find p where F(p) = RHS(p).
"""

import numpy as np


def estimate_average_pressure(
    N,
    m,
    pvt_table,
    production_at_time,
    pi,
    p_min=None,
    p_max=None,
    tol=1.0,
    max_iter=100,
):
    """Estimate average reservoir pressure from production data.

    Parameters
    ----------
    N : float
        Known initial oil-in-place (STB).
    m : float
        Known gas cap ratio.
    pvt_table : dict
        PVT data with keys 'p', 'Bo', 'Bg', 'Rs' (1D arrays, ascending by p).
    production_at_time : dict
        Production data at the target time: {Np, Gp, Rp, Wp, Bw}.
        Rp is cumulative GOR (scf/STB).
    pi : float
        Initial reservoir pressure (psi).
    p_min : float, optional
        Lower pressure bound for search. Defaults to pvt_table['p'].min().
    p_max : float, optional
        Upper pressure bound. Defaults to pi.
    tol : float
        Convergence tolerance (psi).
    max_iter : int
        Maximum iterations.

    Returns
    -------
    float
        Estimated average reservoir pressure (psi).
    """
    pvt = {k: np.array(v, dtype=float) for k, v in pvt_table.items()}
    sort_idx = np.argsort(pvt["p"])
    for k in pvt:
        pvt[k] = pvt[k][sort_idx]

    if p_min is None:
        p_min = float(pvt["p"].min())
    if p_max is None:
        p_max = float(pi)

    Np = production_at_time.get("Np", 0)
    Rp = production_at_time.get("Rp", 0)
    Gp = production_at_time.get("Gp", 0)
    Wp = production_at_time.get("Wp", 0)
    Bw = production_at_time.get("Bw", 1.0)

    Rsi = float(pvt["Rs"][-1])
    Boi = float(pvt["Bo"][-1])
    Bgi = float(pvt["Bg"][-1])

    def _pvt_at(p):
        Bo = float(np.interp(p, pvt["p"], pvt["Bo"]))
        Bg = float(np.interp(p, pvt["p"], pvt["Bg"]))
        Rs = float(np.interp(p, pvt["p"], pvt["Rs"]))
        return Bo, Bg, Rs

    def _F(p):
        Bo, Bg, Rs = _pvt_at(p)
        return Np * (Bo + (Rp - Rs) * Bg) + Wp * Bw

    def _RHS(p):
        Bo, Bg, Rs = _pvt_at(p)
        Eo = (Bo - Boi) + (Rsi - Rs) * Bg
        Eg = Boi * (Bg / Bgi - 1.0) if Bgi != 0 else 0.0
        return N * (Eo + m * Eg)

    # Bisection
    f_low = _F(p_min) - _RHS(p_min)
    f_high = _F(p_max) - _RHS(p_max)

    if f_low * f_high > 0:
        return p_min if abs(f_low) < abs(f_high) else p_max

    for _ in range(max_iter):
        p_mid = (p_min + p_max) / 2.0
        f_mid = _F(p_mid) - _RHS(p_mid)

        if abs(f_mid) < tol:
            return p_mid

        if f_low * f_mid < 0:
            p_max = p_mid
            f_high = f_mid
        else:
            p_min = p_mid
            f_low = f_mid

    return (p_min + p_max) / 2.0
