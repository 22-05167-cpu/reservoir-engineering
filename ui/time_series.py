import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from mbe_solver import compute_mbe_derived_terms


def _render_gas_cap_plot(eo_values, egc_values, f_values):
    eo_array = np.array(eo_values)
    egc_array = np.array(egc_values)
    f_array = np.array(f_values)
    valid_mask = np.abs(eo_array) > 1e-12
    x_values = np.divide(egc_array[valid_mask], eo_array[valid_mask])
    y_values = np.divide(f_array[valid_mask], eo_array[valid_mask])
    finite_mask = np.isfinite(x_values) & np.isfinite(y_values)
    x_clean = x_values[finite_mask]
    y_clean = y_values[finite_mask]
    if len(x_clean) < 2:
        st.info("Not enough valid data points for F/Eo vs Egc/Eo regression.")
        return
    slope, intercept = np.polyfit(x_clean, y_clean, 1)
    n_estimated = intercept
    m_estimated = slope / intercept if abs(intercept) > 1e-12 else 0.0
    y_pred = slope * x_clean + intercept
    ss_res = np.sum((y_clean - y_pred) ** 2)
    ss_tot = np.sum((y_clean - np.mean(y_clean)) ** 2)
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_clean, y=y_clean, mode='markers', name='Data Points',
        marker=dict(color='#1f77b4', size=8),
    ))
    trend_x = np.linspace(x_clean.min(), x_clean.max(), 100)
    trend_y = slope * trend_x + intercept
    fig.add_trace(go.Scatter(
        x=trend_x, y=trend_y, mode='lines',
        name=f'Trendline (R\u00b2 = {r_squared:.4f})',
        line=dict(color='#ff7f0e', width=2, dash='dash'),
    ))
    fig.update_layout(
        title="Havlena-Odeh: F/Eo vs. Boi\u00d7(Bg/Bgi \u2212 1)/Eo (Gas Cap Drive)",
        xaxis_title="Boi\u00d7(Bg/Bgi \u2212 1) / Eo (dimensionless)",
        yaxis_title="F / Eo (STB)",
        height=500,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(f"""
**Gas Cap Drive Interpretation:**
- **N = {n_estimated:,.2f} STB** (Intercept)
- **m = {m_estimated:.4f}** (Slope / Intercept = {slope:,.4f} / {intercept:,.2f})
""")


def _render_water_drive_plot(eo_values, delta_p_values, f_values):
    eo_array = np.array(eo_values)
    dp_array = np.array(delta_p_values)
    f_array = np.array(f_values)
    valid_mask = np.abs(eo_array) > 1e-12
    x_values = np.divide(dp_array[valid_mask], eo_array[valid_mask])
    y_values = np.divide(f_array[valid_mask], eo_array[valid_mask])
    finite_mask = np.isfinite(x_values) & np.isfinite(y_values)
    x_clean = x_values[finite_mask]
    y_clean = y_values[finite_mask]
    if len(x_clean) < 2:
        st.info("Not enough valid data points for F/Eo vs \u0394P/Eo regression.")
        return
    slope, intercept = np.polyfit(x_clean, y_clean, 1)
    n_estimated = intercept
    k_estimated = slope
    y_pred = slope * x_clean + intercept
    ss_res = np.sum((y_clean - y_pred) ** 2)
    ss_tot = np.sum((y_clean - np.mean(y_clean)) ** 2)
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_clean, y=y_clean, mode='markers', name='Data Points',
        marker=dict(color='#1f77b4', size=8),
    ))
    trend_x = np.linspace(x_clean.min(), x_clean.max(), 100)
    trend_y = slope * trend_x + intercept
    fig.add_trace(go.Scatter(
        x=trend_x, y=trend_y, mode='lines',
        name=f'Trendline (R\u00b2 = {r_squared:.4f})',
        line=dict(color='#ff7f0e', width=2, dash='dash'),
    ))
    fig.update_layout(
        title="Havlena-Odeh: F/Eo vs. \u0394P/Eo (Water Drive)",
        xaxis_title="\u0394P / Eo (psi\u00b7STB/bbl)",
        yaxis_title="F / Eo (STB)",
        height=500,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(f"""
**Water Drive Interpretation:**
- **N = {n_estimated:,.2f} STB** (Intercept)
- **K = {k_estimated:,.2f} STB/psi** (Slope = Water Influx Constant)
""")


def _render_volumetric_undersaturated_plot(eo_values, efw_values, f_values):
    eo_array = np.array(eo_values)
    efw_array = np.array(efw_values)
    f_array = np.array(f_values)
    x_array = eo_array + efw_array
    valid_mask = np.abs(x_array) > 1e-12
    x_clean = x_array[valid_mask]
    y_clean = f_array[valid_mask]
    finite_mask = np.isfinite(x_clean) & np.isfinite(y_clean)
    x_clean = x_clean[finite_mask]
    y_clean = y_clean[finite_mask]
    if len(x_clean) < 2:
        st.info("Not enough valid data points for F vs Eo+Efw regression.")
        return
    with st.expander("Advanced Regression Settings", expanded=True):
        force_origin = st.checkbox(
            "Force line through origin (0,0)",
            value=True,
            key="origin_vol_unsat",
        )
        ignore_points = st.slider(
            "Ignore early data points",
            0, len(x_clean) - 2, 0,
            key="ignore_vol_unsat",
        )

        x_fit = x_clean[ignore_points:]
        y_fit = y_clean[ignore_points:]
        if len(x_fit) < 2:
            st.warning("Too few data points remaining after ignoring early points.")
            return

        if force_origin:
            slope = np.sum(x_fit * y_fit) / np.sum(x_fit ** 2)
            intercept = 0.0
        else:
            slope, intercept = np.polyfit(x_fit, y_fit, 1)

        n_estimated = slope
        y_pred = slope * x_clean + intercept
        ss_res = np.sum((y_clean - y_pred) ** 2)
        ss_tot = np.sum((y_clean - np.mean(y_clean)) ** 2)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x_clean, y=y_clean, mode='markers', name='Data Points',
            marker=dict(color='#1f77b4', size=8),
        ))
        trend_x = np.linspace(0, x_clean.max(), 100)
        trend_y = slope * trend_x + intercept
        fig.add_trace(go.Scatter(
            x=trend_x, y=trend_y, mode='lines',
            name=f'Trendline (R\u00b2 = {r_squared:.4f})',
            line=dict(color='#ff7f0e', width=2, dash='dash'),
        ))
        fig.update_layout(
            title="Havlena-Odeh: F vs. Eo + Efw (Volumetric Undersaturated)",
            xaxis_title="Total Expansion, Eo + Efw (bbl/STB)",
            yaxis_title="Total Withdrawal, F (bbl)",
            height=500,
        )
        st.plotly_chart(fig, use_container_width=True)
        intercept_info = f", Intercept = {intercept:,.2f}" if not force_origin else ""
        st.markdown(f"""
**Volumetric Undersaturated Interpretation:**
- **N = {n_estimated:,.2f} STB** (Slope{intercept_info})
""")


