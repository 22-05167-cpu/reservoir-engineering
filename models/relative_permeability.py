"""Relative permeability ratio utilities.

Eq 12-17: field-derived krg/kro from GOR and PVT data.
"""

import numpy as np


def field_relperm_from_gor(GOR, Rs, mu_o, mu_g, Bo, Bg):
    """Eq 12-17: compute krg/kro from field instantaneous GOR.

    GOR: instantaneous producing gas-oil ratio (scf/STB)
    Rs: solution gas-oil ratio (scf/STB)
    mu_o: oil viscosity (cp)
    mu_g: gas viscosity (cp)
    Bo: oil formation volume factor (bbl/STB)
    Bg: gas formation volume factor (bbl/scf)
    """
    numerator = (GOR - Rs) * mu_g * Bg
    denominator = mu_o * Bo
    if abs(denominator) < 1e-15:
        return 0.0
    return numerator / denominator


class RelpermInterpolator:
    """Linear interpolation on Sg vs krg/kro data.

    Handles both table lookup and exponential correlation.
    """

    def __init__(self, Sg_values=None, krg_kro_values=None):
        has_data = (
            Sg_values is not None
            and krg_kro_values is not None
            and len(Sg_values) > 0
            and len(krg_kro_values) > 0
        )
        if has_data:
            self._table_Sg = np.array(Sg_values, dtype=float)
            self._table_krg_kro = np.array(krg_kro_values, dtype=float)
            idx = np.argsort(self._table_Sg)
            self._table_Sg = self._table_Sg[idx]
            self._table_krg_kro = self._table_krg_kro[idx]
            self._use_exponential = False
        else:
            self._use_exponential = True
            self._a = 0.007
            self._b = 11.513

    def set_exponential(self, a, b):
        self._use_exponential = True
        self._a = a
        self._b = b

    def __call__(self, Sg):
        if Sg <= 0.0:
            return 0.0
        if self._use_exponential:
            return self._a * np.exp(self._b * Sg)
        return float(
            np.interp(
                Sg,
                self._table_Sg,
                self._table_krg_kro,
                left=0.0,
                right=self._table_krg_kro[-1],
            )
        )
