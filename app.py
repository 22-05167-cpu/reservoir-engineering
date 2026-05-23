import time

import streamlit as st

from config import all_vars, var_info
from mbe_solver import solve_mbe
from ui.data_input import render_manual_input, render_manual_time_series_table
from ui.results import render_results
from ui.rp_sensitivity import render_rp_sensitivity
from ui.sidebar import render_sidebar
from ui.time_series import render_time_series

st.set_page_config(
    page_title="Reservoir Engineering MBE Tool",
    layout="wide",
    initial_sidebar_state="expanded",
)

FLOAT_VARS = set(var_info.keys())


def _build_water_influx_params(model_type):
    if model_type == "pot_aquifer":
        return {
            "re": st.session_state.get("wf_pa_re", 5000),
            "ra": st.session_state.get("wf_pa_ra", 50000),
            "h": st.session_state.get("wf_pa_h", 100),
            "phi": st.session_state.get("wf_pa_phi", 0.15),
            "theta": st.session_state.get("wf_pa_theta", 180),
            "cw_plus_cf": st.session_state.get("wf_pa_ct", 1e-5),
        }
    if model_type == "schilthuis":
        return {
            "C": st.session_state.get("wf_sch_c", 100),
        }
    if model_type == "veh":
        return {
            "re": st.session_state.get("wf_veh_re", 5000),
            "ra": st.session_state.get("wf_veh_ra", 50000),
            "h": st.session_state.get("wf_veh_h", 100),
            "phi": st.session_state.get("wf_veh_phi", 0.15),
            "k": st.session_state.get("wf_veh_k", 200),
            "mu_w": st.session_state.get("wf_veh_mu", 0.5),
            "ct": st.session_state.get("wf_veh_ct", 1e-5),
            "theta": st.session_state.get("wf_veh_theta", 180),
        }
    return {}


def _hydrate_from_query_params():
    params = st.query_params.to_dict()
    if not params:
        return False

    hydrated = st.session_state.get("_url_hydrated", False)
    if hydrated:
        return params.get("auto_calculate") == "true"

    sidebar_map = {
        "fluid_type": "sidebar_fluid_type",
        "target_var": "sidebar_target_var",
        "reservoir_state": "sidebar_reservoir_state",
        "water_drive_active": "sidebar_water_drive",
        "gas_cap_active": "sidebar_gas_cap",
        "expansion_active": "sidebar_expansion",
    }
    sidebar_bool = {"sidebar_water_drive", "sidebar_gas_cap", "sidebar_expansion"}

    sidebar_fluid_map = {
        "oil": "Oil Reservoir",
        "Oil": "Oil Reservoir",
        "Oil Reservoir": "Oil Reservoir",
        "gas": "Gas Reservoir",
        "Gas": "Gas Reservoir",
        "Gas Reservoir": "Gas Reservoir",
    }
    sidebar_state_map = {
        "saturated": "Saturated Reservoir (p ≤ pb)",
        "Saturated": "Saturated Reservoir (p ≤ pb)",
        "unsaturated": "Unsaturated Reservoir (p > pb)",
        "Unsaturated": "Unsaturated Reservoir (p > pb)",
    }

    for param_key, param_val_list in params.items():
        val = param_val_list[0] if isinstance(param_val_list, list) else param_val_list

        if param_key == "auto_calculate":
            continue

        if param_key in sidebar_map:
            ss_key = sidebar_map[param_key]
            if ss_key == "sidebar_fluid_type":
                st.session_state[ss_key] = sidebar_fluid_map.get(val, "Oil Reservoir")
            elif ss_key == "sidebar_reservoir_state":
                st.session_state[ss_key] = sidebar_state_map.get(
                    val, "Saturated Reservoir (p ≤ pb)"
                )
            elif ss_key in sidebar_bool:
                st.session_state[ss_key] = val.lower() == "true"
            else:
                st.session_state[ss_key] = val
            continue

        if param_key in FLOAT_VARS:
            try:
                st.session_state[f"manual_{param_key}"] = float(val)
            except (ValueError, TypeError):
                pass
            continue

    st.session_state["_url_hydrated"] = True

    try:
        st.query_params.clear()
    except Exception:
        pass

    return params.get("auto_calculate") == "true"


