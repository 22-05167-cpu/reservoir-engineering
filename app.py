"""
Reservoir Engineering MBE Tool — Streamlit Application

This application provides an interactive web interface for solving the
General Material Balance Equation (MBE).  Users can:

  1. Select a target variable to solve for (N, We, m, deltaP, or G).
  2. Choose fluid type (Oil or Gas Reservoir).
  3. Configure reservoir state and active drive mechanisms.
  4. Enter data manually or upload a CSV/Excel file.
  5. View the calculated result, drive-mechanism analysis,
     execution timer, interactive drive-index chart, and a
     downloadable summary table.
  6. View time-series charts (Pressure vs Np, Havlena-Odeh F vs Et)
     when multi-row CSV data is uploaded.

The heavy lifting is delegated to `mbe_solver.py`, which uses SymPy to
symbolically solve the MBE for any missing variable.
"""

import time

import streamlit as st

from config import var_info, all_vars
from mbe_solver import solve_mbe
from ui.sidebar import render_sidebar
from ui.data_input import render_manual_input, render_file_upload
from ui.results import render_results
from ui.time_series import render_time_series

st.set_page_config(
    page_title="Reservoir Engineering MBE Tool",
    layout="wide",
    initial_sidebar_state="expanded"
)

FLOAT_VARS = {'N', 'Np', 'Bo', 'Boi', 'Rp', 'Rsi', 'Rs', 'Bg', 'Bgi',
              'We', 'Wp', 'Bw', 'm', 'Swi', 'cw', 'cf', 'deltaP',
              'G', 'Gp'}


def _hydrate_from_query_params():
    params = st.query_params.to_dict()
    if not params:
        return False

    hydrated = st.session_state.get('_url_hydrated', False)
    if hydrated:
        return params.get('auto_calculate') == 'true'

    sidebar_map = {
        'fluid_type': 'sidebar_fluid_type',
        'target_var': 'sidebar_target_var',
        'reservoir_state': 'sidebar_reservoir_state',
        'water_drive_active': 'sidebar_water_drive',
        'gas_cap_active': 'sidebar_gas_cap',
        'expansion_active': 'sidebar_expansion',
    }
    sidebar_bool = {'sidebar_water_drive', 'sidebar_gas_cap', 'sidebar_expansion'}

    sidebar_fluid_map = {
        'oil': 'Oil Reservoir', 'Oil': 'Oil Reservoir', 'Oil Reservoir': 'Oil Reservoir',
        'gas': 'Gas Reservoir', 'Gas': 'Gas Reservoir', 'Gas Reservoir': 'Gas Reservoir',
    }
    sidebar_state_map = {
        'saturated': 'Saturated Reservoir (p ≤ pb)',
        'Saturated': 'Saturated Reservoir (p ≤ pb)',
        'unsaturated': 'Unsaturated Reservoir (p > pb)',
        'Unsaturated': 'Unsaturated Reservoir (p > pb)',
    }

    for param_key, param_val_list in params.items():
        val = param_val_list[0] if isinstance(param_val_list, list) else param_val_list

        if param_key == 'auto_calculate':
            continue

        if param_key in sidebar_map:
            ss_key = sidebar_map[param_key]
            if ss_key == 'sidebar_fluid_type':
                st.session_state[ss_key] = sidebar_fluid_map.get(val, 'Oil Reservoir')
            elif ss_key == 'sidebar_reservoir_state':
                st.session_state[ss_key] = sidebar_state_map.get(val, 'Saturated Reservoir (p ≤ pb)')
            elif ss_key in sidebar_bool:
                st.session_state[ss_key] = (val.lower() == 'true')
            else:
                st.session_state[ss_key] = val
            continue

        if param_key in FLOAT_VARS:
            try:
                st.session_state[f"manual_{param_key}"] = float(val)
            except ValueError:
                pass
            continue

    st.session_state['_url_hydrated'] = True

    try:
        st.query_params.clear()
    except Exception:
        pass

    return params.get('auto_calculate') == 'true'


auto_calculate = _hydrate_from_query_params()

st.title("Reservoir Engineering: Material Balance Equation (MBE) Solver")
st.markdown("---")

config = render_sidebar()
target_var = config['target_var']
fluid_type = config['fluid_type']
is_unsaturated = config['is_unsaturated']
forced_zeros = config['forced_zeros']

st.header("Data Input")

input_method = st.radio(
    "Input Method",
    options=["Manual Entry", "File Upload (CSV/Excel)"],
    horizontal=True,
    key="app_input_method",
)

known_values = {}
df = None
col_map = {}

if input_method == "Manual Entry":
    manual_result = render_manual_input(var_info, target_var, forced_zeros, is_unsaturated, fluid_type)
    known_values = manual_result['known_values']
else:
    file_result = render_file_upload(var_info, target_var, forced_zeros, is_unsaturated, fluid_type)
    known_values = file_result['known_values']
    df = file_result['df']
    col_map = file_result['col_map']

st.markdown("---")
st.header("Results")

trigger_calc = st.button("Calculate", type="primary") or auto_calculate

if trigger_calc:
    if not known_values and not auto_calculate:
        st.error("Please provide input values before calculating.")
        st.stop()

    for var in forced_zeros:
        known_values[var] = 0.0

    if fluid_type != 'gas' and is_unsaturated:
        if 'Rsi' in known_values:
            known_values['Rp'] = known_values['Rsi']
            known_values['Rs'] = known_values['Rsi']
        elif 'Rp' in known_values:
            known_values['Rsi'] = known_values['Rp']
            known_values['Rs'] = known_values['Rp']
        else:
            st.error(
                "For an unsaturated reservoir, Rsi (and therefore Rp) "
                "must be provided."
            )
            st.stop()

    if target_var in known_values:
        del known_values[target_var]

    with st.spinner("Solving Material Balance Equation..."):
        t_start = time.perf_counter()
        result = solve_mbe(target_var, known_values, forced_zeros, fluid_type)
        t_elapsed = time.perf_counter() - t_start

    all_vals = result.get('all_values', {})
    render_results(result, target_var, forced_zeros, all_vals, t_elapsed, var_info, all_vars, fluid_type)

    if auto_calculate:
        auto_calculate = False

if df is not None and len(df) > 1:
    render_time_series(df, col_map)
