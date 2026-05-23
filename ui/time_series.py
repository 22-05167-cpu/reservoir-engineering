import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from mbe_solver import compute_mbe_derived_terms
from models.water_influx import compute_water_influx_series
from models.gas_hod import pz_vs_gp, gas_f_vs_eg, detect_water_drive_from_pz
from models.roach import roach_alpha_beta, roach_fit
from models.gas_tight import stabilization_time_radial, stabilization_time_fractured


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
    try:
        slope, intercept = np.polyfit(x_clean, y_clean, 1)
    except (np.linalg.LinAlgError, ValueError):
        st.info("Gas cap drive regression failed.")
        return
    n_estimated = intercept
    m_estimated = slope / intercept if abs(intercept) > 1e-12 else 0.0
    y_pred = slope * x_clean + intercept
    ss_res = np.sum((y_clean - y_pred) ** 2)
    ss_tot = np.sum((y_clean - np.mean(y_clean)) ** 2)
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x_clean,
            y=y_clean,
            mode="markers",
            name="Data Points",
            marker=dict(color="#1f77b4", size=8),
        )
    )
    trend_x = np.linspace(x_clean.min(), x_clean.max(), 100)
    trend_y = slope * trend_x + intercept
    fig.add_trace(
        go.Scatter(
            x=trend_x,
            y=trend_y,
            mode="lines",
            name=f"Trendline (R\u00b2 = {r_squared:.4f})",
            line=dict(color="#ff7f0e", width=2, dash="dash"),
        )
    )
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
    try:
        slope, intercept = np.polyfit(x_clean, y_clean, 1)
    except (np.linalg.LinAlgError, ValueError):
        st.info("Water drive regression failed — data may be degenerate.")
        return
    n_estimated = intercept
    k_estimated = slope
    y_pred = slope * x_clean + intercept
    ss_res = np.sum((y_clean - y_pred) ** 2)
    ss_tot = np.sum((y_clean - np.mean(y_clean)) ** 2)
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x_clean,
            y=y_clean,
            mode="markers",
            name="Data Points",
            marker=dict(color="#1f77b4", size=8),
        )
    )
    trend_x = np.linspace(x_clean.min(), x_clean.max(), 100)
    trend_y = slope * trend_x + intercept
    fig.add_trace(
        go.Scatter(
            x=trend_x,
            y=trend_y,
            mode="lines",
            name=f"Trendline (R\u00b2 = {r_squared:.4f})",
            line=dict(color="#ff7f0e", width=2, dash="dash"),
        )
    )
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