auto_calculate = _hydrate_from_query_params()

st.title("Reservoir Engineering: Material Balance Equation (MBE) Solver")
st.markdown("---")

config = render_sidebar()
target_var = config["target_var"]
fluid_type = config["fluid_type"]
is_unsaturated = config["is_unsaturated"]
forced_zeros = config["forced_zeros"]

st.header("Data Input")

known_values = {}
df = None
col_map = {}

manual_result = render_manual_input(
    var_info, target_var, forced_zeros, is_unsaturated, fluid_type
)
known_values = manual_result["known_values"]
ts_result = render_manual_time_series_table(
    var_info, known_values, fluid_type, is_unsaturated
)
df = ts_result["df"]
col_map = ts_result["col_map"]

st.markdown("---")
st.header("Results")

trigger_calc = st.button("Calculate", type="primary") or auto_calculate

cfg_fingerprint = (
    config["target_var"],
    config["fluid_type"],
    config["is_unsaturated"],
    tuple(sorted(config["forced_zeros"])),
)
if cfg_fingerprint != st.session_state.get("_prev_cfg_fp"):
    st.session_state["calculated"] = False

input_fingerprint = (tuple(sorted((k, v) for k, v in known_values.items())),)
if input_fingerprint != st.session_state.get("_prev_inp_fp"):
    st.session_state["calculated"] = False

if trigger_calc:
    if not known_values and not auto_calculate:
        st.error("Please provide input values before calculating.")
        st.stop()

    for var in forced_zeros:
        known_values[var] = 0.0

    if fluid_type != "gas" and is_unsaturated:
        if "Rsi" in known_values:
            known_values["Rp"] = known_values["Rsi"]
            known_values["Rs"] = known_values["Rsi"]
        elif "Rp" in known_values:
            known_values["Rsi"] = known_values["Rp"]
            known_values["Rs"] = known_values["Rp"]
        else:
            st.error(
                "For an unsaturated reservoir, Rsi (and therefore Rp) must be provided."
            )
            st.stop()

    if target_var in known_values:
        del known_values[target_var]

    with st.spinner("Solving Material Balance Equation..."):
        t_start = time.perf_counter()
        result = solve_mbe(target_var, known_values, forced_zeros, fluid_type)
        t_elapsed = time.perf_counter() - t_start

    all_vals = result.get("all_values", {})
    for k, v in known_values.items():
        if k not in all_vals:
            all_vals[k] = v

    st.session_state["calculated"] = True
    st.session_state["results_data"] = {
        "result": result,
        "target_var": target_var,
        "forced_zeros": forced_zeros,
        "all_vals": all_vals,
        "t_elapsed": t_elapsed,
        "fluid_type": fluid_type,
        "is_unsaturated": is_unsaturated,
        "df": df,
        "col_map": col_map,
    }
    st.session_state["_prev_cfg_fp"] = cfg_fingerprint
    st.session_state["_prev_inp_fp"] = input_fingerprint

    if auto_calculate:
        auto_calculate = False

if st.session_state.get("calculated", False):
    rd = st.session_state["results_data"]
    _df = rd.get("df")
    _col_map = rd.get("col_map", {})

    wf_model = st.session_state.get("sidebar_water_influx_model", "none")
    wf_params = _build_water_influx_params(wf_model)

    render_results(
        rd["result"],
        rd["target_var"],
        rd["forced_zeros"],
        rd["all_vals"],
        rd["t_elapsed"],
        var_info,
        all_vars,
        rd["fluid_type"],
        df=_df,
    )
    if _df is not None and len(_df) > 1:
        render_time_series(
            _df,
            _col_map,
            rd["forced_zeros"],
            rd["fluid_type"],
            rd["is_unsaturated"],
            rd["all_vals"],
            water_influx_model=wf_model,
            water_influx_params=wf_params,
        )

    if rd["fluid_type"] == "oil" and not rd["is_unsaturated"]:
        st.markdown("---")
        render_rp_sensitivity(rd["all_vals"])
