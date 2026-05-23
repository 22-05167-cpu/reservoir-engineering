"""Tests for Tracy prediction method and saturation models.

Validates against Example 12-4 from the textbook.
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))

from models.saturation import (
    compute_oil_saturation,
    compute_gas_saturation,
    bubble_point_transition,
    compute_saturations_water_influx,
    compute_saturations_gas_cap,
)
from models.undersaturated import (
    effective_compressibility,
    undersaturated_cumulative_production,
)
from models.relative_permeability import (
    field_relperm_from_gor,
    RelpermInterpolator,
)
from models.tracy import tracy_predict


def approx(expected, actual, rel_tol=0.05):
    if abs(expected) < 1e-15:
        return abs(actual) < 1e-10
    return abs(actual - expected) / abs(expected) <= rel_tol


def test_oil_saturation_volumetric():
    """Example 12-2: So and Sg for known depletion."""
    Swi = 0.20
    Boi = 1.5
    Bo = 1.38
    Np_frac = 0.10

    So = compute_oil_saturation(Np_frac, Bo, Boi, Swi)
    Sg = compute_gas_saturation(So, Swi)

    assert approx(0.662, So, 0.01), f"So={So}, expected 0.662"
    assert approx(0.138, Sg, 0.01), f"Sg={Sg}, expected 0.138"


def test_undersaturated_compressibility():
    """Example 12-3: effective compressibility."""
    So = 0.7
    Swi = 0.30
    co = 15e-6
    cw = 3e-6
    cf = 5e-6

    ce = effective_compressibility(So, Swi, co, cw, cf)
    expected_ce = 23.43e-6
    assert approx(expected_ce, ce, 0.01), f"ce={ce}, expected {expected_ce}"


def test_undersaturated_production():
    """Example 12-3: Np at 3500 psi (delta_p=500)."""
    N = 85e6
    Boi = 1.40
    Bo = 1.414
    ce = 23.43e-6
    pi = 4000
    p = 3500

    Np = undersaturated_cumulative_production(N, Boi, Bo, ce, pi, p)
    expected_Np = 985180
    assert approx(expected_Np, Np, 0.02), f"Np={Np}, expected {expected_Np}"


def test_field_relperm():
    """Eq 12-17: compute krg/kro from GOR data."""
    GOR = 1936
    Rs = 1280
    mu_o = 1.3
    mu_g = 0.0125
    Bo = 1.35
    Bg = 0.001518

    krg_kro = field_relperm_from_gor(GOR, Rs, mu_o, mu_g, Bo, Bg)
    assert krg_kro > 0, f"krg_kro should be positive, got {krg_kro}"


def test_relperm_interpolator_table():
    interp = RelpermInterpolator(
        Sg_values=[0.0, 0.02, 0.04, 0.06, 0.08, 0.10],
        krg_kro_values=[0.0, 0.001, 0.004, 0.01, 0.03, 0.08],
    )
    assert interp(0.0) == 0.0
    assert interp(0.05) > 0
    assert interp(0.10) > interp(0.02)


def test_relperm_interpolator_exponential():
    interp = RelpermInterpolator()
    interp.set_exponential(0.007, 11.513)
    assert interp(-0.01) == 0.0
    assert interp(0.10) > interp(0.05)
    assert interp(0.05) > 0


def test_tracy_example_12_4():
    """Tracy's method against Example 12-4 (p.834-838) with N=15 MMSTB."""
    pvt_table = {
        "p": np.array([4350, 4150, 3950, 3750, 3550, 3350], dtype=float),
        "Bo": np.array([1.43, 1.420, 1.395, 1.380, 1.360, 1.345], dtype=float),
        "Bg": np.array(
            [0.00069, 0.00071, 0.00074, 0.00078, 0.00081, 0.00085], dtype=float
        ),
        "Rs": np.array([840, 820, 770, 730, 680, 640], dtype=float),
    }
    mu_table = {
        "p": np.array([4350, 4150, 3950, 3750, 3550, 3350], dtype=float),
        "mu_o": np.array([1.7, 1.7, 1.7, 1.7, 1.7, 1.7], dtype=float),
        "mu_g": np.array([0.023, 0.023, 0.023, 0.023, 0.023, 0.023], dtype=float),
    }

    Sg_krgkro = [
        (0.000, 0.0),
        (0.005, 0.00005),
        (0.007, 0.00008),
        (0.010, 0.0002),
        (0.020, 0.001),
        (0.040, 0.004),
        (0.060, 0.01),
        (0.080, 0.03),
        (0.100, 0.08),
        (0.120, 0.15),
        (0.150, 0.35),
    ]

    N = 15e6
    Swi = 0.30
    pi = 4350
    pb = 4350
    psi_abandonment = 3350

    df = tracy_predict(
        N=N,
        Swi=Swi,
        pvt_table=pvt_table,
        Sg_krgkro_table=Sg_krgkro,
        pi=pi,
        pb=pb,
        psi_abandonment=psi_abandonment,
        mu_table=mu_table,
        tolerance=1.0,
        max_iter=50,
    )

    assert df is not None
    assert len(df) > 0

    saturated_rows = df[df["is_saturated"]].sort_values("p", ascending=False)

    if len(saturated_rows) > 0:
        first = saturated_rows.iloc[0]
        assert first["Np"] > 0
        assert first["So"] > 0
        assert first["Sg"] > 0

        expected_Np_norm = {
            4150: 0.00292,
            3950: 0.0110,
            3750: 0.0230,
            3550: 0.0356,
            3350: 0.0460,
        }

        for p_val, expected_frac in expected_Np_norm.items():
            match = saturated_rows[saturated_rows["p"] == p_val]
            if len(match) > 0:
                actual_frac = match.iloc[0]["Np"] / N
                assert approx(expected_frac, actual_frac, 0.15), (
                    f"At p={p_val}: Np_frac={actual_frac:.6f}, expected {expected_frac:.6f}"
                )


