import streamlit as st


def render_sidebar() -> dict:
    st.sidebar.header("Configuration")

    target_var = st.sidebar.selectbox(
        "What do you want to solve for?",
        options=['N', 'We', 'm', 'deltaP'],
        format_func=lambda x: {
            'N':      'N  (Initial Oil-In-Place)',
            'We':     'We (Water Influx)',
            'm':      'm  (Size of Initial Gas Cap)',
            'deltaP': 'ΔP (Change in Pressure)'
        }[x]
    )

    reservoir_state = st.sidebar.radio(
        "Reservoir State",
        options=["Saturated Reservoir (p ≤ pb)", "Unsaturated Reservoir (p > pb)"]
    )
    is_unsaturated = (reservoir_state == "Unsaturated Reservoir (p > pb)")

    st.sidebar.markdown("---")
    st.sidebar.subheader("Drive Mechanisms")

    water_drive_active = st.sidebar.checkbox("Water Drive Active?", value=False)
    gas_cap_active = st.sidebar.checkbox("Gas Cap Active?", value=False)
    expansion_active = st.sidebar.checkbox("Rock & Water Expansion Active?", value=False)

    forced_zeros = []
    if is_unsaturated:
        forced_zeros.extend(['m', 'Bg', 'Bgi', 'Rsi'])
    if not water_drive_active:
        forced_zeros.extend(['We', 'Wp', 'Bw'])
    if not gas_cap_active:
        forced_zeros.extend(['m', 'Bgi'])
    if not expansion_active:
        forced_zeros.extend(['cw', 'cf', 'Swi'])
        if target_var != 'deltaP':
            forced_zeros.append('deltaP')
    forced_zeros = list(set(forced_zeros))

    return {
        'target_var': target_var,
        'is_unsaturated': is_unsaturated,
        'forced_zeros': forced_zeros,
        'water_drive_active': water_drive_active,
        'gas_cap_active': gas_cap_active,
        'expansion_active': expansion_active,
    }
