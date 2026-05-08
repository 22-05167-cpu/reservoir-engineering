import pytest

from mbe_solver import solve_mbe


def test_case_1_base_saturated_solve_N():
    """
    Test Case 1: The standard verified problem from the teacher's notes.
    Scenario: Saturated, Combination Drive (Water + Gas Cap).
    Solving for Initial Oil-In-Place (N).
    Expected: ~36.59 MMSTB (Using the physically correct formula).
    """
    known = {
        "Np": 5e6,
        "Rp": 1100,
        "Rsi": 600,
        "Rs": 500,
        "Bo": 1.33,
        "Bg": 0.0015,
        "We": 3e6,
        "Wp": 2e5,
        "Bw": 1.0,
        "Boi": 1.35,
        "m": 0.2,
        "Bgi": 0.0011,
        "deltaP": 500,
    }
    forced = ["cw", "cf", "Swi"]  # Expansion inactive

    result = solve_mbe(target_var="N", known_values=known, forced_zeros=forced)

    assert result["success"] is True
    assert result["result"] == pytest.approx(36_593_625.50, rel=1e-4)


def test_case_2_solution_gas_drive_only():
    """
    Test Case 2: Saturated, Solution Gas Drive ONLY.
    Scenario: The client's notes state that if there is no water drive
    and no gas cap, We=0 and m=0.
    """
    known = {
        "Np": 5e6,
        "Rp": 1100,
        "Rsi": 600,
        "Rs": 500,
        "Bo": 1.33,
        "Bg": 0.0015,
        "Boi": 1.35,
        "Bw": 1.0,
        "Bgi": 0.0011,
        "deltaP": 500,
    }
    # Force Water Drive and Gas Cap off
    forced = ["We", "Wp", "m", "cw", "cf", "Swi"]

    result = solve_mbe(target_var="N", known_values=known, forced_zeros=forced)

    # Numerator: 5e6 * [1.33 + (1100-500)*0.0015] = 11,150,000
    # Denominator: (1.33 - 1.35) + (600-500)*0.0015 = 0.13
    # N = 11,150,000 / 0.13 = 85,769,230.77
    assert result["success"] is True
    assert result["result"] == pytest.approx(85_769_230.77, rel=1e-4)


def test_case_3_solve_for_water_influx():
    """
    Test Case 3: Predicting Water Influx (We).
    Scenario: The client's notes explicitly asked to solve for We when N is known.
    We inject the N from Test Case 1 and see if it correctly finds We = 3,000,000.
    """
    known = {
        "N": 36_593_625.50,
        "Np": 5e6,
        "Rp": 1100,
        "Rsi": 600,
        "Rs": 500,
        "Bo": 1.33,
        "Bg": 0.0015,
        "Wp": 2e5,
        "Bw": 1.0,
        "Boi": 1.35,
        "m": 0.2,
        "Bgi": 0.0011,
        "deltaP": 500,
    }
    forced = ["cw", "cf", "Swi"]

    result = solve_mbe(target_var="We", known_values=known, forced_zeros=forced)

    assert result["success"] is True
    assert result["result"] == pytest.approx(3_000_000.0, rel=1e-3)


def test_case_4_solve_for_gas_cap_size():
    """
    Test Case 4: Estimating Gas Cap Size (m).
    Scenario: The client's notes explicitly asked to solve for m when N is known.
    We inject the N from Test Case 1 and see if it correctly finds m = 0.2.
    """
    known = {
        "N": 36_593_625.50,
        "Np": 5e6,
        "Rp": 1100,
        "Rsi": 600,
        "Rs": 500,
        "Bo": 1.33,
        "Bg": 0.0015,
        "We": 3e6,
        "Wp": 2e5,
        "Bw": 1.0,
        "Boi": 1.35,
        "Bgi": 0.0011,
        "deltaP": 500,
    }
    forced = ["cw", "cf", "Swi"]

    result = solve_mbe(target_var="m", known_values=known, forced_zeros=forced)

    assert result["success"] is True
    assert result["result"] == pytest.approx(0.2, rel=1e-3)


def test_case_5_unsaturated_reservoir_logic():
    """
    Test Case 5: Unsaturated Reservoir (p > pb).
    Scenario: The client's notes state that for unsaturated reservoirs,
    m = 0 and Rp = Rsi (evolved gas is 0). It relies entirely on fluid/rock expansion.
    """
    known = {
        "Np": 1e6,
        "Bo": 1.26,
        "Boi": 1.25,
        "Rsi": 400,
        "Rs": 400,
        "Rp": 400,  # Rp forced to equal Rsi
        "deltaP": 1000,
        "Swi": 0.25,
        "cw": 3e-6,
        "cf": 4e-6,
        "Bg": 0.001,
        "Bgi": 0.001,
        "Bw": 1.0,  # arbitrary, shouldn't affect math
    }
    # Force Gas Cap and Water Drive off
    forced = ["m", "We", "Wp"]

    result = solve_mbe(target_var="N", known_values=known, forced_zeros=forced)

    # Hand Calc verification:
    # Efw = 1.25 * (1+0) * [(0.25*3e-6 + 4e-6) / (1-0.25)] * 1000 = 0.0079166...
    # Denom = (1.26 - 1.25) + 0 + Efw = 0.0179166...
    # Num = 1e6 * [1.26 + 0] = 1,260,000
    # N = 1,260,000 / 0.0179166... = 70,325,581.39

    assert result["success"] is True
    assert result["result"] == pytest.approx(70_325_581.39, rel=1e-4)
