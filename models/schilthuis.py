"""Schilthuis steady-state water influx model.

Ch 11 Eq 11-48, 11-49.
We = C * integral(pi - p) dt via trapezoidal rule.
"""

import numpy as np


def schilthuis_we(C, pi, p_history, t_history):
    """Compute cumulative water influx using Schilthuis steady-state model.

    Parameters
    ----------
    C : float
        Water influx constant (bbl/day/psi).
    pi : float
        Initial reservoir pressure (psi).
    p_history : array-like
        Pressures at each observation time (psi).
    t_history : array-like
        Cumulative times (days), same length as p_history.

    Returns
    -------
    np.ndarray
        Cumulative We (bbl) at each time step.
    """
    if C <= 0:
        return np.zeros(len(p_history))

    p = np.asarray(p_history, dtype=float)
    t = np.asarray(t_history, dtype=float)

    dp = pi - p
    integral = np.zeros_like(t)
    for i in range(1, len(t)):
        dp_avg = (dp[i - 1] + dp[i]) / 2.0
        dt = t[i] - t[i - 1]
        if dt < 0:
            raise ValueError("t_history must be monotonically increasing")
        integral[i] = integral[i - 1] + dp_avg * dt

    return C * integral


def schilthuis_we_at_step(C, pi, p_history, t_history, step_idx):
    """Compute We at a specific step index using Schilthuis model.

    Useful when you only need the latest We value.
    """
    we_all = schilthuis_we(C, pi, p_history, t_history)
    return float(we_all[min(step_idx, len(we_all) - 1)])
