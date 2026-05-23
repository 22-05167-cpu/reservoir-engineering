"""Undersaturated oil reservoir above bubble point pressure.

Eq 12-27 to 12-32 from Chapter 12.
"""


def effective_compressibility(So, Swi, co, cw, cf):
    """Eq 12-29: effective saturation-weighted compressibility.

    So, Swi: fractions (decimal)
    co, cw, cf: compressibilities (1/psi)
    Returns ce in 1/psi.
    """
    num = So * co + Swi * cw + cf
    den = 1.0 - Swi
    if den <= 0:
        raise ValueError("Swi must be less than 1")
    return num / den


def undersaturated_cumulative_production(N, Boi, Bo, ce, pi, p):
    """Eq 12-32: cumulative oil production from pi to current p (above pb).

    N: initial oil-in-place (STB)
    Boi: initial oil FVF (bbl/STB)
    Bo: current oil FVF (bbl/STB)
    ce: effective compressibility (1/psi)
    pi: initial pressure (psi)
    p: current pressure (psi)
    Returns Np in STB.
    """
    if pi <= p:
        return 0.0
    return N * ce * (Boi / Bo) * (pi - p)


def pressure_from_voidage(N, Np, Bo, Boi, ce, pi):
    """Eq 12-31: current pressure from cumulative voidage.

    Returns current pressure p (psi).
    """
    if N <= 0 or Boi <= 0 or ce <= 0:
        raise ValueError("N, Boi, and ce must be positive")
    return pi - (Np * Bo) / (N * Boi * ce)
