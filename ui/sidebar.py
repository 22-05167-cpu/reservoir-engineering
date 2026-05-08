import streamlit as st


def render_sidebar() -> dict:
    st.sidebar.header("Configuration")

    fluid_type = st.sidebar.radio(
        "Fluid Type",
        options=["Oil Reservoir", "Gas Reservoir"],
        horizontal=True,
        key="sidebar_fluid_type",
    )
    is_gas = (fluid_type == "Gas Reservoir")

    if is_gas:
        target_var = st.sidebar.selectbox(
            "What do you want to solve for?",
            options=['G', 'We'],
            format_func=lambda x: {
                'G':  'G  (Initial Gas-In-Place)',
                'We': 'We (Water Influx)',
            }[x],
            key="sidebar_target_var",
        )
        is_unsaturated = False
        reservoir_state = None
    else:
        target_var = st.sidebar.selectbox(
            "What do you want to solve for?",
            options=['N', 'We', 'm', 'deltaP'],
            format_func=lambda x: {
                'N':      'N  (Initial Oil-In-Place)',
                'We':     'We (Water Influx)',
                'm':      'm  (Size of Initial Gas Cap)',
                'deltaP': 'ΔP (Change in Pressure)'
            }[x],
            key="sidebar_target_var",
        )

        reservoir_state = st.sidebar.radio(
            "Reservoir State",
            options=["Saturated Reservoir (p ≤ pb)", "Unsaturated Reservoir (p > pb)"],
            key="sidebar_reservoir_state",
        )
        is_unsaturated = (reservoir_state == "Unsaturated Reservoir (p > pb)")

    st.sidebar.markdown("---")
    st.sidebar.subheader("Drive Mechanisms")

    water_drive_active = st.sidebar.checkbox("Water Drive Active?", value=False, key="sidebar_water_drive")

    if is_gas:
        gas_cap_active = False
        expansion_active = False
    else:
        gas_cap_active = st.sidebar.checkbox("Gas Cap Active?", value=False, key="sidebar_gas_cap")
        expansion_active = st.sidebar.checkbox("Rock & Water Expansion Active?", value=False, key="sidebar_expansion")

    forced_zeros = []
    if not is_gas and is_unsaturated:
        forced_zeros.extend(['m', 'Bg', 'Bgi', 'Rsi', 'Rs'])
    if not water_drive_active:
        forced_zeros.extend(['We', 'Wp', 'Bw'])
    if not is_gas and not gas_cap_active:
        forced_zeros.extend(['m', 'Bgi'])
    if not is_gas and not expansion_active:
        forced_zeros.extend(['cw', 'cf', 'Swi'])
        if target_var != 'deltaP':
            forced_zeros.append('deltaP')
    forced_zeros = list(dict.fromkeys(forced_zeros))

    return {
        'target_var': target_var,
        'fluid_type': 'gas' if is_gas else 'oil',
        'is_unsaturated': is_unsaturated,
        'forced_zeros': forced_zeros,
        'water_drive_active': water_drive_active,
        'gas_cap_active': gas_cap_active,
        'expansion_active': expansion_active,
    }
