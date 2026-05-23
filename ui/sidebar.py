import streamlit as st


def render_sidebar():
    st.sidebar.header("Configuration")

    fluid_type = st.sidebar.radio(
        "Fluid Type",
        options=["Oil Reservoir", "Gas Reservoir"],
        horizontal=True,
        key="sidebar_fluid_type",
    )
    is_gas = fluid_type == "Gas Reservoir"

    if is_gas:
        target_var = st.sidebar.selectbox(
            "What do you want to solve for?",
            options=["G", "We"],
            format_func=lambda x: {
                "G": "G  (Initial Gas-In-Place)",
                "We": "We (Water Influx)",
            }[x],
            key="sidebar_target_var",
        )
        is_unsaturated = False
    else:
        target_var = st.sidebar.selectbox(
            "What do you want to solve for?",
            options=["N", "We", "m", "deltaP"],
            format_func=lambda x: {
                "N": "N  (Initial Oil-In-Place)",
                "We": "We (Water Influx)",
                "m": "m  (Size of Initial Gas Cap)",
                "deltaP": "ΔP (Change in Pressure)",
            }[x],
            key="sidebar_target_var",
        )

        reservoir_state = st.sidebar.radio(
            "Reservoir State",
            options=["Saturated Reservoir (p ≤ pb)", "Unsaturated Reservoir (p > pb)"],
            key="sidebar_reservoir_state",
        )
        is_unsaturated = reservoir_state == "Unsaturated Reservoir (p > pb)"

    st.sidebar.markdown("---")
    st.sidebar.subheader("Drive Mechanisms")

    water_drive_active = st.sidebar.checkbox(
        "Water Drive Active?", value=False, key="sidebar_water_drive"
    )

    if water_drive_active:
        _render_water_influx_config()

    if is_gas:
        gas_cap_active = False
        expansion_active = False
    else:
        gas_cap_active = st.sidebar.checkbox(
            "Gas Cap Active?", value=False, key="sidebar_gas_cap"
        )
        expansion_active = st.sidebar.checkbox(
            "Rock & Water Expansion Active?", value=False, key="sidebar_expansion"
        )

    forced_zeros = set()

    if not is_gas and is_unsaturated:
        forced_zeros.update(["m", "Bg", "Bgi", "Rsi", "Rs"])
    if not water_drive_active:
        forced_zeros.update(["We", "Wp", "Bw"])
    if not is_gas and not gas_cap_active:
        forced_zeros.update(["m", "Bgi"])
    if not is_gas and not expansion_active:
        forced_zeros.update(["cw", "cf", "Swi"])
        if target_var != "deltaP":
            forced_zeros.add("deltaP")

    return {
        "target_var": target_var,
        "fluid_type": "gas" if is_gas else "oil",
        "is_unsaturated": is_unsaturated,
        "forced_zeros": list(forced_zeros),
        "water_drive_active": water_drive_active,
        "gas_cap_active": gas_cap_active,
        "expansion_active": expansion_active,
    }


def _render_water_influx_config():
    wf_key = "sidebar_water_influx_model"

    wf_model = st.sidebar.selectbox(
        "Water Influx Model",
        options=["none", "pot_aquifer", "schilthuis", "veh"],
        format_func=lambda x: {
            "none": "None (We = K·ΔP default)",
            "pot_aquifer": "Pot-Aquifer Geometry",
            "schilthuis": "Schilthuis Steady-State",
            "veh": "Van Everdingen-Hurst Unsteady",
        }[x],
        key=wf_key,
    )

    if wf_model == "none":
        return

    st.sidebar.markdown(f"**{wf_model.replace('_', ' ').title()} Parameters**")

    if wf_model == "pot_aquifer":
        _wf_pot_aquifer()
    elif wf_model == "schilthuis":
        _wf_schilthuis()
    elif wf_model == "veh":
        _wf_veh()


def _wf_pot_aquifer():
    st.sidebar.number_input(
        "Re (reservoir radius, ft)",
        min_value=1.0,
        value=5000.0,
        step=100.0,
        key="wf_pa_re",
    )
    st.sidebar.number_input(
        "Ra (aquifer radius, ft)",
        min_value=1.0,
        value=50000.0,
        step=1000.0,
        key="wf_pa_ra",
    )
    st.sidebar.number_input(
        "h (aquifer thickness, ft)",
        min_value=1.0,
        value=100.0,
        step=10.0,
        key="wf_pa_h",
    )
    st.sidebar.number_input(
        "phi (porosity)",
        min_value=0.0,
        max_value=1.0,
        value=0.15,
        step=0.01,
        key="wf_pa_phi",
    )
    st.sidebar.number_input(
        "theta (encroachment angle, deg)",
        min_value=0.0,
        max_value=360.0,
        value=180.0,
        step=10.0,
        key="wf_pa_theta",
    )
    st.sidebar.number_input(
        "cw+cf (total compressibility, 1/psi)",
        min_value=0.0,
        value=1e-5,
        step=1e-6,
        format="%.2e",
        key="wf_pa_ct",
    )


def _wf_schilthuis():
    st.sidebar.number_input(
        "C (water influx constant, bbl/day/psi)",
        min_value=0.0,
        value=100.0,
        step=10.0,
        key="wf_sch_c",
    )


def _wf_veh():
    st.sidebar.number_input(
        "Re (reservoir radius, ft)",
        min_value=1.0,
        value=5000.0,
        step=100.0,
        key="wf_veh_re",
    )
    st.sidebar.number_input(
        "Ra (aquifer radius, ft)",
        min_value=1.0,
        value=50000.0,
        step=1000.0,
        key="wf_veh_ra",
    )
    st.sidebar.number_input(
        "h (aquifer thickness, ft)",
        min_value=1.0,
        value=100.0,
        step=10.0,
        key="wf_veh_h",
    )
    st.sidebar.number_input(
        "phi (porosity)",
        min_value=0.0,
        max_value=1.0,
        value=0.15,
        step=0.01,
        key="wf_veh_phi",
    )
    st.sidebar.number_input(
        "k (permeability, md)", min_value=0.0, value=200.0, step=10.0, key="wf_veh_k"
    )
    st.sidebar.number_input(
        "mu_w (water viscosity, cp)",
        min_value=0.0,
        value=0.5,
        step=0.1,
        key="wf_veh_mu",
    )
    st.sidebar.number_input(
        "ct (total compressibility, 1/psi)",
        min_value=0.0,
        value=1e-5,
        step=1e-6,
        format="%.2e",
        key="wf_veh_ct",
    )
    st.sidebar.number_input(
        "theta (encroachment angle, deg)",
        min_value=0.0,
        max_value=360.0,
        value=180.0,
        step=10.0,
        key="wf_veh_theta",
    )