def _render_volumetric_saturated_plot(eo_values, f_values):
    eo_array = np.array(eo_values)
    f_array = np.array(f_values)
    valid_mask = np.abs(eo_array) > 1e-12
    x_clean = eo_array[valid_mask]
    y_clean = f_array[valid_mask]
    finite_mask = np.isfinite(x_clean) & np.isfinite(y_clean)
    x_clean = x_clean[finite_mask]
    y_clean = y_clean[finite_mask]
    if len(x_clean) < 2:
        st.info("Not enough valid data points for F vs Eo regression.")
        return
    with st.expander("Advanced Regression Settings", expanded=True):
        force_origin = st.checkbox(
            "Force line through origin (0,0)",
            value=True,
            key="origin_vol_sat",
        )
        ignore_points = st.slider(
            "Ignore early data points",
            0, len(x_clean) - 2, 0,
            key="ignore_vol_sat",
        )

        x_fit = x_clean[ignore_points:]
        y_fit = y_clean[ignore_points:]
        if len(x_fit) < 2:
            st.warning("Too few data points remaining after ignoring early points.")
            return

        if force_origin:
            slope = np.sum(x_fit * y_fit) / np.sum(x_fit ** 2)
            intercept = 0.0
        else:
            slope, intercept = np.polyfit(x_fit, y_fit, 1)

        n_estimated = slope
        y_pred = slope * x_clean + intercept
        ss_res = np.sum((y_clean - y_pred) ** 2)
        ss_tot = np.sum((y_clean - np.mean(y_clean)) ** 2)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x_clean, y=y_clean, mode='markers', name='Data Points',
            marker=dict(color='#1f77b4', size=8),
        ))
        trend_x = np.linspace(0, x_clean.max(), 100)
        trend_y = slope * trend_x + intercept
        fig.add_trace(go.Scatter(
            x=trend_x, y=trend_y, mode='lines',
            name=f'Trendline (R\u00b2 = {r_squared:.4f})',
            line=dict(color='#ff7f0e', width=2, dash='dash'),
        ))
        fig.update_layout(
            title="Havlena-Odeh: F vs. Eo (Volumetric Saturated)",
            xaxis_title="Oil Expansion, Eo (bbl/STB)",
            yaxis_title="Total Withdrawal, F (bbl)",
            height=500,
        )
        st.plotly_chart(fig, use_container_width=True)
        intercept_info = f", Intercept = {intercept:,.2f}" if not force_origin else ""
        st.markdown(f"""
**Volumetric Saturated Interpretation:**
- **N = {n_estimated:,.2f} STB** (Slope{intercept_info})
""")


