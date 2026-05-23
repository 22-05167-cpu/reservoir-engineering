"""Prediction UI — Streamlit page for Tracy's reservoir performance prediction.

Provides input for PVT data, relperm data, and parameters,
then runs prediction and displays results (tables, plots).
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from models.tracy import tracy_predict
from models.undersaturated import (
    effective_compressibility,
    undersaturated_cumulative_production,
)
from models.saturation import compute_oil_saturation, compute_gas_saturation
from models.relative_permeability import RelpermInterpolator


def render_prediction_page():
    st.title("Reservoir Performance Prediction")
    st.markdown(
        "Tracy's method — predicts Np, Gp, GOR, So, Sg vs pressure for solution-gas-drive reservoirs."
    )
    st.markdown("---")

    col1, col2 = st.columns([1, 1])

    with col1:
        N = st.number_input(
            "Initial Oil-In-Place N (STB)",
            min_value=0.0,
            value=15e6,
            step=1e6,
            format="%.0f",
        )
        Swi = st.number_input(
            "Initial Water Saturation Swi",
            min_value=0.0,
            max_value=1.0,
            value=0.30,
            step=0.01,
        )
        pi = st.number_input(
            "Initial Pressure pi (psi)", min_value=0.0, value=4350.0, step=100.0
        )
        pb = st.number_input(
            "Bubble-Point Pressure pb (psi)", min_value=0.0, value=4350.0, step=100.0
        )
        p_abandon = st.number_input(
            "Abandonment Pressure (psi)", min_value=0.0, value=500.0, step=100.0
        )

    with col2:
        mu_o_const = st.number_input(
            "Oil Viscosity μo (cp)", min_value=0.0, value=1.7, step=0.1
        )
        mu_g_const = st.number_input(
            "Gas Viscosity μg (cp)", min_value=0.0, value=0.023, step=0.001
        )
        So_init = st.number_input(
            "Initial Oil Saturation Soi",
            min_value=0.0,
            max_value=1.0,
            value=0.70,
            step=0.01,
        )
        if pi > pb:
            co = st.number_input(
                "Oil Compressibility co (1/psi)",
                min_value=0.0,
                value=15e-6,
                step=1e-6,
                format="%.2e",
            )
            cw = st.number_input(
                "Water Compressibility cw (1/psi)",
                min_value=0.0,
                value=3e-6,
                step=1e-6,
                format="%.2e",
            )
            cf_input = st.number_input(
                "Formation Compressibility cf (1/psi)",
                min_value=0.0,
                value=5e-6,
                step=1e-6,
                format="%.2e",
            )
        else:
            co = cw = cf_input = 0.0

    st.markdown("---")

    pvt_tab, relperm_tab = st.tabs(["PVT Data", "Relative Permeability"])

    with pvt_tab:
        st.markdown("**PVT Table** (pressure, Bo, Bg, Rs)")
        default_pvt = pd.DataFrame(
            {
                "p": [4350, 4150, 3950, 3750, 3550, 3350],
                "Bo": [1.43, 1.420, 1.395, 1.380, 1.360, 1.345],
                "Bg": [0.00069, 0.00071, 0.00074, 0.00078, 0.00081, 0.00085],
                "Rs": [840, 820, 770, 730, 680, 640],
            }
        )
        pvt_df = default_pvt.copy()

        pvt_df = st.data_editor(
            pvt_df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "p": st.column_config.NumberColumn(
                    "p (psi)", min_value=0, format="%.0f"
                ),
                "Bo": st.column_config.NumberColumn("Bo (bbl/STB)", format="%.4f"),
                "Bg": st.column_config.NumberColumn("Bg (bbl/scf)", format="%.6f"),
                "Rs": st.column_config.NumberColumn("Rs (scf/STB)", format="%.0f"),
            },
        )

    with relperm_tab:
        st.markdown(
            "**Relative Permeability Table** (Sg, krg/kro) or use exponential correlation"
        )
        relperm_mode = st.radio(
            "Relperm source", ["Table", "Exponential correlation"], horizontal=True
        )

        if relperm_mode == "Table":
            default_relperm = pd.DataFrame(
                {
                    "Sg": [0.0, 0.01, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.15],
                    "krg_kro": [
                        0.0,
                        0.0002,
                        0.001,
                        0.004,
                        0.01,
                        0.03,
                        0.08,
                        0.15,
                        0.35,
                    ],
                }
            )
            relperm_input_df = default_relperm.copy()
            relperm_df = st.data_editor(
                relperm_input_df,
                num_rows="dynamic",
                use_container_width=True,
            )
            Sg_table = relperm_df["Sg"].tolist()
            krg_table = relperm_df["krg_kro"].tolist()
        else:
            col_a, col_b = st.columns(2)
            with col_a:
                exp_a = st.number_input(
                    "Coefficient a", min_value=0.0, value=0.007, format="%.6f"
                )
            with col_b:
                exp_b = st.number_input(
                    "Exponent b", min_value=0.0, value=11.513, format="%.3f"
                )
            Sg_demo = np.linspace(0, 0.15, 8)
            krg_demo = [exp_a * np.exp(exp_b * sg) for sg in Sg_demo]
            relperm_df = pd.DataFrame({"Sg": Sg_demo, "krg_kro": krg_demo})
            st.dataframe(relperm_df, use_container_width=True)
            Sg_table = None
            krg_table = None
            exp_params = (exp_a, exp_b)

    st.markdown("---")

    run_btn = st.button("Run Prediction", type="primary")

    if run_btn:
        pvt = {
            "p": np.array(pvt_df["p"].values, dtype=float),
            "Bo": np.array(pvt_df["Bo"].values, dtype=float),
            "Bg": np.array(pvt_df["Bg"].values, dtype=float),
            "Rs": np.array(pvt_df["Rs"].values, dtype=float),
        }
        sort_idx = np.argsort(pvt["p"])
        for k in pvt:
            pvt[k] = pvt[k][sort_idx]

        if relperm_mode == "Table":
            relperm_data = list(
                zip(
                    [float(x) for x in Sg_table],
                    [float(x) for x in krg_table],
                )
            )
        else:
            relperm_data = []

        Np_sat_start = 0.0
        Gp_sat_start = 0.0

        if pi > pb:
            from models.saturation import bubble_point_transition

            Rsi = float(pvt["Rs"][np.argmax(pvt["p"])])
            Boi = float(pvt["Bo"][np.argmax(pvt["p"])])
            Bo_at_pb = float(np.interp(pb, pvt["p"], pvt["Bo"]))

            ce = effective_compressibility(So_init, Swi, co, cw, cf_input)
            Np_at_pb = undersaturated_cumulative_production(
                N, Boi, Bo_at_pb, ce, pi, pb
            )

            if Np_at_pb > N:
                Np_at_pb = N

            Np_sat_start = Np_at_pb
            Gp_sat_start = Np_at_pb * Rsi
            st.info(
                f"Undersaturated phase: Np at pb = {Np_at_pb:,.0f} STB ({Np_at_pb / N * 100:.2f}%)"
            )

        with st.spinner("Running Tracy prediction..."):
            mu_table = {
                "p": pvt["p"].copy(),
                "mu_o": np.full_like(pvt["p"], mu_o_const),
                "mu_g": np.full_like(pvt["p"], mu_g_const),
            }

            if relperm_mode == "Exponential":
                relperm_interp = RelpermInterpolator()
                a_val, b_val = exp_params
                relperm_interp.set_exponential(a_val, b_val)
            else:
                relperm_interp = None

            df_result = tracy_predict(
                N=N,
                Swi=Swi,
                pvt_table=pvt,
                Sg_krgkro_table=relperm_data,
                pi=pi,
                pb=pb,
                psi_abandonment=p_abandon,
                mu_table=mu_table,
                Np_sat_start=Np_sat_start,
                Gp_sat_start=Gp_sat_start,
                relperm_interpolator=relperm_interp,
            )

        if df_result is None or len(df_result) == 0:
            st.error("Prediction returned no data. Check PVT table and pressure range.")
            return

        st.success("Prediction complete!")

        recovery = df_result["Np"].max() / N * 100
        max_gp = df_result["Gp"].max()

        col_r1, col_r2, col_r3, col_r4 = st.columns(4)
        col_r1.metric("Ultimate Recovery", f"{df_result['Np'].max():,.0f} STB")
        col_r2.metric("Recovery Factor", f"{recovery:.2f}%")
        col_r3.metric("Total Gas Produced", f"{max_gp:,.0f} scf")
        col_r4.metric(
            "Pressure Range",
            f"{df_result['p'].max():.0f} → {df_result['p'].min():.0f} psi",
        )

        st.markdown("### Prediction Results Table")
        display_cols = ["p", "Np", "Gp", "GOR", "Rp", "So", "Sg", "krg_kro"]
        display_df = df_result[display_cols].copy()
        display_df["Np"] = display_df["Np"].apply(lambda x: f"{x:,.0f}")
        display_df["Gp"] = display_df["Gp"].apply(lambda x: f"{x:,.0f}")
        display_df["GOR"] = display_df["GOR"].apply(lambda x: f"{x:,.1f}")
        display_df["Rp"] = display_df["Rp"].apply(lambda x: f"{x:,.1f}")
        display_df["So"] = display_df["So"].apply(lambda x: f"{x:.4f}")
        display_df["Sg"] = display_df["Sg"].apply(lambda x: f"{x:.4f}")
        display_df["krg_kro"] = display_df["krg_kro"].apply(lambda x: f"{x:.6f}")
        st.dataframe(display_df, use_container_width=True)

        csv_data = df_result.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Prediction Results as CSV",
            data=csv_data,
            file_name="prediction_results.csv",
            mime="text/csv",
        )

        st.markdown("### Performance Curves")

        fig = make_subplots(
            rows=2,
            cols=3,
            subplot_titles=(
                "Np vs Pressure",
                "GOR vs Pressure",
                "Cumulative Gp vs Pressure",
                "So/Sg vs Pressure",
                "Rp vs Pressure",
                "krg/kro vs Sg",
            ),
            horizontal_spacing=0.12,
            vertical_spacing=0.15,
        )

        sat = df_result[df_result["is_saturated"]].sort_values("p", ascending=True)
        all_data = df_result.sort_values("p", ascending=True)

        fig.add_trace(
            go.Scatter(
                x=all_data["p"],
                y=all_data["Np"],
                mode="lines+markers",
                name="Np",
                line=dict(color="#1f77b4"),
            ),
            row=1,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=all_data["p"],
                y=all_data["GOR"],
                mode="lines+markers",
                name="GOR",
                line=dict(color="#d62728"),
            ),
            row=1,
            col=2,
        )

        fig.add_trace(
            go.Scatter(
                x=all_data["p"],
                y=all_data["Gp"],
                mode="lines+markers",
                name="Gp",
                line=dict(color="#2ca02c"),
            ),
            row=1,
            col=3,
        )

        fig.add_trace(
            go.Scatter(
                x=all_data["p"],
                y=all_data["So"],
                mode="lines+markers",
                name="So",
                line=dict(color="#1f77b4"),
            ),
            row=2,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=all_data["p"],
                y=all_data["Sg"],
                mode="lines+markers",
                name="Sg",
                line=dict(color="#ff7f0e"),
            ),
            row=2,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=all_data["p"],
                y=all_data["Rp"],
                mode="lines+markers",
                name="Rp",
                line=dict(color="#9467bd"),
            ),
            row=2,
            col=2,
        )

        fig.add_trace(
            go.Scatter(
                x=all_data["krg_kro"],
                y=all_data["Sg"],
                mode="lines+markers",
                name="krg/kro",
                line=dict(color="#8c564b"),
            ),
            row=2,
            col=3,
        )

        fig.update_xaxes(title_text="Pressure (psi)", row=1, col=1)
        fig.update_xaxes(title_text="Pressure (psi)", row=1, col=2)
        fig.update_xaxes(title_text="Pressure (psi)", row=1, col=3)
        fig.update_xaxes(title_text="Pressure (psi)", row=2, col=1)
        fig.update_xaxes(title_text="Pressure (psi)", row=2, col=2)
        fig.update_xaxes(title_text="krg/kro", row=2, col=3, type="log")

        fig.update_yaxes(title_text="Np (STB)", row=1, col=1)
        fig.update_yaxes(title_text="GOR (scf/STB)", row=1, col=2)
        fig.update_yaxes(title_text="Gp (scf)", row=1, col=3)
        fig.update_yaxes(title_text="Saturation", row=2, col=1)
        fig.update_yaxes(title_text="Rp (scf/STB)", row=2, col=2)
        fig.update_yaxes(title_text="Sg", row=2, col=3)

        fig.update_layout(
            height=700, showlegend=False, margin=dict(l=60, r=30, t=40, b=60)
        )
        st.plotly_chart(fig, use_container_width=True)

        if len(sat) > 0:
            st.markdown("### Drive Mechanism Insights")
            lowest_row = sat.sort_values("p", ascending=True).iloc[0]
            final_p = lowest_row["p"]
            final_So = lowest_row["So"]
            final_Sg = lowest_row["Sg"]
            final_GOR = lowest_row["GOR"]
            final_Rp = lowest_row["Rp"]
            final_RF = lowest_row["Np"] / N * 100

            insights = []
            insights.append(
                f"At abandonment ({final_p:.0f} psi): So = {final_So:.3f}, Sg = {final_Sg:.3f}"
            )
            insights.append(
                f"Initial GOR = Rsi = {float(pvt['Rs'][np.argmax(pvt['p'])]):.0f} scf/STB, "
                f"Final GOR = {final_GOR:.0f} scf/STB"
            )
            insights.append(
                f"Cumulative GOR (Rp) at abandonment: {final_Rp:.0f} scf/STB"
            )
            insights.append(f"Recovery Factor: {final_RF:.2f}%")

            if final_Sg > 0.05:
                insights.append(
                    "Significant free gas saturation developed — secondary gas cap may be forming."
                )
            if final_GOR > 2 * float(pvt["Rs"][np.argmax(pvt["p"])]):
                insights.append(
                    "GOR significantly exceeds solution GOR — gas is mobile and being produced preferentially."
                )
            if final_RF < 15:
                insights.append(
                    "Low recovery factor — typical for solution-gas drive without pressure support."
                )
            elif final_RF > 30:
                insights.append(
                    "High recovery factor — favorable depletion or additional drive mechanism active."
                )

            st.markdown("**Insights from Prediction:**")
            for ins in insights:
                st.markdown(f"- {ins}")


if __name__ == "__main__":
    render_prediction_page()
