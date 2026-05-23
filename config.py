"""
config.py — Centralized constants and symbols for the MBE application.

Shared constants extracted from app.py and mbe_solver.py so that both
modules (and any future modules) reference a single source of truth.
"""

import sympy as sp

var_info = {
    "N": {"label": "N – Initial Oil-In-Place (STB)", "default": 0.0, "format": "%.2f"},
    "Np": {
        "label": "Np – Cumulative Oil Produced (STB)",
        "default": 0.0,
        "format": "%.2f",
    },
    "Bo": {"label": "Bo – Current Oil FVF (bbl/STB)", "default": 1.0, "format": "%.4f"},
    "Boi": {
        "label": "Boi – Initial Oil FVF (bbl/STB)",
        "default": 1.0,
        "format": "%.4f",
    },
    "Rp": {
        "label": "Rp – Cumulative Produced GOR (scf/STB)",
        "default": 0.0,
        "format": "%.2f",
    },
    "Rsi": {
        "label": "Rsi – Initial Solution GOR (scf/STB)",
        "default": 0.0,
        "format": "%.2f",
    },
    "Rs": {
        "label": "Rs – Current Solution GOR (scf/STB)",
        "default": 0.0,
        "format": "%.2f",
    },
    "Bg": {
        "label": "Bg – Current Gas FVF (bbl/scf)",
        "default": 0.001,
        "format": "%.6f",
    },
    "Bgi": {
        "label": "Bgi – Initial Gas FVF (bbl/scf)",
        "default": 0.001,
        "format": "%.6f",
    },
    "We": {
        "label": "We – Cumulative Water Influx (bbl)",
        "default": 0.0,
        "format": "%.2f",
    },
    "Wp": {
        "label": "Wp – Cumulative Water Produced (bbl)",
        "default": 0.0,
        "format": "%.2f",
    },
    "Bw": {"label": "Bw – Water FVF (bbl/STB)", "default": 1.0, "format": "%.4f"},
    "m": {
        "label": "m – Gas Cap Ratio (dimensionless)",
        "default": 0.0,
        "format": "%.4f",
    },
    "Swi": {
        "label": "Swi – Initial Water Saturation (decimal)",
        "default": 0.2,
        "format": "%.4f",
    },
    "cw": {
        "label": "cw – Water Compressibility (psi⁻¹)",
        "default": 0.0,
        "format": "%.2e",
    },
    "cf": {
        "label": "cf – Formation Compressibility (psi⁻¹)",
        "default": 0.0,
        "format": "%.2e",
    },
    "deltaP": {
        "label": "ΔP – Change in Pressure (psi)",
        "default": 0.0,
        "format": "%.2f",
    },
    "G": {"label": "G – Initial Gas-In-Place (Mscf)", "default": 0.0, "format": "%.2f"},
    "Gp": {
        "label": "Gp – Cumulative Gas Produced (Mscf)",
        "default": 0.0,
        "format": "%.2f",
    },
}

all_vars = list(var_info.keys())

OIL_VARS = [
    "N",
    "Np",
    "Bo",
    "Boi",
    "Rp",
    "Rsi",
    "Rs",
    "Bg",
    "Bgi",
    "We",
    "Wp",
    "Bw",
    "m",
    "Swi",
    "cw",
    "cf",
    "deltaP",
]
GAS_VARS = ["G", "Gp", "Bg", "Bgi", "We", "Wp", "Bw"]

N, Np, Bo, Boi, Rp, Rsi, Rs, Bg, Bgi, We, Wp, Bw, m, Swi, cw, cf, deltaP, G, Gp = (
    sp.symbols("N Np Bo Boi Rp Rsi Rs Bg Bgi We Wp Bw m Swi cw cf deltaP G Gp")
)

SYMBOLS = {
    "N": N,
    "Np": Np,
    "Bo": Bo,
    "Boi": Boi,
    "Rp": Rp,
    "Rsi": Rsi,
    "Rs": Rs,
    "Bg": Bg,
    "Bgi": Bgi,
    "We": We,
    "Wp": Wp,
    "Bw": Bw,
    "m": m,
    "Swi": Swi,
    "cw": cw,
    "cf": cf,
    "deltaP": deltaP,
    "G": G,
    "Gp": Gp,
}

WATER_INFLUX_MODEL_DEFAULTS = {
    "pot_aquifer": {
        "re": 5000.0,
        "ra": 50000.0,
        "h": 100.0,
        "phi": 0.15,
        "theta": 180.0,
        "cw_plus_cf": 1e-5,
    },
    "schilthuis": {
        "C": 100.0,
    },
    "veh": {
        "re": 5000.0,
        "ra": 50000.0,
        "h": 100.0,
        "phi": 0.15,
        "k": 200.0,
        "mu_w": 0.5,
        "ct": 1e-5,
        "theta": 180.0,
    },
}
