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
    fluid_type: str = 'oil',
) -> None:
    is_gas = (fluid_type == 'gas')

    if not result['success']:
        st.error(f"Calculation failed: {result['error_message']}")
        return

    st.success("Calculation successful!")
    st.caption(f"\u23f1\ufe0f Calculation completed in {t_elapsed:.4f} seconds")

    res = result['result']

    if target_var == 'N':
        display_str = f"{res:,.2f} STB"
        if abs(res) >= 1e6:
            display_str += f" &nbsp;|&nbsp; **{res/1e6:.2f} MMSTB**"
    elif target_var == 'We':
        display_str = f"{res:,.2f} bbl"
    elif target_var == 'm':
        display_str = f"{res:.4f} (dimensionless)"
    elif target_var == 'deltaP':
        display_str = f"{res:,.2f} psi"
    elif target_var == 'G':
        display_str = f"{res:,.2f} Mscf"
        if abs(res) >= 1e6:
            display_str += f" &nbsp;|&nbsp; **{res/1e6:.2f} MMscf**"
    else:
        display_str = f"{res}"

    st.markdown(
        f"<h2 style='color:#1f77b4;'>{target_var} = {display_str}</h2>",
        unsafe_allow_html=True,
    )

    if not is_gas:
        N_val = all_vals.get('N')
        Np_val = all_vals.get('Np')
        if N_val is not None and N_val != 0:
            rf = (Np_val / N_val) * 100
            st.markdown(
                f"<h3 style='color:#2ca02c;'>Recovery Factor (Rf) = {rf:.2f}%</h3>",
                unsafe_allow_html=True,
            )

    st.subheader("Drive Mechanism Analysis")

    if is_gas:
        we_val = all_vals.get('We') or 0
        if we_val == 0:
            mechanism = "Volumetric Depletion"
            explanation = (
                "The gas reservoir is producing by gas expansion only. "
                "No water influx is contributing. This is the simplest "
                "gas reservoir behavior."
            )
        else:
            mechanism = "Water Drive"
            explanation = (
                "Significant water influx is observed, indicating that aquifer "
                "expansion is contributing to reservoir drive energy. "
                "Strong Aquifer present. Watch for water breakthrough."
            )
    else:
        m_val = all_vals.get('m') or 0
        we_val = all_vals.get('We') or 0
        np_val = all_vals.get('Np') or 0
        bo_val = all_vals.get('Bo') or 0

        water_is_significant = abs(we_val) > 1e6 or (
            np_val * bo_val > 0 and abs(we_val) > 0.1 * np_val * bo_val
        )

        if m_val == 0 and we_val == 0:
            mechanism = "Solution Gas Drive"
            explanation = (
                "The reservoir is producing primarily due to expansion of the oil "
                "and liberation of dissolved gas. Neither a gas cap nor significant "
                "water influx is contributing to drive energy. "
                "Expect recovery factors to be low (15-25%) unless secondary "
                "recovery is implemented."
            )
        elif m_val > 0 and water_is_significant:
            mechanism = "Combination Drive"
            explanation = (
                "Both a gas cap (m > 0) and significant water influx are active, "
                "providing combined expansion energy that drives oil toward the wellbore."
            )
        elif m_val > 0:
            mechanism = "Gas Cap Drive"
            explanation = (
                "A gas cap is present (m > 0) and provides significant expansion "
                "energy that helps drive oil toward the wellbore. "
                "Gas Cap is the primary engine. Avoid producing gas from the top "
                "of the reservoir to save this energy."
            )
        elif water_is_significant:
            mechanism = "Water Drive"
            explanation = (
                "Significant water influx is observed, indicating that aquifer "
                "expansion is the primary source of reservoir drive energy. "
                "Strong Aquifer present. This means high recovery but a risk of "
                "early water breakthrough in the wells."
            )
        else:
            mechanism = "Solution Gas Drive"
            explanation = (
                "The reservoir is producing primarily due to expansion of the oil "
                "and liberation of dissolved gas. "
                "Expect recovery factors to be low (15-25%) unless secondary "
                "recovery is implemented."
            )

    st.markdown(f"**Primary Drive Mechanism: {mechanism}**")
    st.caption(explanation)

    if not is_gas:
        st.subheader("Expert Insights & Recommendations")

        Rp_val = all_vals.get('Rp')
        Rsi_val = all_vals.get('Rsi')
        deltaP_val = all_vals.get('deltaP')
        Np_val_expert = all_vals.get('Np')
        m_val = all_vals.get('m', 0)
        we_val = all_vals.get('We', 0)

        if target_var == 'deltaP' and Np_val_expert is not None and Np_val_expert > 0:
            st.warning(
                "Unsaturated Reservoir interpretation: The reservoir is 'tight' or "
                "has very little natural energy. Pressure will likely hit the "
                "bubble point soon."
            )

        if m_val == 0 and we_val == 0 and Rp_val is not None and Rsi_val is not None and Rp_val == Rsi_val:
            st.warning(
                "Rock and Fluid Expansion is the only energy source. "
                "This is the least efficient drive."
            )

        if Rp_val is not None and Rsi_val is not None and Rp_val > Rsi_val:
            st.warning(
                "The reservoir has developed Secondary Gas Saturation. "
                "You are losing your 'pressure engine' through the wellbore."
            )

        st.info(
            "Tip for Trend Analysis: To verify your assumed Drive Mechanisms "
            "(m and We), plot N over time. A Constant N means assumptions are "
            "correct. An Increasing N means an unaccounted energy source "
            "(larger aquifer/gas cap). A Decreasing N means you are "
            "overestimating the energy."
        )

    st.subheader("Drive Indices (Energy Contribution)")
    drive_data = compute_drive_indices(all_vals, fluid_type)

    if sum(drive_data['raw']) > 0:
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=drive_data['labels'],
                    values=drive_data['values'],
                    hole=0.4,
                    textinfo='label+percent',
                    hovertemplate=(
                        "<b>%{label}</b><br>"
                        "Contribution: %{percent}<br>"
                        "Raw magnitude: %{customdata:,.4f}<extra></extra>"
                    ),
                    customdata=drive_data['raw'],
                )
            ]
        )
        fig.update_layout(
            title_text="Relative Energy Contributions",
            showlegend=True,
            height=500,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(
            "No drive terms are active (all forced to zero). "
            "Enable a drive mechanism in the sidebar to see the chart."
        )

    st.subheader("Summary of All Variables")

    vars_to_display = GAS_VARS if is_gas else OIL_VARS
    display_rows = []
    export_rows = []
    for var in vars_to_display:
        val = all_vals.get(var)
        info = var_info[var]

        status = (
            'Target' if var == target_var
            else ('Forced Zero' if (forced_zeros and var in forced_zeros)
                  else 'Input')
        )

        if val is None:
            val_str = "\u2014"
        elif var in ('cw', 'cf'):
            val_str = f"{val:.2e}"
        elif var in ('Bg', 'Bgi'):
            val_str = f"{val:.6f}"
        elif var == 'm':
            val_str = f"{val:.4f}"
        else:
            val_str = f"{val:,.4f}"

        display_rows.append({
            'Variable': var,
            'Description': info['label'].split(' \u2013 ')[-1],
            'Value': val_str,
            'Status': status,
        })

        export_rows.append({
            'Variable': var,
            'Description': info['label'].split(' \u2013 ')[-1],
            'Value': val,
            'Status': status,
        })

    df_summary = pd.DataFrame(display_rows)
    st.dataframe(df_summary, use_container_width=True, hide_index=True)

    st.subheader("Export Results")
    df_export = pd.DataFrame(export_rows)
    csv_data = df_export.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Summary as CSV",
        data=csv_data,
        file_name="mbe_results.csv",
        mime="text/csv",
        key="download_results",
    )