def _render_water_drive_model_plot(eo_values, we_values, f_values):
    """Havlena-Odeh diagnostic: F/Eo vs We/Eo.

    A 45-degree straight line confirms the water influx model is correct.
    """
    eo_array = np.array(eo_values)
    we_array = np.array(we_values)
    f_array = np.array(f_values)
    valid_mask = np.abs(eo_array) > 1e-12
    x_values = np.divide(we_array[valid_mask], eo_array[valid_mask])
    y_values = np.divide(f_array[valid_mask], eo_array[valid_mask])
    finite_mask = np.isfinite(x_values) & np.isfinite(y_values)
    x_clean = x_values[finite_mask]
    y_clean = y_values[finite_mask]
    if len(x_clean) < 2:
        st.info("Not enough valid data points for F/Eo vs We/Eo regression.")
        return
    try:
        slope, intercept = np.polyfit(x_clean, y_clean, 1)
    except (np.linalg.LinAlgError, ValueError):
        st.info("Water influx diagnostic regression failed — data may be degenerate.")
        return

    n_estimated = intercept
    y_pred = slope * x_clean + intercept
    ss_res = np.sum((y_clean - y_pred) ** 2)
    ss_tot = np.sum((y_clean - np.mean(y_clean)) ** 2)
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    dev_45 = abs(slope - 1.0)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x_clean,
            y=y_clean,
            mode="markers",
            name="Data Points",
            marker=dict(color="#1f77b4", size=8),
        )
    )
    trend_x = np.linspace(x_clean.min(), x_clean.max(), 100)
    trend_y = slope * trend_x + intercept
    fig.add_trace(
        go.Scatter(
            x=trend_x,
            y=trend_y,
            mode="lines",
            name=f"Best fit (slope={slope:.3f})",
            line=dict(color="#ff7f0e", width=2, dash="dash"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=trend_x,
            y=trend_x + intercept,
            mode="lines",
            name="45° ideal",
            line=dict(color="#2ca02c", width=1, dash="dot"),
        )
    )
    fig.update_layout(
        title=f"Water Influx Diagnostic: F/Eo vs We/Eo (R²={r_squared:.4f})",
        xaxis_title="We / Eo (STB)",
        yaxis_title="F / Eo (STB)",
        height=500,
    )
    st.plotly_chart(fig, use_container_width=True)

    if dev_45 < 0.1:
        diag_msg = f"Model fits well. Slope= {slope:.3f} (close to 1.0)"
    elif slope > 1.1:
        diag_msg = f"Model underestimates (slope={slope:.3f} > 1). Try larger aquifer (increase ra)."
    elif slope < 0.9:
        diag_msg = f"Model overestimates (slope={slope:.3f} < 1). Try smaller aquifer (decrease ra)."
    else:
        diag_msg = f"Slope= {slope:.3f} (moderate deviation from 1.0)."

    st.markdown(f"""
**Water Influx Diagnostic:**
- **N = {n_estimated:,.2f} STB** (Intercept)
- **Slope = {slope:.4f}** (ideal = 1.0)
- **Diagnosis:** {diag_msg}
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
    col_a, col_b = st.columns([1, 1])
    with col_a:
        force_origin = st.checkbox(
            "Force line through origin (0,0)",
            value=True,
            key="origin_vol_unsat",
        )
    with col_b:
        ignore_points = st.slider(
            "Ignore early data points",
            0,
            len(x_clean) - 2,
            0,
            key="ignore_vol_unsat",
        )

        x_fit = x_clean[ignore_points:]
        y_fit = y_clean[ignore_points:]
        if len(x_fit) < 2:
            st.warning("Too few data points remaining after ignoring early points.")
            return

        if force_origin:
            slope = np.sum(x_fit * y_fit) / np.sum(x_fit**2)
            intercept = 0.0
        else:
            try:
                slope, intercept = np.polyfit(x_fit, y_fit, 1)
            except (np.linalg.LinAlgError, ValueError):
                st.info("Undersaturated regression failed — data may be degenerate.")
                return

        n_estimated = slope
        y_pred = slope * x_clean + intercept
        ss_res = np.sum((y_clean - y_pred) ** 2)
        ss_tot = np.sum((y_clean - np.mean(y_clean)) ** 2)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=x_clean,
                y=y_clean,
                mode="markers",
                name="Data Points",
                marker=dict(color="#1f77b4", size=8),
            )
        )
        trend_x = np.linspace(0, x_clean.max(), 100)
        trend_y = slope * trend_x + intercept
        fig.add_trace(
            go.Scatter(
                x=trend_x,
                y=trend_y,
                mode="lines",
                name=f"Trendline (R\u00b2 = {r_squared:.4f})",
                line=dict(color="#ff7f0e", width=2, dash="dash"),
            )
        )
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
    col_a, col_b = st.columns([1, 1])
    with col_a:
        force_origin = st.checkbox(
            "Force line through origin (0,0)",
            value=True,
            key="origin_vol_sat",
        )
    with col_b:
        ignore_points = st.slider(
            "Ignore early data points",
            0,
            len(x_clean) - 2,
            0,
            key="ignore_vol_sat",
        )

        x_fit = x_clean[ignore_points:]
        y_fit = y_clean[ignore_points:]
        if len(x_fit) < 2:
            st.warning("Too few data points remaining after ignoring early points.")
            return

        if force_origin:
            slope = np.sum(x_fit * y_fit) / np.sum(x_fit**2)
            intercept = 0.0
        else:
            try:
                slope, intercept = np.polyfit(x_fit, y_fit, 1)
            except (np.linalg.LinAlgError, ValueError):
                st.info("Saturated regression failed — data may be degenerate.")
                return

        n_estimated = slope
        y_pred = slope * x_clean + intercept
        ss_res = np.sum((y_clean - y_pred) ** 2)
        ss_tot = np.sum((y_clean - np.mean(y_clean)) ** 2)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=x_clean,
                y=y_clean,
                mode="markers",
                name="Data Points",
                marker=dict(color="#1f77b4", size=8),
            )
        )
        trend_x = np.linspace(0, x_clean.max(), 100)
        trend_y = slope * trend_x + intercept
        fig.add_trace(
            go.Scatter(
                x=trend_x,
                y=trend_y,
                mode="lines",
                name=f"Trendline (R\u00b2 = {r_squared:.4f})",
                line=dict(color="#ff7f0e", width=2, dash="dash"),
            )
        )
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


def render_time_series(
    df,
    col_map,
    forced_zeros=None,
    fluid_type="oil",
    is_unsaturated=False,
    all_vals=None,
    water_influx_model="none",
    water_influx_params=None,
):
    if df is None or len(df) <= 1:
        return

    st.markdown("---")
    with st.expander("📈  Time-Series Analysis", expanded=False):
        st.markdown("""
        **What these plots mean:**
        - **F vs Et** — straight line through origin means your m and We assumptions are correct
        - **F curves upward** → missing energy source (larger m or We needed)
        - **F curves downward** → overestimating the energy
        - **F/Eo vs We/Eo** — 45° line means the water influx model fits
        """)
        st.markdown("---")
        _render_ts_content(
            df,
            col_map,
            forced_zeros,
            fluid_type,
            is_unsaturated,
            all_vals,
            water_influx_model,
            water_influx_params,
        )


def _render_ts_content(
    df,
    col_map,
    forced_zeros,
    fluid_type,
    is_unsaturated,
    all_vals,
    water_influx_model="none",
    water_influx_params=None,
):

    if fluid_type == "gas":
        _render_gas_ts_content(
            df, col_map, all_vals, water_influx_model, water_influx_params
        )
        return

    def get_val(var_name, row_series):
        if var_name in col_map and col_map[var_name] in df.columns:
            val = pd.to_numeric(row_series[col_map[var_name]], errors="coerce")
            if pd.notna(val):
                return float(val)
        return float(all_vals.get(var_name, 0.0) or 0.0)

    delta_pressure_column = col_map.get("deltaP")
    cumulative_oil_column = col_map.get("Np")

    if delta_pressure_column is None or cumulative_oil_column is None:
        st.info(
            "Pressure vs. Cumulative Production plot requires 'deltaP' and 'Np' columns."
        )
    else:
        delta_pressure_series = pd.Series(
            pd.to_numeric(df[delta_pressure_column], errors="coerce")
        )
        cumulative_oil_series = pd.Series(
            pd.to_numeric(df[cumulative_oil_column], errors="coerce")
        )

        mask = delta_pressure_series.notna() & cumulative_oil_series.notna()
        delta_pressure_values = delta_pressure_series[mask]
        cumulative_oil_values = cumulative_oil_series[mask]

        pressure_chart = go.Figure()
        pressure_chart.add_trace(
            go.Scatter(
                x=cumulative_oil_values,
                y=delta_pressure_values,
                mode="lines+markers",
                name="Pressure vs Np",
                line=dict(color="#d62728", width=2),
            )
        )
        pressure_chart.update_layout(
            title="Pressure Decline vs. Cumulative Oil Production",
            xaxis_title="Cumulative Oil Produced, Np (STB)",
            yaxis_title="Pressure Drop, ΔP (psi)",
            height=450,
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
        row_values = {
            v: get_val(v, row)
            for v in [
                "Np",
                "Bo",
                "Rp",
                "Rsi",
                "Rs",
                "Bg",
                "Wp",
                "Bw",
                "Boi",
                "m",
                "Bgi",
                "Swi",
                "cw",
                "cf",
                "deltaP",
            ]
        }
        p_col = next((c for c in df.columns if c.lower() in ["pressure", "p"]), None)
        if p_col:
            initial_p = pd.to_numeric(df[p_col].iloc[0], errors="coerce")
            current_p = pd.to_numeric(row[p_col], errors="coerce")
            if pd.notna(initial_p) and pd.notna(current_p):
                row_values["deltaP"] = float(initial_p - current_p)
        terms = compute_mbe_derived_terms(row_values)
        total_withdrawal_values.append(terms["F"])
        total_expansion_values.append(terms["Et"])
        efw_values.append(terms["rock_water_expansion"])
        Bo = get_val("Bo", row)
        Boi = get_val("Boi", row)
        Bg = get_val("Bg", row)
        Bgi = get_val("Bgi", row)
        Rsi = get_val("Rsi", row)
        Rs = get_val("Rs", row)
        Eo = (Bo - Boi) + (Rsi - Rs) * Bg
        Egc = Boi * (Bg / Bgi - 1.0) if Bgi != 0 else 0.0
        eo_values.append(Eo)
        egc_values.append(Egc)
        delta_p_values.append(row_values["deltaP"])

    # ── Water influx model We computation ──────────────────────────────
    we_values = None
    if water_influx_model not in (None, "none") and water_influx_params:
        p_col = None
        for c in df.columns:
            if c.lower() in ["pressure", "p"]:
                p_col = c
                break
        if p_col is not None:
            p_hist_vals = pd.to_numeric(df[p_col], errors="coerce").dropna().tolist()
            if len(p_hist_vals) >= 2:
                pi_hist = p_hist_vals[0]
                wf_params = dict(water_influx_params)
                wf_params["pi"] = pi_hist

                time_col = None
                for c in df.columns:
                    if c.lower() in ["time", "t", "days", "date"]:
                        time_col = c
                        break
                if time_col is not None:
                    t_hist = (
                        pd.to_numeric(df[time_col], errors="coerce").dropna().tolist()
                    )
                else:
                    t_hist = list(range(len(p_hist_vals)))

                we_series = compute_water_influx_series(
                    water_influx_model, wf_params, p_hist_vals, t_history=t_hist
                )
                if len(we_series) < len(df):
                    we_series = we_series + [0.0] * (len(df) - len(we_series))
                we_values = we_series

    havlena_chart = go.Figure()
    havlena_chart.add_trace(
        go.Scatter(
            x=total_expansion_values,
            y=total_withdrawal_values,
            mode="markers",
            name="Data Points",
            marker=dict(color="#1f77b4", size=8),
        )
    )

    valid_points = [
        (et, f_val)
        for et, f_val in zip(total_expansion_values, total_withdrawal_values)
        if not (np.isnan(et) or np.isnan(f_val) or np.isinf(et) or np.isinf(f_val))
    ]
    if len(valid_points) >= 2:
        et_array = np.array([v[0] for v in valid_points])
        f_array = np.array([v[1] for v in valid_points])
        try:
            trend_coefficients = np.polyfit(et_array, f_array, 1)
            slope, intercept = trend_coefficients[0], trend_coefficients[1]
            trend_x = np.linspace(et_array.min(), et_array.max(), 100)
            trend_y = slope * trend_x + intercept
            r_squared = 1 - np.sum(
                (f_array - (slope * et_array + intercept)) ** 2
            ) / np.sum((f_array - f_array.mean()) ** 2)
            havlena_chart.add_trace(
                go.Scatter(
                    x=trend_x,
                    y=trend_y,
                    mode="lines",
                    name=f"Trendline (slope ≈ {slope:,.2f}, R² = {r_squared:.4f})",
                    line=dict(color="#ff7f0e", width=2, dash="dash"),
                )
            )
        except (np.linalg.LinAlgError, ValueError):
            st.info(
                "Trendline could not be computed — data may be degenerate "
                "(e.g., all values identical). Add more varied rows."
            )

    havlena_chart.update_layout(
        title="Havlena-Odeh Plot: F vs. Et",
        xaxis_title="Total Expansion, Et (bbl/STB)",
        yaxis_title="Total Withdrawal, F (bbl)",
        height=500,
    )
    st.plotly_chart(havlena_chart, use_container_width=True)

    st.markdown("""
**Havlena-Odeh Straight-Line Interpretation**

In the Havlena-Odeh straight-line method, a linear trend in the F vs. Et plot confirms that the
assumed drive mechanisms are consistent with the production history. The slope of the best-fit
line represents the **Initial Oil-in-Place (N)**. Deviations from linearity suggest that additional
or different drive mechanisms may be active.
""")

    if fluid_type == "oil":
        fz_set = set(forced_zeros or [])
        gas_cap_active = "m" not in fz_set
        water_drive_active = "We" not in fz_set

        if is_unsaturated:
            st.markdown("---")
            st.subheader("Volumetric Undersaturated: Havlena-Odeh Plot")
            _render_volumetric_undersaturated_plot(
                eo_values, efw_values, total_withdrawal_values
            )
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
                if we_values is not None and any(w != 0 for w in we_values):
                    _render_water_drive_model_plot(
                        eo_values, we_values, total_withdrawal_values
                    )
                else:
                    _render_water_drive_plot(
                        eo_values, delta_p_values, total_withdrawal_values
                    )


def _render_gas_ts_content(
    df, col_map, all_vals, water_influx_model="none", water_influx_params=None
):
    """Gas-specific time-series analysis: p/Z vs Gp, F vs Eg, linear aquifer, Roach."""

    def get_val(var_name, row_series):
        if var_name in col_map and col_map[var_name] in df.columns:
            val = pd.to_numeric(row_series[col_map[var_name]], errors="coerce")
            if pd.notna(val):
                return float(val)
        return float(all_vals.get(var_name, 0.0) or 0.0)

    p_vals, z_vals, gp_vals, bg_vals, wp_vals = [], [], [], [], []
    z_key = None
    for c in df.columns:
        if c.lower() in ["z", "z_factor", "gas_deviation"]:
            z_key = c
            break

    for i in range(len(df)):
        row = df.iloc[i]
        p_vals.append(get_val("p", row))
        gp_vals.append(get_val("Gp", row))
        bg_vals.append(get_val("Bg", row))
        wp_vals.append(get_val("Wp", row))
        z_val = pd.to_numeric(row[z_key], errors="coerce") if z_key else None
        z_vals.append(
            float(z_val)
            if z_val is not None and pd.notna(z_val)
            else all_vals.get("Z", 0.8)
        )

    p_arr = np.array(p_vals)
    gp_arr = np.array(gp_vals)
    bg_arr = np.array(bg_vals)
    z_arr = np.array(z_vals)

    st.markdown("---")
    st.subheader("Gas Reservoir Time-Series Analysis")

    # ── 1. p/Z vs Gp plot ────────────────────────────────────────────
    pz_data = pz_vs_gp(p_arr, z_arr, gp_arr)
    fig_pz = go.Figure()
    fig_pz.add_trace(
        go.Scatter(
            x=pz_data["gp"],
            y=pz_data["pz"],
            mode="lines+markers",
            name="p/Z",
            line=dict(color="#1f77b4"),
        )
    )
    if len(p_arr) >= 2:
        try:
            coeffs = np.polyfit(pz_data["gp"], pz_data["pz"], 1)
            trend = np.polyval(coeffs, pz_data["gp"])
            fig_pz.add_trace(
                go.Scatter(
                    x=pz_data["gp"],
                    y=trend,
                    mode="lines",
                    name="Trend",
                    line=dict(color="#ff7f0e", dash="dash"),
                )
            )
            g_estimate = -pz_data["pi_zi"] / coeffs[0] if coeffs[0] != 0 else 0
        except (np.linalg.LinAlgError, ValueError):
            g_estimate = None
    fig_pz.update_layout(
        title="p/Z vs Cumulative Gas Production",
        xaxis_title="Gp (scf)",
        yaxis_title="p/Z (psi)",
        height=400,
    )
    st.plotly_chart(fig_pz, use_container_width=True)
    if g_estimate and g_estimate > 0:
        wd = detect_water_drive_from_pz(pz_data["pz"], pz_data["gp"])
        st.markdown(
            f"**G estimate:** {g_estimate:,.0f} scf | "
            f"Curvature={wd['curvature']:.4f} | "
            f"{'Water drive suspected' if wd['is_water_drive'] else 'Volumetric'}"
        )
    st.markdown("---")

    # ── 2. F vs Eg Havlena-Odeh plot ─────────────────────────────────
    Bgi = float(bg_arr[0]) if len(bg_arr) > 0 else 0
    hod = gas_f_vs_eg(None, bg_arr, Bgi, gp_arr, np.array(wp_vals), 1.0)
    fig_feg = go.Figure()
    valid_eg = np.abs(hod["Eg"]) > 1e-15
    fig_feg.add_trace(
        go.Scatter(
            x=hod["Eg"][valid_eg],
            y=hod["F"][valid_eg],
            mode="lines+markers",
            name="F vs Eg",
            line=dict(color="#2ca02c"),
        )
    )
    if np.sum(valid_eg) >= 2:
        try:
            slope = np.sum(hod["F"][valid_eg] * hod["Eg"][valid_eg]) / np.sum(
                hod["Eg"][valid_eg] ** 2
            )
            trend_line = slope * hod["Eg"][valid_eg]
            fig_feg.add_trace(
                go.Scatter(
                    x=hod["Eg"][valid_eg],
                    y=trend_line,
                    mode="lines",
                    name=f"G ≈ {slope:,.0f}",
                    line=dict(color="#d62728", dash="dash"),
                )
            )
        except Exception:
            pass
    fig_feg.update_layout(
        title="F vs Eg (Gas Havlena-Odeh)",
        xaxis_title="Eg = Bg - Bgi (bbl/scf)",
        yaxis_title="F = Gp*Bg + Wp*Bw (bbl)",
        height=400,
    )
    st.plotly_chart(fig_feg, use_container_width=True)

    # ── 3. Water influx diagnostic for gas ────────────────────────────
    if water_influx_model not in (None, "none") and water_influx_params:
        we_values = _compute_gas_we_series(
            water_influx_model, water_influx_params, p_vals
        )
        if we_values is not None and any(w != 0 for w in we_values):
            st.markdown("---")
            st.subheader("Gas Water Influx Diagnostic")
            _render_gas_we_diagnostic(hod["F"], hod["Eg"], we_values)

    # ── 4. Roach's alpha/beta plot ────────────────────────────────────
    if len(z_vals) >= 3 and np.std(z_arr) > 0.01:
        st.markdown("---")
        st.subheader("Roach α/β Plot (Abnormally Pressured Gas)")
        pi = p_vals[0]
        zi = z_vals[0]
        rb = roach_alpha_beta(p_vals, z_vals, pi, zi)
        valid_r = (
            np.isfinite(rb["alpha"])
            & np.isfinite(rb["beta"])
            & (np.abs(rb["alpha"]) > 1e-15)
            & (np.abs(rb["beta"]) > 1e-15)
        )
        fig_r = go.Figure()
        fig_r.add_trace(
            go.Scatter(
                x=rb["alpha"][valid_r],
                y=rb["beta"][valid_r],
                mode="markers",
                marker=dict(color="#9467bd", size=8),
                name="α vs β",
            )
        )
        if np.sum(valid_r) >= 2:
            try:
                coeffs_r = np.polyfit(rb["alpha"][valid_r], rb["beta"][valid_r], 1)
                trend_r = np.polyval(coeffs_r, rb["alpha"][valid_r])
                fig_r.add_trace(
                    go.Scatter(
                        x=rb["alpha"][valid_r],
                        y=trend_r,
                        mode="lines",
                        name="Fit",
                        line=dict(color="#8c564b", dash="dash"),
                    )
                )
                G_roach = 1.0 / coeffs_r[0] if coeffs_r[0] != 0 else 0
                ER_roach = -coeffs_r[1]
                st.markdown(
                    f"**Roach estimate:** G = {G_roach:,.0f} scf, "
                    f"ER = {ER_roach:.4e} psi⁻¹"
                )
            except Exception:
                pass
        fig_r.update_layout(
            title="Roach Method: α vs β",
            xaxis_title="α (psi⁻¹)",
            yaxis_title="β (psi⁻¹)",
            height=400,
        )
        st.plotly_chart(fig_r, use_container_width=True)

    # ── 5. tpss calculator ────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Gas Stabilization Time (tpss)")
    col_a, col_b = st.columns(2)
    with col_a:
        phi_in = st.number_input(
            "Porosity φ", min_value=0.0, value=0.14, step=0.01, key="tpss_phi"
        )
        mu_in = st.number_input(
            "Gas viscosity μg (cp)",
            min_value=0.0,
            value=0.016,
            step=0.001,
            key="tpss_mu",
        )
        ct_in = st.number_input(
            "Total compressibility ct (psi⁻¹)",
            min_value=0.0,
            value=8e-4,
            step=1e-4,
            format="%.2e",
            key="tpss_ct",
        )
    with col_b:
        k_in = st.number_input(
            "Permeability k (md)", min_value=0.0, value=0.1, step=0.1, key="tpss_k"
        )
        acres_in = st.number_input(
            "Drainage area (acres)",
            min_value=0.0,
            value=40.0,
            step=10.0,
            key="tpss_acres",
        )
        xf_in = st.number_input(
            "Fracture half-length xf (ft, 0=unfractured)",
            min_value=0,
            value=0,
            step=50,
            key="tpss_xf",
        )

    if st.button("Calculate tpss", key="tpss_btn"):
        t_rad = stabilization_time_radial(
            phi_in, mu_in, ct_in, A_acres=acres_in, k=k_in
        )
        st.metric(
            "Radial tpss",
            f"{t_rad:.0f} days ({t_rad / 30.44:.1f} months)" if t_rad > 0 else "N/A",
        )
        if xf_in > 0:
            t_frac = stabilization_time_fractured(phi_in, mu_in, ct_in, xf_in, k_in)
            st.metric(
                "Fractured tpss",
                f"{t_frac:.0f} days ({t_frac / 30.44:.1f} months)"
                if t_frac > 0
                else "N/A",
            )
            mu_in = st.number_input(
                "Gas viscosity μg (cp)",
                min_value=0.0,
                value=0.016,
                step=0.001,
                key="tpss_mu",
            )
            ct_in = st.number_input(
                "Total compressibility ct (psi⁻¹)",
                min_value=0.0,
                value=8e-4,
                step=1e-4,
                format="%.2e",
                key="tpss_ct",
            )
        with col_b:
            k_in = st.number_input(
                "Permeability k (md)", min_value=0.0, value=0.1, step=0.1, key="tpss_k"
            )
            acres_in = st.number_input(
                "Drainage area (acres)",
                min_value=0.0,
                value=40.0,
                step=10.0,
                key="tpss_acres",
            )
            xf_in = st.number_input(
                "Fracture half-length xf (ft, 0=unfractured)",
                min_value=0,
                value=0,
                step=50,
                key="tpss_xf",
            )

        if st.button("Calculate tpss", key="tpss_btn"):
            t_rad = stabilization_time_radial(
                phi_in, mu_in, ct_in, A_acres=acres_in, k=k_in
            )
            st.metric(
                "Radial tpss",
                f"{t_rad:.0f} days ({t_rad / 30.44:.1f} months)"
                if t_rad > 0
                else "N/A",
            )
            if xf_in > 0:
                t_frac = stabilization_time_fractured(phi_in, mu_in, ct_in, xf_in, k_in)
                st.metric(
                    "Fractured tpss",
                    f"{t_frac:.0f} days ({t_frac / 30.44:.1f} months)"
                    if t_frac > 0
                    else "N/A",
                )


def _compute_gas_we_series(model_type, params, p_vals):
    """Compute We series for gas using selected water influx model."""
    from models.water_influx import compute_water_influx_series

    try:
        wf_params = dict(params)
        wf_params["pi"] = p_vals[0] if len(p_vals) > 0 else 0
        return compute_water_influx_series(
            model_type, wf_params, p_vals, t_history=list(range(len(p_vals)))
        )
    except Exception:
        return None


def _render_gas_we_diagnostic(F, Eg, we_values):
    """F/Eg vs We/Eg plot for gas water influx diagnostic."""
    F_arr = np.array(F)
    Eg_arr = np.array(Eg)
    We_arr = np.array(we_values)
    valid = np.abs(Eg_arr) > 1e-15
    x = np.divide(We_arr[valid], Eg_arr[valid])
    y = np.divide(F_arr[valid], Eg_arr[valid])
    if len(x) < 2:
        st.info("Not enough data for water influx diagnostic.")
        return
    try:
        slope, intercept = np.polyfit(x, y, 1)
    except (np.linalg.LinAlgError, ValueError):
        st.info("Water influx diagnostic failed.")
        return
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x, y=y, mode="markers", name="Data", marker=dict(color="#1f77b4", size=8)
        )
    )
    trend_x = np.linspace(x.min(), x.max(), 100)
    trend_y = slope * trend_x + intercept
    fig.add_trace(
        go.Scatter(
            x=trend_x,
            y=trend_y,
            mode="lines",
            name=f"Slope={slope:.3f}",
            line=dict(color="#ff7f0e", dash="dash"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=trend_x,
            y=trend_x + intercept,
            mode="lines",
            name="45° ideal",
            line=dict(color="#2ca02c", dash="dot"),
        )
    )
    fig.update_layout(
        title="Gas Water Influx Diagnostic: F/Eg vs We/Eg",
        xaxis_title="We / Eg",
        yaxis_title="F / Eg",
        height=400,
    )
    st.plotly_chart(fig, use_container_width=True)
    dev = abs(slope - 1.0)
    if dev < 0.1:
        st.markdown("Model fits well (slope close to 1.0)")
    elif slope > 1.1:
        st.markdown("Model underestimates — try larger aquifer")
    elif slope < 0.9:
        st.markdown("Model overestimates — try smaller aquifer")