def render_time_series(df, col_map, forced_zeros=None, fluid_type='oil', is_unsaturated=False, all_vals=None):
    if df is None or len(df) <= 1:
        return

    def get_val(var_name, row_series):
        if var_name in col_map and col_map[var_name] in df.columns:
            val = pd.to_numeric(row_series[col_map[var_name]], errors='coerce')
            if pd.notna(val):
                return float(val)
        return float(all_vals.get(var_name, 0.0) or 0.0)

    st.markdown("---")
    st.header("Time-Series Analysis")

    delta_pressure_column = col_map.get('deltaP')
    cumulative_oil_column = col_map.get('Np')

    if delta_pressure_column is None or cumulative_oil_column is None:
        st.info("Pressure vs. Cumulative Production plot requires 'deltaP' and 'Np' columns.")
    else:
        delta_pressure_series = pd.Series(pd.to_numeric(df[delta_pressure_column], errors='coerce'))
        cumulative_oil_series = pd.Series(pd.to_numeric(df[cumulative_oil_column], errors='coerce'))

        mask = delta_pressure_series.notna() & cumulative_oil_series.notna()
        delta_pressure_values = delta_pressure_series[mask]
        cumulative_oil_values = cumulative_oil_series[mask]

        pressure_chart = go.Figure()
        pressure_chart.add_trace(go.Scatter(
            x=cumulative_oil_values, y=delta_pressure_values,
            mode='lines+markers',
            name='Pressure vs Np',
            line=dict(color='#d62728', width=2)
        ))
        pressure_chart.update_layout(
            title="Pressure Decline vs. Cumulative Oil Production",
            xaxis_title="Cumulative Oil Produced, Np (STB)",
            yaxis_title="Pressure Drop, ΔP (psi)",
            height=450
        )
        st.plotly_chart(pressure_chart, use_container_width=True)

    total_withdrawal_values = []
    total_expansion_values = []
    eo_values = []
    egc_values = []
    efw_values = []
    delta_p_values = []
    for i in range(len(df)):
        row = df.iloc[i]
        row_values = {v: get_val(v, row) for v in ['Np', 'Bo', 'Rp', 'Rsi', 'Rs', 'Bg', 'Wp', 'Bw', 'Boi', 'm', 'Bgi', 'Swi', 'cw', 'cf', 'deltaP']}
        p_col = next((c for c in df.columns if c.lower() in ['pressure', 'p']), None)
        if p_col:
            initial_p = pd.to_numeric(df[p_col].iloc[0], errors='coerce')
            current_p = pd.to_numeric(row[p_col], errors='coerce')
            if pd.notna(initial_p) and pd.notna(current_p):
                row_values['deltaP'] = float(initial_p - current_p)
        terms = compute_mbe_derived_terms(row_values)
        total_withdrawal_values.append(terms['F'])
        total_expansion_values.append(terms['Et'])
        efw_values.append(terms['rock_water_expansion'])
        Bo = get_val('Bo', row)
        Boi = get_val('Boi', row)
        Bg = get_val('Bg', row)
        Bgi = get_val('Bgi', row)
        Rsi = get_val('Rsi', row)
        Rs = get_val('Rs', row)
        Eo = (Bo - Boi) + (Rsi - Rs) * Bg
        Egc = Boi * (Bg / Bgi - 1.0) if Bgi != 0 else 0.0
        eo_values.append(Eo)
        egc_values.append(Egc)
        delta_p_values.append(get_val('deltaP', row))

    havlena_chart = go.Figure()
    havlena_chart.add_trace(go.Scatter(
        x=total_expansion_values, y=total_withdrawal_values,
        mode='markers',
        name='Data Points',
        marker=dict(color='#1f77b4', size=8)
    ))

    valid_points = [
        (et, f_val) for et, f_val in zip(total_expansion_values, total_withdrawal_values)
        if not (np.isnan(et) or np.isnan(f_val) or np.isinf(et) or np.isinf(f_val))
    ]
    if len(valid_points) >= 2:
        et_array = np.array([v[0] for v in valid_points])
        f_array = np.array([v[1] for v in valid_points])
        trend_coefficients = np.polyfit(et_array, f_array, 1)
        slope, intercept = trend_coefficients[0], trend_coefficients[1]
        trend_x = np.linspace(et_array.min(), et_array.max(), 100)
        trend_y = slope * trend_x + intercept
        r_squared = 1 - np.sum((f_array - (slope * et_array + intercept))**2) / np.sum((f_array - f_array.mean())**2)
        havlena_chart.add_trace(go.Scatter(
            x=trend_x, y=trend_y,
            mode='lines',
            name=f'Trendline (slope ≈ {slope:,.2f}, R² = {r_squared:.4f})',
            line=dict(color='#ff7f0e', width=2, dash='dash')
        ))

    havlena_chart.update_layout(
        title="Havlena-Odeh Plot: F vs. Et",
        xaxis_title="Total Expansion, Et (bbl/STB)",
        yaxis_title="Total Withdrawal, F (bbl)",
        height=500
    )
    st.plotly_chart(havlena_chart, use_container_width=True)

    st.markdown("""
**Havlena-Odeh Straight-Line Interpretation**

In the Havlena-Odeh straight-line method, a linear trend in the F vs. Et plot confirms that the
assumed drive mechanisms are consistent with the production history. The slope of the best-fit
line represents the **Initial Oil-in-Place (N)**. Deviations from linearity suggest that additional
or different drive mechanisms may be active.
""")

    if fluid_type == 'oil':
        fz_set = set(forced_zeros or [])
        gas_cap_active = 'm' not in fz_set
        water_drive_active = 'We' not in fz_set

        if is_unsaturated:
            st.markdown("---")
            st.subheader("Volumetric Undersaturated: Havlena-Odeh Plot")
            _render_volumetric_undersaturated_plot(eo_values, efw_values, total_withdrawal_values)
        elif not gas_cap_active and not water_drive_active:
            st.markdown("---")
            st.subheader("Volumetric Saturated: Havlena-Odeh Plot")
            _render_volumetric_saturated_plot(eo_values, total_withdrawal_values)
        else:
            if gas_cap_active:
                st.markdown("---")
                st.subheader("Gas Cap Drive: Parameterized Havlena-Odeh Plot")
                _render_gas_cap_plot(eo_values, egc_values, total_withdrawal_values)

            if water_drive_active:
                st.markdown("---")
                st.subheader("Water Drive: Parameterized Havlena-Odeh Plot")
                _render_water_drive_plot(eo_values, delta_p_values, total_withdrawal_values)
