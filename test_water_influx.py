"""Tests for water influx models and pressure estimation (Ch 11, 3)."""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))

from models.pot_aquifer import pot_aquifer_we, pot_aquifer_series
from models.schilthuis import schilthuis_we
from models.van_everdingen_hurst import veh_we, weD
from models.water_influx import (
    compute_water_influx,
    compute_water_influx_series,
    WATER_INFLUX_MODELS,
)
from models.pressure_estimate import estimate_average_pressure


def approx(a, b, rel_tol=0.01):
    if abs(b) < 1e-15:
        return abs(a) < 1e-10
    return abs(a - b) / max(abs(b), 1e-15) <= rel_tol


# ─── Pot-Aquifer ────────────────────────────────────────────────────────────


def test_pot_aquifer_zero_dp():
    assert pot_aquifer_we(4000, 4000, 5000, 50000, 100, 0.15, 180, 1e-5) == 0.0


def test_pot_aquifer_no_aquifer():
    assert pot_aquifer_we(4000, 3500, 5000, 5000, 100, 0.15, 180, 1e-5) == 0.0


def test_pot_aquifer_symmetric():
    we_180 = pot_aquifer_we(4000, 3500, 5000, 50000, 100, 0.15, 180, 1e-5)
    we_360 = pot_aquifer_we(4000, 3500, 5000, 50000, 100, 0.15, 360, 1e-5)
    assert approx(we_360, 2 * we_180), f"{we_360} != 2*{we_180}"


def test_pot_aquifer_positive():
    we = pot_aquifer_we(4000, 3500, 5000, 50000, 100, 0.15, 360, 1e-5)
    assert we > 0


def test_pot_aquifer_series():
    p_hist = [4000, 3800, 3600, 3400]
    vals = pot_aquifer_series(4000, p_hist, 5000, 50000, 100, 0.15, 360, 1e-5)
    assert len(vals) == 4
    assert vals[0] == 0.0
    assert vals[1] > 0
    assert vals[2] > vals[1]
    assert vals[3] > vals[2]


# ─── Schilthuis ─────────────────────────────────────────────────────────────


def test_schilthuis_constant_pressure():
    p_hist = [4000, 4000, 4000]
    t_hist = [0, 100, 200]
    we = schilthuis_we(100, 4000, p_hist, t_hist)
    assert all(w == 0 for w in we)


def test_schilthuis_linear_decline():
    p_hist = [4000, 3950, 3900]
    t_hist = [0, 365, 730]
    we = schilthuis_we(50, 4000, p_hist, t_hist)
    assert we[0] == 0.0
    assert we[-1] > we[1] > 0
    expected = 50 * (365 * 25 + 365 * 75)
    assert approx(we[-1], expected, 0.001), f"{we[-1]} != {expected}"


def test_schilthuis_increasing_time():
    p_hist = [4000, 3900]
    t_hist = [0, 10]
    we = schilthuis_we(10, 4000, p_hist, t_hist)
    assert we[-1] > 0


# ─── VEH ────────────────────────────────────────────────────────────────────


def test_veh_weD_infinite():
    assert weD(0.001, 0) > 0
    assert weD(1.0, 0) > 0
    assert weD(100.0, 0) > weD(1.0, 0)


def test_veh_weD_finite_limited():
    wed_2 = weD(1000.0, 2)
    assert wed_2 <= (4 - 1) / 2 * 1.1


def test_veh_zero_dp():
    p_hist = [4000, 4000, 4000]
    t_hist = [0, 100, 200]
    we = veh_we(5000, 50000, 100, 0.15, 200, 0.5, 1e-5, 180, 4000, p_hist, t_hist)
    assert all(w == 0 for w in we)


def test_veh_positive():
    p_hist = [4000, 3950, 3900]
    t_hist = [0, 365, 730]
    we = veh_we(5000, 50000, 100, 0.15, 200, 0.5, 1e-5, 180, 4000, p_hist, t_hist)
    assert we[-1] > 0
    assert we[-1] >= we[1]


# ─── Dispatch ───────────────────────────────────────────────────────────────


def test_dispatch_none():
    assert compute_water_influx(None, {}, [4000]) == 0.0
    assert compute_water_influx("none", {}, [4000]) == 0.0


def test_dispatch_pot_aquifer():
    we = compute_water_influx(
        "pot_aquifer",
        {
            "pi": 4000,
            "re": 5000,
            "ra": 50000,
            "h": 100,
            "phi": 0.15,
            "theta": 360,
            "cw_plus_cf": 1e-5,
        },
        [4000, 3500],
    )
    assert we > 0


def test_dispatch_schilthuis():
    we = compute_water_influx(
        "schilthuis",
        {"pi": 4000, "C": 50},
        [4000, 3950],
        t_history=[0, 365],
    )
    assert we > 0


def test_dispatch_unknown():
    try:
        compute_water_influx("bogus", {}, [4000])
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_water_influx_models_listed():
    assert "pot_aquifer" in WATER_INFLUX_MODELS
    assert "schilthuis" in WATER_INFLUX_MODELS
    assert "veh" in WATER_INFLUX_MODELS


# ─── Case 6: Pressure Estimate ──────────────────────────────────────────────


def test_case6_no_production():
    pvt = {
        "p": np.array([2000, 3000, 4000]),
        "Bo": np.array([1.20, 1.25, 1.30]),
        "Bg": np.array([0.0015, 0.0012, 0.0010]),
        "Rs": np.array([400, 500, 600]),
    }
    p_est = estimate_average_pressure(
        N=10e6,
        m=0,
        pvt_table=pvt,
        production_at_time={"Np": 0, "Rp": 600, "Wp": 0},
        pi=4000,
    )
    assert approx(p_est, 4000, 0.1), f"{p_est} != 4000"


def test_case6_known_case():
    pvt = {
        "p": np.array([3000, 3200, 3400, 3600, 3800, 4000]),
        "Bo": np.array([1.25, 1.26, 1.27, 1.28, 1.29, 1.30]),
        "Bg": np.array([0.0013, 0.0012, 0.00115, 0.0011, 0.00105, 0.0010]),
        "Rs": np.array([450, 480, 510, 540, 570, 600]),
    }
    p_est = estimate_average_pressure(
        N=10e6,
        m=0.2,
        pvt_table=pvt,
        production_at_time={"Np": 1e6, "Rp": 700, "Wp": 0},
        pi=4000,
        p_min=3000,
        p_max=4000,
    )
    assert p_est > 3000
    assert p_est < 4000


if __name__ == "__main__":
    test_pot_aquifer_zero_dp()
    test_pot_aquifer_no_aquifer()
    test_pot_aquifer_symmetric()
    test_pot_aquifer_positive()
    test_pot_aquifer_series()
    test_schilthuis_constant_pressure()
    test_schilthuis_linear_decline()
    test_schilthuis_increasing_time()
    test_veh_weD_infinite()
    test_veh_weD_finite_limited()
    test_veh_zero_dp()
    test_veh_positive()
    test_dispatch_none()
    test_dispatch_pot_aquifer()
    test_dispatch_schilthuis()
    test_dispatch_unknown()
    test_water_influx_models_listed()
    test_case6_no_production()
    test_case6_known_case()
    print("All water influx tests passed!")
