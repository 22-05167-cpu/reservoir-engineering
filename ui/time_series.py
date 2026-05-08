import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from havlena_odeh import compute_havlena_odeh_f_et


def render_time_series(df, col_map: dict) -> None:
    if df is None or len(df) <= 1:
        return

    st.markdown("---")
    st.header("Time-Series Analysis")

    dp_col = col_map.get('deltaP')
    np_col = col_map.get('Np')

    if dp_col is None or np_col is None:
        st.info("Pressure vs. Cumulative Production plot requires 'deltaP' and 'Np' columns.")
    else:
        deltaP_vals = pd.to_numeric(df[dp_col], errors='coerce')
        Np_vals = pd.to_numeric(df[np_col], errors='coerce')

        mask = deltaP_vals.notna() & Np_vals.notna()
        deltaP_vals = deltaP_vals[mask]
        Np_vals = Np_vals[mask]

        fig_a = go.Figure()
        fig_a.add_trace(go.Scatter(
            x=Np_vals, y=deltaP_vals,
            mode='lines+markers',
            name='Pressure vs Np',
            line=dict(color='#d62728', width=2)
        ))
        fig_a.update_layout(
            title="Pressure Decline vs. Cumulative Oil Production",
            xaxis_title="Cumulative Oil Produced, Np (STB)",
            yaxis_title="Pressure Drop, ΔP (psi)",
            height=450
        )
        st.plotly_chart(fig_a, use_container_width=True)

    required = ['Np', 'Bo', 'Rp', 'Rsi', 'Rs', 'Bg', 'Wp', 'Bw', 'Boi', 'm', 'Bgi', 'Swi', 'cw', 'cf', 'deltaP']
    if not all(c in col_map for c in required):
        st.info("Havlena-Odeh plot requires: Np, Bo, Rp, Rsi, Rs, Bg, Wp, Bw, Boi, m, Bgi, Swi, cw, cf, deltaP columns.")
        return

    F_vals = []
    Et_vals = []
    for i in range(len(df)):
        row_values = {}
        for var_name in required:
            col = col_map.get(var_name)
            if col:
                try:
                    row_values[var_name] = float(df[col].iloc[i])
                except (ValueError, TypeError):
                    row_values[var_name] = 0.0
        ho = compute_havlena_odeh_f_et(row_values)
        F_vals.append(ho['F'])
        Et_vals.append(ho['Et'])

    fig_b = go.Figure()
    fig_b.add_trace(go.Scatter(
        x=Et_vals, y=F_vals,
        mode='markers',
        name='Data Points',
        marker=dict(color='#1f77b4', size=8)
    ))

    valid = [(et, f) for et, f in zip(Et_vals, F_vals) if not (np.isnan(et) or np.isnan(f) or np.isinf(et) or np.isinf(f))]
    if len(valid) >= 2:
        et_arr = np.array([v[0] for v in valid])
        f_arr = np.array([v[1] for v in valid])
        coeffs = np.polyfit(et_arr, f_arr, 1)
        slope, intercept = coeffs[0], coeffs[1]
        trend_x = np.linspace(et_arr.min(), et_arr.max(), 100)
        trend_y = slope * trend_x + intercept
        r2 = 1 - np.sum((f_arr - (slope * et_arr + intercept))**2) / np.sum((f_arr - f_arr.mean())**2)
        fig_b.add_trace(go.Scatter(
            x=trend_x, y=trend_y,
            mode='lines',
            name=f'Trendline (slope ≈ {slope:,.2f}, R² = {r2:.4f})',
            line=dict(color='#ff7f0e', width=2, dash='dash')
        ))

    fig_b.update_layout(
        title="Havlena-Odeh Plot: F vs. Et",
        xaxis_title="Total Expansion, Et (bbl/STB)",
        yaxis_title="Total Withdrawal, F (bbl)",
        height=500
    )
    st.plotly_chart(fig_b, use_container_width=True)

    st.markdown("""
**Havlena-Odeh Straight-Line Interpretation**

In the Havlena-Odeh straight-line method, a linear trend in the F vs. Et plot confirms that the
assumed drive mechanisms are consistent with the production history. The slope of the best-fit
line represents the **Initial Oil-in-Place (N)**. Deviations from linearity suggest that additional
or different drive mechanisms may be active.
""")
