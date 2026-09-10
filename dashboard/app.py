from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Market Risk Control Centre", layout="wide")
st.title("Australian Treasury Market Risk Control Centre")

report_dir = Path(st.sidebar.text_input("Report directory", "reports"))


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
model_performance = read_report("model_performance")
imputation_audit = read_report("imputation_audit")
treasury_positions = read_report("treasury_positions")
key_rate_dv01 = read_report("key_rate_dv01")
treasury_scenarios = read_report("treasury_scenarios")
frtb_summary = read_report("frtb_es_summary")
frtb_buckets = read_report("frtb_liquidity_buckets")
modellability = read_report("risk_factor_modellability")
es_backtesting = read_report("es_backtesting")
tail_uncertainty = read_report("tail_risk_uncertainty")
derivative_positions = read_report("derivative_positions")
derivative_scenarios = read_report("derivative_scenarios")
derivative_risk = read_report("derivative_historical_risk")

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
headline_cols[0].metric("Max 99% VaR", f"A${latest['var'].max():,.0f}")
headline_cols[1].metric("Limit breaches", int((risk_limits["status"] == "breach").sum()))
headline_cols[2].metric(
    "Validated models", int((model_monitoring["overall_status"] == "pass").sum())
)
market_date = pd.Timestamp(treasury_positions["as_of_date"].iloc[0]).strftime("%d %b %y")
headline_cols[3].metric("RBA market date", market_date)
headline_cols[4].metric(
    "Core runtime", f"{efficiency_values.get('analytics_runtime_seconds', 0):.2f}s"
)

(
    overview_tab,
    treasury_tab,
    frtb_tab,
    options_tab,
    validation_tab,
    stress_tab,
    controls_tab,
) = st.tabs(
    [
        "Risk overview",
        "Treasury book",
        "FRTB & liquidity",
        "Options",
        "Model validation",
        "Stress and attribution",
        "Controls and efficiency",
    ]
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
    left, right = st.columns(2)
    with left:
        st.subheader("Common-holdout quantile loss")
        fig = px.bar(
            model_performance,
            x="model",
            y="mean_quantile_loss",
            color="quantile_loss_rank",
            text_auto=".3g",
        )
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.subheader("Model ranking")
        st.dataframe(model_performance, use_container_width=True, hide_index=True)
    st.subheader("Model monitoring decision table")
    st.dataframe(model_monitoring, use_container_width=True, hide_index=True)
    st.subheader("Backtesting detail")
    st.dataframe(backtest_summary, use_container_width=True, hide_index=True)
    left, right = st.columns(2)
    with left:
        st.subheader("Expected Shortfall calibration")
        st.dataframe(es_backtesting, use_container_width=True, hide_index=True)
    with right:
        st.subheader("Tail-risk estimation uncertainty")
        st.dataframe(tail_uncertainty, use_container_width=True, hide_index=True)

with treasury_tab:
    bond_rows = treasury_positions[treasury_positions["instrument_type"] == "fixed_rate_bond"]
    treasury_metrics = st.columns(4)
    treasury_metrics[0].metric(
        "Net market value", f"A${treasury_positions['market_value_aud'].sum():,.0f}"
    )
    treasury_metrics[1].metric("Net DV01", f"A${bond_rows['dv01_aud'].sum():,.0f}")
    treasury_metrics[2].metric("Bond positions", len(bond_rows))
    treasury_metrics[3].metric("Market source", treasury_positions["market_source"].iloc[0])
    st.subheader("Trade-level valuation and sensitivities")
    st.dataframe(treasury_positions, use_container_width=True, hide_index=True)

    left, right = st.columns(2)
    with left:
        st.subheader("Key-rate DV01")
        key_rate_view = key_rate_dv01.groupby("curve_pillar", as_index=False)[
            "key_rate_dv01_aud"
        ].sum()
        fig = px.bar(key_rate_view, x="curve_pillar", y="key_rate_dv01_aud", text_auto=".2s")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.subheader("Full-revaluation scenario P&L")
        scenario_view = treasury_scenarios.groupby("scenario", as_index=False)["pnl_aud"].sum()
        fig = px.bar(scenario_view, x="scenario", y="pnl_aud", text_auto=".2s")
        st.plotly_chart(fig, use_container_width=True)

with frtb_tab:
    frtb = frtb_summary.iloc[0]
    frtb_metrics = st.columns(4)
    frtb_metrics[0].metric(
        "Liquidity-adjusted ES", f"A${frtb['liquidity_adjusted_es_aud']:,.0f}"
    )
    frtb_metrics[1].metric(
        "Stress-scaled ES", f"A${frtb['stress_scaled_es_aud']:,.0f}"
    )
    frtb_metrics[2].metric("Stress scalar", f"{frtb['stress_scaling_factor']:.3f}x")
    frtb_metrics[3].metric(
        "Modellability proxy reviews",
        int((modellability["modellability_proxy_status"] == "review").sum()),
    )
    left, right = st.columns(2)
    with left:
        st.subheader("Liquidity-horizon ES components")
        fig = px.bar(
            frtb_buckets,
            x="liquidity_horizon_days",
            y="scaled_es_component_aud",
            text_auto=".2s",
        )
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.subheader("Risk-factor data availability")
        st.dataframe(modellability, use_container_width=True, hide_index=True)
    st.caption("FRTB-inspired management view; not a regulatory capital calculation.")

with options_tab:
    option_risk = derivative_risk.iloc[0]
    option_metrics = st.columns(4)
    option_metrics[0].metric(
        "Option book value", f"A${option_risk['net_option_market_value_aud']:,.0f}"
    )
    option_metrics[1].metric(
        "Full-revaluation VaR", f"A${option_risk['full_revaluation_var_aud']:,.0f}"
    )
    option_metrics[2].metric(
        "Full-revaluation ES",
        f"A${option_risk['full_revaluation_expected_shortfall_aud']:,.0f}",
    )
    option_metrics[3].metric("Historical shocks", int(option_risk["observations"]))
    st.subheader("Trade-level Greeks")
    st.dataframe(derivative_positions, use_container_width=True, hide_index=True)
    st.subheader("Full revaluation versus delta-gamma-vega")
    scenario_comparison = (
        derivative_scenarios.groupby("scenario", as_index=False)[
            ["full_revaluation_pnl_aud", "delta_gamma_vega_pnl_aud"]
        ]
        .sum()
        .melt(id_vars="scenario", var_name="method", value_name="pnl_aud")
    )
    fig = px.bar(
        scenario_comparison,
        x="scenario",
        y="pnl_aud",
        color="method",
        barmode="group",
        text_auto=".2s",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("Approximation error by trade")
    st.dataframe(derivative_scenarios, use_container_width=True, hide_index=True)

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

    st.subheader("Imputation lineage")
    st.dataframe(imputation_audit, use_container_width=True, hide_index=True)

    st.subheader("Operating efficiency evidence")
    st.dataframe(efficiency, use_container_width=True, hide_index=True)
    st.subheader("Scenario engine benchmark")
    st.dataframe(benchmark, use_container_width=True, hide_index=True)
