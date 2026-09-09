from __future__ import annotations

from statistics import median
from time import perf_counter

import numpy as np
import pandas as pd

from market_risk.config import PortfolioConfig


def scenario_performance_benchmark(
    config: PortfolioConfig,
    scenario_count: int = 50_000,
    repeats: int = 3,
) -> pd.DataFrame:
    """Compare matrix-based scenario valuation with a transparent row-loop reference."""
    weights = np.asarray(list(config.weights.values()), dtype=float)
    configured = [
        [float(details.get("shocks", {}).get(ticker, 0.0)) for ticker in config.weights]
        for details in config.stress_scenarios.values()
    ]
    if not configured:
        configured = [[0.0] * len(weights)]
    shock_matrix = np.resize(np.asarray(configured, dtype=float), (scenario_count, len(weights)))

    vector_times = []
    reference_times = []
    vector_result = np.array([])
    reference_result = np.array([])
    for _ in range(repeats):
        started = perf_counter()
        vector_result = shock_matrix @ weights
        vector_times.append(perf_counter() - started)

        started = perf_counter()
        reference_result = np.asarray(
            [sum(shock * weight for shock, weight in zip(row, weights)) for row in shock_matrix]
        )
        reference_times.append(perf_counter() - started)

    vector_seconds = median(vector_times)
    reference_seconds = median(reference_times)
    return pd.DataFrame(
        [
            {
                "scenario_count": scenario_count,
                "positions_per_scenario": len(weights),
                "vectorized_runtime_ms": vector_seconds * 1_000,
                "reference_loop_runtime_ms": reference_seconds * 1_000,
                "speedup_x": reference_seconds / max(vector_seconds, 1e-12),
                "max_absolute_difference": float(
                    np.max(np.abs(vector_result - reference_result))
                ),
                "benchmark_basis": "median of repeated in-process runs on this machine",
            }
        ]
    )


def operational_efficiency_report(
    config: PortfolioConfig,
    analytics_runtime_seconds: float,
    benchmark: pd.DataFrame,
    tables: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    assumptions = config.workflow_assumptions
    manual_steps = assumptions.get("manual_steps", {})
    manual_minutes = float(sum(float(value) for value in manual_steps.values()))
    review_minutes = float(assumptions.get("analyst_review_minutes", 10))
    business_days = float(assumptions.get("business_days_per_month", 22))
    time_reduction = (manual_minutes - review_minutes) / manual_minutes if manual_minutes else 0.0
    monthly_hours_saved = max(manual_minutes - review_minutes, 0.0) * business_days / 60.0
    rows_produced = int(sum(len(frame) for frame in tables.values()))
    speedup = float(benchmark["speedup_x"].iloc[0])

    return pd.DataFrame(
        [
            {
                "metric": "analytics_runtime_seconds",
                "value": analytics_runtime_seconds,
                "unit": "seconds",
                "basis": "measured",
                "interpretation": "Core calculations before file and database writes",
            },
            {
                "metric": "scenario_engine_speedup",
                "value": speedup,
                "unit": "times",
                "basis": "measured",
                "interpretation": "Vectorized engine versus transparent Python row loop",
            },
            {
                "metric": "report_tables_generated",
                "value": len(tables),
                "unit": "tables",
                "basis": "measured",
                "interpretation": "CSV and SQL-ready governed outputs per run",
            },
            {
                "metric": "report_rows_generated",
                "value": rows_produced,
                "unit": "rows",
                "basis": "measured",
                "interpretation": "Rows across the automated reporting pack",
            },
            {
                "metric": "manual_workflow_minutes",
                "value": manual_minutes,
                "unit": "minutes per daily run",
                "basis": "configured assumption",
                "interpretation": "Editable baseline for seven spreadsheet-style activities",
            },
            {
                "metric": "analyst_review_minutes",
                "value": review_minutes,
                "unit": "minutes per daily run",
                "basis": "configured assumption",
                "interpretation": "Human review remains required for control ownership",
            },
            {
                "metric": "modelled_process_time_reduction",
                "value": time_reduction * 100.0,
                "unit": "percent",
                "basis": "derived from configured assumptions",
                "interpretation": "Reduction in analyst preparation time, excluding review",
            },
            {
                "metric": "modelled_monthly_hours_saved",
                "value": monthly_hours_saved,
                "unit": "hours",
                "basis": "derived from configured assumptions",
                "interpretation": f"At {business_days:.0f} reporting days per month",
            },
        ]
    )


def render_management_summary(
    config: PortfolioConfig,
    risk_summary: pd.DataFrame,
    model_monitoring: pd.DataFrame,
    risk_limits: pd.DataFrame,
    stress_results: pd.DataFrame,
    efficiency: pd.DataFrame,
) -> str:
    metrics = efficiency.set_index("metric")["value"]
    worst_stress = stress_results.sort_values("loss_aud", ascending=False).iloc[0]
    breaches = risk_limits[risk_limits["status"] == "breach"]
    reviews = model_monitoring[model_monitoring["overall_status"] == "review"]
    headline = risk_summary.pivot(index="model", columns="metric", values="value_aud")

    model_lines = "\n".join(
        f"- {model}: VaR A${row['var']:,.0f}; ES A${row['expected_shortfall']:,.0f}."
        for model, row in headline.iterrows()
    )
    return f"""# Daily Market Risk Management Summary

**Portfolio:** {config.name}  
**As of:** {risk_summary['as_of_date'].max()}  
**Portfolio value:** A${config.value_aud:,.0f}

## Executive risk view

{model_lines}
- Worst configured scenario: **{worst_stress['scenario']}**, loss A${worst_stress['loss_aud']:,.0f}.
- Limit status: **{len(breaches)} breach(es)** across {len(risk_limits)} monitored measures.
- Model status: **{len(reviews)} model(s) require review** across {len(model_monitoring)} models.

## Operating efficiency

- Core analytics runtime: **{metrics['analytics_runtime_seconds']:.3f} seconds** on this machine.
- Scenario engine: **{metrics['scenario_engine_speedup']:.1f}x faster** than the reference row loop in the reproducible benchmark.
- Reporting pack: **{int(metrics['report_tables_generated'])} governed tables** and **{int(metrics['report_rows_generated']):,} rows** generated automatically.
- Modelled analyst preparation-time reduction: **{metrics['modelled_process_time_reduction']:.1f}%**, from {metrics['manual_workflow_minutes']:.0f} to {metrics['analyst_review_minutes']:.0f} minutes per daily run.
- Modelled capacity released: **{metrics['modelled_monthly_hours_saved']:.1f} hours per month**.

The time-saved figures are scenario estimates based on editable assumptions in `configs/portfolio.yml`; they are not claims from a production deployment. Human review and escalation remain mandatory.
"""
