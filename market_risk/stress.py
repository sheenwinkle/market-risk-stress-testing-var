from __future__ import annotations

import numpy as np
import pandas as pd

from market_risk.config import PortfolioConfig


def configured_stress_scenarios(config: PortfolioConfig) -> pd.DataFrame:
    rows = []
    weights = pd.Series(config.weights)
    for scenario, details in config.stress_scenarios.items():
        shocks = pd.Series(details.get("shocks", {}), dtype=float).reindex(weights.index).fillna(0.0)
        scenario_return = float((weights * shocks).sum())
        rows.append(
            {
                "scenario": scenario,
                "description": details.get("description", ""),
                "scenario_return": scenario_return,
                "loss_aud": max(-scenario_return * config.value_aud, 0.0),
                "weighted_average_shock": scenario_return,
            }
        )
    return pd.DataFrame(rows).sort_values("loss_aud", ascending=False)


def stress_position_contributions(config: PortfolioConfig) -> pd.DataFrame:
    rows = []
    for scenario, details in config.stress_scenarios.items():
        for ticker, weight in config.weights.items():
            shock = float(details.get("shocks", {}).get(ticker, 0.0))
            pnl_aud = weight * shock * config.value_aud
            rows.append(
                {
                    "scenario": scenario,
                    "ticker": ticker,
                    "weight": weight,
                    "shock": shock,
                    "pnl_aud": pnl_aud,
                    "loss_contribution_aud": max(-pnl_aud, 0.0),
                }
            )
    return pd.DataFrame(rows).sort_values(["scenario", "loss_contribution_aud"], ascending=[True, False])


def reverse_stress_results(config: PortfolioConfig, stress_results: pd.DataFrame) -> pd.DataFrame:
    target = float(config.risk_limits.get("reverse_stress_loss_aud", config.value_aud * 0.1))
    results = stress_results.copy()
    results["target_loss_aud"] = target
    results["shock_multiplier_to_target"] = np.where(
        results["loss_aud"] > 0,
        target / results["loss_aud"],
        np.nan,
    )
    results["distance_to_target_aud"] = target - results["loss_aud"]
    return results.sort_values("shock_multiplier_to_target")


def historical_stress_windows(
    portfolio_returns: pd.Series,
    portfolio_value: float,
    holding_period_days: int = 10,
    top_n: int = 10,
) -> pd.DataFrame:
    clean = portfolio_returns.dropna()
    cumulative = (1.0 + clean).rolling(holding_period_days).apply(np.prod, raw=True) - 1.0
    worst = cumulative.dropna().sort_values().head(top_n)
    return pd.DataFrame(
        {
            "end_date": worst.index,
            "holding_period_days": holding_period_days,
            "scenario_return": worst.values,
            "loss_aud": (-worst.values * portfolio_value).clip(min=0.0),
        }
    )


def factor_sensitivities(
    portfolio_returns: pd.Series,
    factor_returns: pd.DataFrame,
) -> pd.DataFrame:
    aligned = pd.concat([portfolio_returns, factor_returns], axis=1, join="inner").dropna()
    if aligned.empty or factor_returns.empty:
        return pd.DataFrame(columns=["factor", "beta", "r_squared"])

    y = aligned.iloc[:, 0].to_numpy()
    x = aligned.iloc[:, 1:].to_numpy()
    x_with_intercept = np.column_stack([np.ones(len(x)), x])
    coefficients, *_ = np.linalg.lstsq(x_with_intercept, y, rcond=None)
    predictions = x_with_intercept @ coefficients
    residual_sum_squares = float(np.sum((y - predictions) ** 2))
    total_sum_squares = float(np.sum((y - y.mean()) ** 2))
    r_squared = 1.0 - residual_sum_squares / total_sum_squares if total_sum_squares > 0 else 0.0

    return pd.DataFrame(
        {
            "factor": aligned.columns[1:],
            "beta": coefficients[1:],
            "r_squared": r_squared,
        }
    ).sort_values("beta", key=lambda s: s.abs(), ascending=False)
