"""Unified water influx dispatch."""

from .pot_aquifer import pot_aquifer_we, pot_aquifer_series
from .schilthuis import schilthuis_we
from .van_everdingen_hurst import veh_we


WATER_INFLUX_MODELS = {
    "pot_aquifer": {
        "label": "Pot-Aquifer Geometry",
        "params": ["re", "ra", "h", "phi", "theta", "cw_plus_cf"],
    },
    "schilthuis": {
        "label": "Schilthuis Steady-State",
        "params": ["C"],
    },
    "veh": {
        "label": "Van Everdingen-Hurst Unsteady",
        "params": ["re", "ra", "h", "phi", "k", "mu_w", "ct", "theta"],
    },
}


def compute_water_influx(model_type, params, p_history, t_history=None):
    """Compute cumulative water influx using the selected model.

    Parameters
    ----------
    model_type : str
        One of 'pot_aquifer', 'schilthuis', 'veh', or None/'none'.
    params : dict
        Model parameters dict.
    p_history : list
        Pressure history (psi).
    t_history : list, optional
        Time history (days). Required for schilthuis and veh.

    Returns
    -------
    float
        Cumulative water influx We (bbl) at the LAST time step.
    """
    if model_type is None or model_type == "none":
        return 0.0

    we_series = compute_water_influx_series(model_type, params, p_history, t_history)
    if len(we_series) == 0:
        return 0.0
    return float(we_series[-1])


def compute_water_influx_series(model_type, params, p_history, t_history=None):
    """Compute We at each time step.

    Returns list of We values (bbl), one per entry in p_history.
    """
    if model_type is None or model_type == "none":
        return [0.0] * len(p_history)

    if model_type == "pot_aquifer":
        pi = params.get("pi", p_history[0] if p_history else 0)
        return pot_aquifer_series(
            pi=pi,
            p_history=p_history,
            re=params.get("re", 5000),
            ra=params.get("ra", 50000),
            h=params.get("h", 100),
            phi=params.get("phi", 0.15),
            theta=params.get("theta", 180),
            cw_plus_cf=params.get("cw_plus_cf", 1e-5),
        )

    if model_type == "schilthuis":
        if t_history is None:
            raise ValueError("t_history required for Schilthuis model")
        pi = params.get("pi", p_history[0] if p_history else 0)
        return schilthuis_we(
            C=params.get("C", 100),
            pi=pi,
            p_history=p_history,
            t_history=t_history,
        ).tolist()

    if model_type == "veh":
        if t_history is None:
            raise ValueError("t_history required for VEH model")
        pi = params.get("pi", p_history[0] if p_history else 0)
        return veh_we(
            re=params.get("re", 5000),
            ra=params.get("ra", 50000),
            h=params.get("h", 100),
            phi=params.get("phi", 0.15),
            k=params.get("k", 200),
            mu_w=params.get("mu_w", 0.5),
            ct=params.get("ct", 1e-5),
            theta=params.get("theta", 180),
            pi=pi,
            p_history=p_history,
            t_history=t_history,
        ).tolist()

    raise ValueError(f"Unknown water influx model: {model_type}")
