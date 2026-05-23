"""
results.py — Renders MBE calculation results in the Streamlit UI.

This module handles the display of:
  - Success banner and execution timer
  - Prominent result display for the solved variable
  - Recovery Factor computation and display
  - Drive mechanism analysis text
  - Drive-index pie chart using Plotly
  - Summary data table of all variables
  - CSV export download button
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from mbe_solver import compute_drive_indices
from config import OIL_VARS, GAS_VARS


def render_results(
    result: dict,
    target_var: str,
    forced_zeros: list,
    all_vals: dict,
    t_elapsed: float,
    var_info: dict,
    all_vars: list,
    fluid_type: str = "oil",
    df=None,
) -> None:
    is_gas = fluid_type == "gas"
    has_time_series = df is not None and len(df) > 1

    if not result["success"]:
        if has_time_series:
            st.warning(
                f"Single-point solver note: {result['error_message']}. "
                "Time-series plots are generated below using the uploaded data."
            )
        else:
            st.error(f"Calculation failed: {result['error_message']}")
        return

    st.success("Calculation successful!")
    st.caption(f"\u23f1\ufe0f Calculation completed in {t_elapsed:.4f} seconds")

    solved_value = result["result"]

    if target_var == "N":
        display_str = f"{solved_value:,.2f} STB"
        if abs(solved_value) >= 1e6:
            display_str += f" &nbsp;|&nbsp; **{solved_value / 1e6:.2f} MMSTB**"
    elif target_var == "We":
        display_str = f"{solved_value:,.2f} bbl"
    elif target_var == "m":
        display_str = f"{solved_value:.4f} (dimensionless)"
    elif target_var == "deltaP":
        display_str = f"{solved_value:,.2f} psi"
    elif target_var == "G":
        display_str = f"{solved_value:,.2f} Mscf"
        if abs(solved_value) >= 1e6:
            display_str += f" &nbsp;|&nbsp; **{solved_value / 1e6:.2f} MMscf**"
    else:
        display_str = f"{solved_value}"

    st.markdown(
        f"<h2 style='color:#1f77b4;'>{target_var} = {display_str}</h2>",
        unsafe_allow_html=True,
    )

    # ── Metric row ─────────────────────────────────────────────────────
    mechanism = _classify_drive(is_gas, all_vals)
    rf_str, we_str, m_str = "", "", ""
    if not is_gas:
        N_val = all_vals.get("N")
        Np_val = all_vals.get("Np")
        if N_val is not None and N_val != 0:
            rf_pct = (Np_val / N_val) * 100
            rf_str = f"{rf_pct:.2f}%"

        we_v = all_vals.get("We") or 0
        if abs(we_v) >= 1e6:
            we_str = f"{we_v / 1e6:.2f} MM bbl"
        else:
            we_str = f"{we_v:,.0f} bbl"

        m_v = all_vals.get("m") or 0
        m_str = f"{m_v:.4f}"
    else:
        G_val = all_vals.get("G")
        Gp_val = all_vals.get("Gp")
        if G_val is not None and G_val != 0:
            rf_pct = (Gp_val / G_val) * 100
            rf_str = f"{rf_pct:.2f}%"
        we_v = all_vals.get("We") or 0
        we_str = f"{we_v:,.0f} bbl"
        m_str = "—"

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Recovery Factor", rf_str)
    col2.metric("Water Influx", we_str)
    if not is_gas:
        col3.metric("Gas Cap Ratio", m_str)
    else:
        col3.metric("Gas Cap Ratio", m_str)
    col4.metric("Drive Mechanism", mechanism)

    st.markdown("---")

    # ── Expander 1: Drive Indices & Insights ────────────────────────────
    with st.expander("📊  Drive Indices & Insights", expanded=False):
        _render_drive_insights(is_gas, all_vals, fluid_type, target_var)

    # ── Expander 2: Variable Summary ────────────────────────────────────
    with st.expander("📋  Variable Summary", expanded=False):
        _render_variable_summary(is_gas, all_vals, var_info, target_var, forced_zeros)


def _classify_drive(is_gas, all_vals):
    if is_gas:
        we_val = all_vals.get("We") or 0
        return "Water Drive" if we_val != 0 else "Volumetric Depletion"
    m_val = all_vals.get("m") or 0
    we_val = all_vals.get("We") or 0
    np_val = all_vals.get("Np") or 0
    bo_val = all_vals.get("Bo") or 0
    water_big = abs(we_val) > 1e6 or (
        np_val * bo_val > 0 and abs(we_val) > 0.1 * np_val * bo_val
    )
    if m_val == 0 and we_val == 0:
        return "Solution Gas Drive"
    if m_val > 0 and water_big:
        return "Combination Drive"
    if m_val > 0:
        return "Gas Cap Drive"
    if water_big:
        return "Water Drive"
    return "Solution Gas Drive"


def _render_drive_insights(is_gas, all_vals, fluid_type, target_var):
    if is_gas:
        we_val = all_vals.get("We") or 0
        if we_val == 0:
            st.markdown(
                "**Volumetric Depletion** — The gas reservoir is producing by gas expansion only."
            )
        else:
            st.markdown(
                "**Water Drive** — Significant water influx is contributing energy. Watch for water breakthrough."
            )
    else:
        m_val = all_vals.get("m") or 0
        we_val = all_vals.get("We") or 0
        np_val = all_vals.get("Np") or 0
        bo_val = all_vals.get("Bo") or 0
        water_big = abs(we_val) > 1e6 or (
            np_val * bo_val > 0 and abs(we_val) > 0.1 * np_val * bo_val
        )

        if m_val == 0 and we_val == 0:
            st.markdown(
                "**Solution Gas Drive** — Oil expansion and gas liberation are the primary energy sources. Recovery typically low (15-25%)."
            )
        elif m_val > 0 and water_big:
            st.markdown(
                "**Combination Drive** — Both gas cap (m > 0) and significant water influx are active."
            )
        elif m_val > 0:
            st.markdown(
                "**Gas Cap Drive** — The gas cap provides expansion energy. Avoid producing gas from the top of the reservoir."
            )
        elif water_big:
            st.markdown(
                "**Water Drive** — Aquifer expansion is the primary source of drive energy. High recovery but risk of early water breakthrough."
            )
        else:
            st.markdown(
                "**Solution Gas Drive** — No gas cap or water influx. Recovery typically low."
            )

    st.markdown("#### Expert Insights")
    if not is_gas:
        Rp_val = all_vals.get("Rp")
        Rsi_val = all_vals.get("Rsi")
        Np_val_expert = all_vals.get("Np")
        m_val_exp = all_vals.get("m", 0)
        we_val_exp = all_vals.get("We", 0)

        if target_var == "deltaP" and Np_val_expert is not None and Np_val_expert > 0:
            st.warning(
                "The reservoir may be tight. Pressure will likely hit the bubble point soon."
            )
        if (
            m_val_exp == 0
            and we_val_exp == 0
            and Rp_val is not None
            and Rsi_val is not None
            and Rp_val == Rsi_val
        ):
            st.warning(
                "Rock and fluid expansion is the only energy source — least efficient drive."
            )
        if Rp_val is not None and Rsi_val is not None and Rp_val > Rsi_val:
            st.warning(
                "Secondary gas saturation developed. Pressure energy is being lost through the wellbore."
            )
        st.info(
            "Plot N over time. Constant N → assumptions correct. Increasing N → unaccounted energy source. Decreasing N → overestimating energy."
        )

    st.markdown("#### Drive Indices (Energy Contribution)")
    drive_data = compute_drive_indices(all_vals, fluid_type)
    if sum(drive_data["raw"]) > 0:
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=drive_data["labels"],
                    values=drive_data["values"],
                    hole=0.4,
                    textinfo="label+percent",
                    hovertemplate="<b>%{label}</b><br>Contribution: %{percent}<br>Raw: %{customdata:,.4f}<extra></extra>",
                    customdata=drive_data["raw"],
                )
            ]
        )
        fig.update_layout(
            title_text="Relative Energy Contributions", showlegend=True, height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No drive terms active. Enable a drive mechanism in the sidebar.")


def _render_variable_summary(is_gas, all_vals, var_info, target_var, forced_zeros):
    vars_to_display = GAS_VARS if is_gas else OIL_VARS
    display_rows = []
    export_rows = []
    for var in vars_to_display:
        val = all_vals.get(var)
        info = var_info[var]
        status = (
            "Target"
            if var == target_var
            else ("Forced Zero" if (forced_zeros and var in forced_zeros) else "Input")
        )
        val_str = (
            "\u2014"
            if val is None
            else (
                f"{val:.2e}"
                if var in ("cw", "cf")
                else (
                    f"{val:.6f}"
                    if var in ("Bg", "Bgi")
                    else (f"{val:.4f}" if var == "m" else f"{val:,.4f}")
                )
            )
        )
        display_rows.append(
            {
                "Variable": var,
                "Description": info["label"].split(" \u2013 ")[-1],
                "Value": val_str,
                "Status": status,
            }
        )
        export_rows.append(
            {
                "Variable": var,
                "Description": info["label"].split(" \u2013 ")[-1],
                "Value": val,
                "Status": status,
            }
        )

    st.dataframe(pd.DataFrame(display_rows), use_container_width=True, hide_index=True)
    csv_data = pd.DataFrame(export_rows).to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Summary as CSV",
        data=csv_data,
        file_name="mbe_results.csv",
        mime="text/csv",
        key="download_results",
    )
