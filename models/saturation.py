import numpy as np


def compute_oil_saturation(Np_frac, Bo, Boi, Swi):
    """Eq 12-15: oil saturation for volumetric depletion drive.

    Np_frac = Np / N (fractional recovery, 0 to 1)
    """
    return (1.0 - Swi) * (1.0 - Np_frac) * (Bo / Boi)


def compute_gas_saturation(So, Swi):
    """Eq 12-16: gas saturation from oil and water saturations."""
    return 1.0 - So - Swi


def compute_saturations_water_influx(Np_frac, Bo, Boi, Swi, We, Wp, Bw, Sorw, NBoi):
    """Eq 12-20: oil saturation adjusted for water influx.

    Np_frac: fractional recovery Np/N
    Sorw: residual oil saturation in water-invaded zone (imbibition)
    NBoi: N * Boi (initial hydrocarbon volume)
    """
    net_water = We - Wp * Bw
    if net_water <= 0:
        So = compute_oil_saturation(Np_frac, Bo, Boi, Swi)
        Sg = compute_gas_saturation(So, Swi)
        return So, Sg

    denom = 1.0 - Swi - Sorw
    if denom <= 0:
        So = compute_oil_saturation(Np_frac, Bo, Boi, Swi)
        Sg = compute_gas_saturation(So, Swi)
        return So, Sg

    PV_water = net_water / denom
    oil_trapped = PV_water * Sorw
    pore_volume = NBoi / (1.0 - Swi)
    remaining_pv = pore_volume - PV_water

    if remaining_pv <= 0:
        So = 0.0
        Sg = 0.0
        return So, Sg

    remaining_oil = (1.0 - Np_frac) * NBoi / (1.0 - Swi) * (1.0 - Swi) * (Bo / Boi)

    total_oil = remaining_oil - oil_trapped
    So = total_oil / remaining_pv
    So = max(0.0, So)
    Sg = 1.0 - So - Swi
    Sg = max(0.0, Sg)
    return So, Sg


def compute_saturations_gas_cap(Np_frac, Bo, Boi, Bg, Bgi, Swi, m, Sorg, NBoi):
    """Eq 12-24: oil saturation adjusted for gas-cap expansion.

    m: gas cap ratio
    Sorg: residual oil saturation in gas-invaded zone
    NBoi: N * Boi
    """
    gas_cap_expansion = m * NBoi * (Bg / Bgi - 1.0)
    if gas_cap_expansion <= 0:
        So = compute_oil_saturation(Np_frac, Bo, Boi, Swi)
        Sg = compute_gas_saturation(So, Swi)
        return So, Sg

    denom = 1.0 - Swi - Sorg
    if denom <= 0:
        So = compute_oil_saturation(Np_frac, Bo, Boi, Swi)
        Sg = compute_gas_saturation(So, Swi)
        return So, Sg

    PV_gas = gas_cap_expansion / denom
    oil_trapped = PV_gas * Sorg
    pore_volume = NBoi / (1.0 - Swi)

    remaining_oil = (1.0 - Np_frac) * NBoi * Bo / Boi
    total_oil = remaining_oil - oil_trapped
    remaining_pv = pore_volume

    So = total_oil / remaining_pv
    So = max(0.0, So)
    Sg = 1.0 - So - Swi
    Sg = max(0.0, Sg)
    return So, Sg


def compute_saturations_combination(
    Np_frac, Bo, Boi, Bg, Bgi, Swi, m, We, Wp, Bw, Sorw, Sorg, NBoi
):
    """Eq 12-25: oil saturation for combination drive (water + gas cap)."""
    pore_volume = NBoi / (1.0 - Swi)
    net_water = We - Wp * Bw

    pv_water = 0.0
    if net_water > 0 and (1.0 - Swi - Sorw) > 0:
        pv_water = net_water / (1.0 - Swi - Sorw)

    gas_cap_expansion = 0.0
    pv_gas = 0.0
    if m > 0 and Bgi > 0:
        gas_cap_expansion = m * NBoi * (Bg / Bgi - 1.0)
        if gas_cap_expansion > 0 and (1.0 - Swi - Sorg) > 0:
            pv_gas = gas_cap_expansion / (1.0 - Swi - Sorg)

    oil_trapped = pv_water * Sorw + pv_gas * Sorg
    remaining_oil = (1.0 - Np_frac) * NBoi * Bo / Boi
    remaining_pv = pore_volume - pv_water - pv_gas

    if remaining_pv <= 0:
        So = 0.0
        Sg = 0.0
        return So, Sg

    total_oil = remaining_oil - oil_trapped
    So = total_oil / remaining_pv
    So = max(0.0, So)
    Sg = 1.0 - So - Swi
    Sg = max(0.0, Sg)
    return So, Sg


def bubble_point_transition(Ni, Np_pb, Boi_at_pi, Bo_at_pb, Swi, cw, cf, pi, pb):
    """Compute Nb and saturations at bubble point after undersaturated depletion.

    Ni: initial oil-in-place at pi (STB)
    Np_pb: cumulative oil produced at bubble point (STB)
    Returns dict with Nb, Soi_at_pb, Swi_at_pb, PV_at_pb
    """
    Nb = Ni - Np_pb

    delta_p = pi - pb
    water_exp = 1.0 + cw * delta_p
    pore_compact = cf * delta_p

    PV_at_pi = Ni * Boi_at_pi / (1.0 - Swi)
    PV_at_pb = PV_at_pi * (1.0 - pore_compact) + (Swi * PV_at_pi) * (water_exp - 1.0)

    Soi_at_pb = (Nb * Bo_at_pb) / PV_at_pb
    Swi_at_pb = 1.0 - Soi_at_pb

    return {
        "Nb": Nb,
        "Soi_at_pb": Soi_at_pb,
        "Swi_at_pb": Swi_at_pb,
        "PV_at_pb": PV_at_pb,
    }
