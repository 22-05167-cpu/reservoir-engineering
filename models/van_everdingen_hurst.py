"""Van Everdingen-Hurst unsteady-state water influx model.

Ch 11 Eq 11-50, 11-51.
We = B * sum(Delta_p * WeD(tD, rD)) via superposition.
"""

import numpy as np
from scipy.interpolate import RegularGridInterpolator

INF_TD = np.array(
    [
        0.001,
        0.005,
        0.01,
        0.02,
        0.03,
        0.05,
        0.07,
        0.10,
        0.20,
        0.30,
        0.50,
        0.70,
        1.0,
        2.0,
        3.0,
        5.0,
        7.0,
        10.0,
        20.0,
        30.0,
        50.0,
        70.0,
        100.0,
        200.0,
        500.0,
        1000.0,
    ],
    dtype=float,
)

INF_WED = np.array(
    [
        0.0356,
        0.0805,
        0.112,
        0.152,
        0.184,
        0.236,
        0.282,
        0.342,
        0.504,
        0.635,
        0.877,
        1.08,
        1.31,
        1.97,
        2.52,
        3.40,
        4.18,
        5.17,
        7.56,
        9.51,
        13.0,
        16.3,
        20.6,
        31.8,
        56.3,
        86.5,
    ],
    dtype=float,
)

FINITE_TD = np.array(
    [
        0.001,
        0.005,
        0.01,
        0.02,
        0.03,
        0.05,
        0.07,
        0.10,
        0.20,
        0.30,
        0.50,
        0.70,
        1.0,
        2.0,
        3.0,
        5.0,
        7.0,
        10.0,
        20.0,
        30.0,
        50.0,
        70.0,
        100.0,
    ],
    dtype=float,
)

FINITE_WED = {
    2: np.array(
        [
            0.035,
            0.080,
            0.111,
            0.151,
            0.182,
            0.232,
            0.276,
            0.331,
            0.471,
            0.575,
            0.737,
            0.848,
            0.944,
            1.15,
            1.25,
            1.38,
            1.44,
            1.49,
            1.50,
            1.50,
            1.50,
            1.50,
            1.50,
        ],
        dtype=float,
    ),
    3: np.array(
        [
            0.035,
            0.080,
            0.112,
            0.152,
            0.183,
            0.234,
            0.279,
            0.337,
            0.487,
            0.603,
            0.797,
            0.946,
            1.09,
            1.45,
            1.73,
            2.14,
            2.50,
            2.89,
            3.66,
            3.92,
            4.00,
            4.00,
            4.00,
        ],
        dtype=float,
    ),
    5: np.array(
        [
            0.036,
            0.080,
            0.112,
            0.152,
            0.183,
            0.235,
            0.280,
            0.339,
            0.494,
            0.616,
            0.822,
            0.989,
            1.15,
            1.61,
            1.99,
            2.72,
            3.40,
            4.32,
            7.08,
            9.16,
            11.44,
            12.00,
            12.00,
        ],
        dtype=float,
    ),
    10: np.array(
        [
            0.036,
            0.080,
            0.112,
            0.152,
            0.183,
            0.235,
            0.280,
            0.339,
            0.494,
            0.616,
            0.824,
            0.993,
            1.16,
            1.63,
            2.03,
            2.80,
            3.55,
            4.60,
            8.14,
            11.1,
            16.6,
            21.0,
            27.0,
        ],
        dtype=float,
    ),
}


def _weD_infinite(tD):
    """WeD for infinite-acting aquifer (rD = inf)."""
    scalar_input = np.isscalar(tD)
    tD_arr = np.atleast_1d(np.asarray(tD, dtype=float))
    result = np.interp(tD_arr, INF_TD, INF_WED)
    early_mask = tD_arr < INF_TD[0]
    if np.any(early_mask):
        result = np.where(early_mask, 1.128 * np.sqrt(tD_arr), result)
    return float(result.item()) if scalar_input else result


def _weD_finite(tD, rD):
    """WeD for finite aquifer with given rD."""
    scalar_input = np.isscalar(tD)
    tD_arr = np.atleast_1d(np.asarray(tD, dtype=float))
    rD_values = np.array(sorted(FINITE_WED.keys()))
    idx = np.argmin(np.abs(rD_values - rD))
    nearest_rD = rD_values[idx]
    result = np.interp(tD_arr, FINITE_TD, FINITE_WED[nearest_rD])
    early_mask = tD_arr < FINITE_TD[0]
    if np.any(early_mask):
        result = np.where(early_mask, 1.128 * np.sqrt(tD_arr), result)
    return float(result.item()) if scalar_input else result


def weD(tD, rD):
    """Dimensionless water influx WeD for constant terminal pressure.

    Parameters
    ----------
    tD : float
        Dimensionless time.
    rD : float
        Dimensionless aquifer radius (ra / re). Use 0 for infinite.

    Returns
    -------
    float
        WeD value.
    """
    if rD <= 0:
        return _weD_infinite(tD)
    finite_max = (rD**2 - 1.0) / 2.0
    wed_val = _weD_finite(tD, rD)
    return min(wed_val, finite_max)


def veh_we(re, ra, h, phi, k, mu_w, ct, theta, pi, p_history, t_history):
    """Compute cumulative water influx via VEH unsteady-state model.

    Uses superposition in time.

    Parameters
    ----------
    re : float
        Reservoir radius (ft).
    ra : float
        Aquifer radius (ft).
    h : float
        Aquifer thickness (ft).
    phi : float
        Aquifer porosity (fraction).
    k : float
        Aquifer permeability (md).
    mu_w : float
        Water viscosity (cp).
    ct : float
        Total compressibility cw + cf (psi^-1).
    theta : float
        Encroachment angle (degrees).
    pi : float
        Initial reservoir pressure (psi).
    p_history : array-like
        Pressures at each observation time (psi).
    t_history : array-like
        Cumulative times (days).

    Returns
    -------
    np.ndarray
        Cumulative We (bbl) at each time step.
    """
    p = np.asarray(p_history, dtype=float)
    t = np.asarray(t_history, dtype=float)
    n = len(t)
    rD = ra / re if ra > re else 10.0

    B = 1.119 * phi * ct * (re**2) * h * (theta / 360.0)

    we_values = np.zeros(n)

    dp_drops = np.zeros(n)
    dp_drops[0] = pi - p[0]
    for i in range(1, n):
        dp_drops[i] = p[i - 1] - p[i]

    tD_vals = 0.006328 * k * t / (phi * mu_w * ct * (re**2))

    for i in range(n):
        we_super = 0.0
        for j in range(i + 1):
            dtD = tD_vals[i] - (tD_vals[j - 1] if j > 0 else 0.0)
            if dtD <= 0:
                continue
            we_super += dp_drops[j] * weD(dtD, rD)
        we_values[i] = B * we_super

    return we_values
