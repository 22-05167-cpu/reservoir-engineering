"""Pot-aquifer water influx model.

Ch 11 Eq 11-45, Ch 3 Eq 3.27.
We = (cw + cf) * Wi * f * (pi - p)
"""

import numpy as np


def pot_aquifer_we(pi, p_current, re, ra, h, phi, theta, cw_plus_cf):
    """Compute cumulative water influx from pot-aquifer geometry.

    Parameters
    ----------
    pi : float
        Initial reservoir pressure (psi).
    p_current : float
        Current reservoir pressure (psi).
    re : float
        Reservoir radius (ft).
    ra : float
        Aquifer radius (ft).
    h : float
        Aquifer thickness (ft).
    phi : float
        Aquifer porosity (fraction).
    theta : float
        Encroachment angle (degrees, 360 = full circle).
    cw_plus_cf : float
        Total aquifer compressibility = cw + cf (psi^-1).

    Returns
    -------
    float
        Cumulative water influx We (bbl).
    """
    if pi <= p_current:
        return 0.0
    if ra <= re:
        return 0.0

    dp = pi - p_current
    f = theta / 360.0
    Wi = np.pi * (ra**2 - re**2) * h * phi / 5.615
    return cw_plus_cf * Wi * f * dp


def pot_aquifer_series(pi, p_history, re, ra, h, phi, theta, cw_plus_cf):
    """Compute We at each pressure step.

    Returns list of We values (bbl) same length as p_history.
    """
    return [pot_aquifer_we(pi, p, re, ra, h, phi, theta, cw_plus_cf) for p in p_history]
