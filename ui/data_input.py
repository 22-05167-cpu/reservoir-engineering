import streamlit as st
import pandas as pd

from config import OIL_VARS, GAS_VARS


def _get_display_order(fluid_type):
    if fluid_type == 'gas':
        return GAS_VARS
    return OIL_VARS


def render_manual_input(var_info: dict, target_var: str, forced_zeros: list, is_unsaturated: bool, fluid_type: str = 'oil') -> dict:
    st.subheader("Enter Known Variables")

    col_left, col_right = st.columns(2)

    display_order = _get_display_order(fluid_type)

    known_values = {}
    for idx, var in enumerate(display_order):
        if var == target_var:
            continue
        if var in forced_zeros:
            continue
        if fluid_type != 'gas' and is_unsaturated and var in ('Rp', 'Rs'):
            continue

        info = var_info[var]
        container = col_left if idx % 2 == 0 else col_right
        min_val = 0.0 if var not in ('deltaP',) else None

        val = container.number_input(
            info['label'],
            value=info['default'],
            format=info['format'],
            min_value=min_val,
            key=f"manual_{var}"
        )
        known_values[var] = val

    if fluid_type != 'gas' and is_unsaturated:
        if 'Rsi' in known_values:
            known_values['Rp'] = known_values['Rsi']
            known_values['Rs'] = known_values['Rsi']
        else:
            known_values['Rp'] = 0.0
            known_values['Rs'] = 0.0

    return {'known_values': known_values}


def render_file_upload(var_info: dict, target_var: str, forced_zeros: list, is_unsaturated: bool, fluid_type: str = 'oil') -> dict:
    st.subheader("Upload Data File")

    uploaded_file = st.file_uploader(
        "Upload CSV or Excel file",
        type=['csv', 'xlsx', 'xls']
    )

    if uploaded_file is None:
        st.info("Please upload a file to proceed.")
        return {'known_values': {}, 'df': None, 'col_map': {}}

    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.success(
        f"Loaded file: {len(df)} row(s), "
        f"columns: {', '.join(df.columns.astype(str))}"
    )

    col_map = {}
    for col in df.columns:
        col_clean = col.strip().lower()
        for var in var_info.keys():
            if col_clean == var.lower():
                col_map[var] = col
                break

    if col_map:
        st.write("**Mapped columns:**")
        st.json(col_map)
    else:
        st.warning(
            "No recognized columns found. Expected one of: "
            + ", ".join(var_info.keys())
        )

    if len(df) > 1:
        st.info("Multi-row file detected – time-series charts will be generated below.")

    display_order = _get_display_order(fluid_type)

    known_values = {}
    for var in display_order:
        if var == target_var:
            continue
        if var in forced_zeros:
            continue
        if var not in col_map:
            continue

        try:
            known_values[var] = float(df[col_map[var]].iloc[0])
        except Exception:
            st.warning(f"Could not read value for '{var}' from column '{col_map[var]}'.")

    if fluid_type != 'gas' and is_unsaturated:
        if 'Rsi' in known_values:
            known_values['Rp'] = known_values['Rsi']
            known_values['Rs'] = known_values['Rsi']
        elif 'Rp' in known_values and 'Rsi' not in known_values:
            known_values['Rsi'] = known_values['Rp']
            known_values['Rs'] = known_values['Rp']

    return {'known_values': known_values, 'df': df, 'col_map': col_map}
