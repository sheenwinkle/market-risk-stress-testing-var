from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Market Risk Control Centre", layout="wide")
st.title("Australian Treasury Market Risk Control Centre")

report_dir = Path(st.sidebar.text_input("Report directory", "reports"))


@st.cache_data
def read_report(name: str) -> pd.DataFrame:
    path = report_dir / f"{name}.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


risk_summary = read_report("risk_summary")
backtest = read_report("var_backtest")
backtest_summary = read_report("backtest_summary")
stress = read_report("stress_results")
historical_stress = read_report("historical_stress")
component = read_report("component_var")
portfolio_returns = read_report("portfolio_returns")
model_monitoring = read_report("model_monitoring")
risk_limits = read_report("risk_limits")
reverse_stress = read_report("reverse_stress")
stress_contributions = read_report("stress_contributions")
data_quality = read_report("data_quality")
efficiency = read_report("operational_efficiency")
benchmark = read_report("performance_benchmark")

if risk_summary.empty:
    st.warning("Run `market-risk run` first to create reports.")
    st.stop()

latest = risk_summary.pivot_table(
    index="model",
    columns="metric",
    values="value_aud",
    aggfunc="last",
).reset_index()

efficiency_values = efficiency.set_index("metric")["value"] if not efficiency.empty else pd.Series()
headline_cols = st.columns(5)
headline_cols[0].metric("Portfolio", "A$1.0m")
headline_cols[1].metric("Max 99% VaR", f"A${latest['var'].max():,.0f}")
headline_cols[2].metric("Max 99% ES", f"A${latest['expected_shortfall'].max():,.0f}")
headline_cols[3].metric("Limit breaches", int((risk_limits["status"] == "breach").sum()))
headline_cols[4].metric(
    "Prep-time reduction",
    f"{efficiency_values.get('modelled_process_time_reduction', 0):.1f}%",
)

overview_tab, validation_tab, stress_tab, controls_tab = st.tabs(
    ["Risk overview", "Model validation", "Stress and attribution", "Controls and efficiency"]
)

with overview_tab:
    st.subheader("Portfolio returns and rolling VaR")
    if not portfolio_returns.empty and not backtest.empty:
        portfolio_returns["date"] = pd.to_datetime(portfolio_returns["date"])
        backtest["date"] = pd.to_datetime(backtest["date"])
        model_options = latest["model"].tolist()
        selected_model = st.segmented_control(
            "VaR model",
            options=model_options,
            default="ewma" if "ewma" in model_options else model_options[0],
        )
        chart_data = portfolio_returns.merge(
            backtest[backtest["model"] == selected_model][["date", "var"]],
            on="date",
            how="left",
        )
        chart_data["negative_var"] = -chart_data["var"]
        fig = px.line(
            chart_data,
            x="date",
            y=["portfolio_return", "negative_var"],
            labels={"value": "daily return", "variable": "series"},
        )
        st.plotly_chart(fig, use_container_width=True)

    left, right = st.columns(2)
    with left:
        st.subheader("Current model comparison")
        st.dataframe(latest, use_container_width=True, hide_index=True)
    with right:
        st.subheader("Component VaR")
        fig = px.bar(component, x="ticker", y="component_var_aud", text_auto=".2s")
        st.plotly_chart(fig, use_container_width=True)

with validation_tab:
    st.subheader("Model monitoring decision table")
    st.dataframe(model_monitoring, use_container_width=True, hide_index=True)
    st.subheader("Backtesting detail")
    st.dataframe(backtest_summary, use_container_width=True, hide_index=True)

with stress_tab:
    left, right = st.columns(2)
    with left:
        st.subheader("Configured scenario losses")
        fig = px.bar(stress, x="scenario", y="loss_aud", color="scenario", text_auto=".2s")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.subheader("Reverse stress distance")
        st.dataframe(reverse_stress, use_container_width=True, hide_index=True)

    selected_scenario = st.selectbox("Position attribution scenario", stress["scenario"].tolist())
    contribution_view = stress_contributions[stress_contributions["scenario"] == selected_scenario]
    fig = px.bar(
        contribution_view,
        x="ticker",
        y="loss_contribution_aud",
        text_auto=".2s",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("Worst historical 10-day windows")
    st.dataframe(historical_stress, use_container_width=True, hide_index=True)

with controls_tab:
    left, right = st.columns(2)
    with left:
        st.subheader("Risk limit utilisation")
        fig = px.bar(
            risk_limits,
            x="dimension",
            y="utilisation_pct",
            color="status",
            text_auto=".1%",
        )
        fig.add_hline(y=1.0, line_dash="dash", annotation_text="limit")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.subheader("Data quality controls")
        st.dataframe(data_quality, use_container_width=True, hide_index=True)

    st.subheader("Operating efficiency evidence")
    st.dataframe(efficiency, use_container_width=True, hide_index=True)
    st.subheader("Scenario engine benchmark")
    st.dataframe(benchmark, use_container_width=True, hide_index=True)