def test_tracy_monotonic_np():
    """Np should increase as pressure decreases."""
    pvt_table = {
        "p": np.array([4350, 4150, 3950, 3750, 3550, 3350], dtype=float),
        "Bo": np.array([1.43, 1.420, 1.395, 1.380, 1.360, 1.345], dtype=float),
        "Bg": np.array(
            [0.00069, 0.00071, 0.00074, 0.00078, 0.00081, 0.00085], dtype=float
        ),
        "Rs": np.array([840, 820, 770, 730, 680, 640], dtype=float),
    }
    mu_table = {
        "p": np.array([4350, 4150, 3950, 3750, 3550, 3350], dtype=float),
        "mu_o": np.array([1.7, 1.7, 1.7, 1.7, 1.7, 1.7], dtype=float),
        "mu_g": np.array([0.023, 0.023, 0.023, 0.023, 0.023, 0.023], dtype=float),
    }
    Sg_krgkro = [(0.0, 0.0), (0.05, 0.005), (0.10, 0.05), (0.15, 0.20)]

    df = tracy_predict(
        N=15e6,
        Swi=0.30,
        pvt_table=pvt_table,
        Sg_krgkro_table=Sg_krgkro,
        pi=4350,
        pb=4350,
        psi_abandonment=3350,
        mu_table=mu_table,
    )

    sat = df[df["is_saturated"]].sort_values("p", ascending=False)
    if len(sat) > 1:
        np_vals = sat["Np"].values
        for j in range(1, len(np_vals)):
            assert np_vals[j] >= np_vals[j - 1] - 1, (
                f"Np not monotonic at index {j}: {np_vals[j - 1]} -> {np_vals[j]}"
            )


def test_tracy_zero_production():
    """No production when no pressure drop."""
    pvt_table = {
        "p": np.array([4350], dtype=float),
        "Bo": np.array([1.43], dtype=float),
        "Bg": np.array([0.00069], dtype=float),
        "Rs": np.array([840], dtype=float),
    }
    Sg_krgkro = [(0.0, 0.0)]

    df = tracy_predict(
        N=15e6,
        Swi=0.30,
        pvt_table=pvt_table,
        Sg_krgkro_table=Sg_krgkro,
        pi=4350,
        pb=4350,
        psi_abandonment=4350,
    )
    assert df is not None
    if len(df) > 0:
        assert df["Np"].iloc[-1] == 0


def test_bubble_point_transition():
    Ni = 100e6
    Np_pb = 1.5e6
    Boi_at_pi = 1.3
    Bo_at_pb = 1.31
    Swi = 0.25
    cw = 3e-6
    cf = 5e-6
    pi = 4000
    pb = 3330

    result = bubble_point_transition(
        Ni, Np_pb, Boi_at_pi, Bo_at_pb, Swi, cw, cf, pi, pb
    )
    assert result["Nb"] > 0
    assert result["Soi_at_pb"] > 0
    assert result["Swi_at_pb"] > 0
    assert abs(result["Soi_at_pb"] + result["Swi_at_pb"] - 1.0) < 1e-10


def test_saturation_water_influx():
    Np_frac = 0.1
    Bo = 1.38
    Boi = 1.5
    Swi = 0.20
    We = 1e6
    Wp = 0
    Bw = 1.0
    Sorw = 0.25
    NBoi = 100e6 * 1.5

    So, Sg = compute_saturations_water_influx(
        Np_frac, Bo, Boi, Swi, We, Wp, Bw, Sorw, NBoi
    )
    assert 0 <= So <= 1
    assert 0 <= Sg <= 1 - Swi
    assert abs(So + Sg + Swi - 1.0) < 1e-10


def test_saturation_gas_cap():
    Np_frac = 0.05
    Bo = 1.35
    Boi = 1.4
    Swi = 0.20
    Bg = 0.0015
    Bgi = 0.001
    m = 0.4
    Sorg = 0.20
    NBoi = 100e6 * 1.4

    So, Sg = compute_saturations_gas_cap(Np_frac, Bo, Boi, Bg, Bgi, Swi, m, Sorg, NBoi)
    assert 0 <= So <= 1
    assert 0 <= Sg <= 1 - Swi
    assert abs(So + Sg + Swi - 1.0) < 1e-10


def test_saturation_gas_cap_no_gas():
    Np_frac = 0.1
    Bo = 1.3
    Boi = 1.4
    Swi = 0.20
    Bg = 0.0008
    Bgi = 0.001
    m = 0.0001
    Sorg = 0.20
    NBoi = 100e6 * 1.4

    So, Sg = compute_saturations_gas_cap(Np_frac, Bo, Boi, Bg, Bgi, Swi, m, Sorg, NBoi)
    expected_So = (1 - Swi) * (1 - Np_frac) * (Bo / Boi)
    assert approx(expected_So, So, 0.001)


if __name__ == "__main__":
    test_oil_saturation_volumetric()
    test_undersaturated_compressibility()
    test_undersaturated_production()
    test_field_relperm()
    test_relperm_interpolator_table()
    test_relperm_interpolator_exponential()
    test_tracy_example_12_4()
    test_tracy_monotonic_np()
    test_tracy_zero_production()
    test_bubble_point_transition()
    test_saturation_water_influx()
    test_saturation_gas_cap()
    test_saturation_gas_cap_no_gas()
    print("All tests passed!")
