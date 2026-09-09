from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from market_risk.risk_models import historical_var_es

ALLOWED_LIQUIDITY_HORIZONS = (10, 20, 40, 60, 120)


@dataclass(frozen=True)
class FrtbEsResult:
    summary: pd.DataFrame
    liquidity_buckets: pd.DataFrame
    modellability_proxy: pd.DataFrame


def _ten_day_pnl_returns(daily_returns: pd.DataFrame, weights: pd.Series) -> pd.Series:
    daily_pnl_return = daily_returns.mul(weights, axis="columns").sum(axis=1)
    return daily_pnl_return.rolling(10).sum().dropna()


def liquidity_horizon_expected_shortfall(
    asset_returns: pd.DataFrame,
    weights: dict[str, float],
    liquidity_horizons: dict[str, int],
    confidence_level: float = 0.975,
) -> tuple[float, pd.DataFrame]:
    """Calculate the MAR33-style liquidity-horizon aggregation on 10-day P&L returns."""
    tickers = list(weights)
    missing = set(tickers) - set(asset_returns.columns)
    if missing:
        raise ValueError(f"Asset returns are missing: {sorted(missing)}")
    invalid = {
        ticker: horizon
        for ticker, horizon in liquidity_horizons.items()
        if horizon not in ALLOWED_LIQUIDITY_HORIZONS
    }
    if invalid:
        raise ValueError(f"Unsupported liquidity horizons: {invalid}")

    aligned = asset_returns[tickers].dropna()
    weight_series = pd.Series(weights, dtype=float)
    base_returns = _ten_day_pnl_returns(aligned, weight_series)
    base_es = historical_var_es(base_returns, confidence_level).expected_shortfall
    rows = [
        {
            "liquidity_horizon_days": 10,
            "included_assets": ",".join(tickers),
            "ten_day_es_return": base_es,
            "horizon_increment_days": 10,
            "scaled_es_component": base_es,
            "squared_contribution": base_es**2,
        }
    ]

    previous_horizon = 10
    squared_total = base_es**2
    for horizon in ALLOWED_LIQUIDITY_HORIZONS[1:]:
        included = [ticker for ticker in tickers if liquidity_horizons[ticker] >= horizon]
        if not included:
            previous_horizon = horizon
            continue
        subset_weights = weight_series.reindex(included)
        subset_returns = _ten_day_pnl_returns(aligned[included], subset_weights)
        subset_es = historical_var_es(subset_returns, confidence_level).expected_shortfall
        increment = horizon - previous_horizon
        scaled_component = subset_es * np.sqrt(increment / 10.0)
        squared_contribution = scaled_component**2
        squared_total += squared_contribution
        rows.append(
            {
                "liquidity_horizon_days": horizon,
                "included_assets": ",".join(included),
                "ten_day_es_return": subset_es,
                "horizon_increment_days": increment,
                "scaled_es_component": scaled_component,
                "squared_contribution": squared_contribution,
            }
        )
        previous_horizon = horizon

    return float(np.sqrt(squared_total)), pd.DataFrame(rows)


def stressed_es_scalar(
    portfolio_ten_day_returns: pd.Series,
    confidence_level: float = 0.975,
    window_observations: int = 250,
) -> tuple[float, float, float, pd.Timestamp, pd.Timestamp]:
    clean = portfolio_ten_day_returns.dropna().astype(float)
    if len(clean) < window_observations:
        raise ValueError("Not enough observations to identify a one-year stress window.")
    current_es = historical_var_es(clean, confidence_level).expected_shortfall
    candidates = []
    for end in range(window_observations, len(clean) + 1):
        window = clean.iloc[end - window_observations : end]
        window_es = historical_var_es(window, confidence_level).expected_shortfall
        candidates.append((window_es, window.index.min(), window.index.max()))
    stress_es, start_date, end_date = max(candidates, key=lambda row: row[0])
    scalar = max(stress_es / current_es, 1.0) if current_es > 0 else 1.0
    return float(scalar), current_es, stress_es, start_date, end_date


def risk_factor_modellability_proxy(
    raw_prices: pd.DataFrame,
    liquidity_horizons: dict[str, int],
) -> pd.DataFrame:
    """Transparent data-availability proxy; this is not the regulatory RFET."""
    latest = raw_prices.index.max()
    trailing = raw_prices.loc[raw_prices.index > latest - pd.Timedelta(days=365)]
    rows = []
    for ticker, horizon in liquidity_horizons.items():
        observed_dates = trailing.index[trailing[ticker].notna()]
        gaps = observed_dates.to_series().diff().dt.days.dropna()
        observation_count = len(observed_dates)
        distinct_months = observed_dates.to_period("M").nunique()
        max_gap = int(gaps.max()) if not gaps.empty else 365
        passes_proxy = observation_count >= 24 and distinct_months >= 12 and max_gap <= 90
        rows.append(
            {
                "risk_factor": ticker,
                "liquidity_horizon_days": horizon,
                "observations_12m": observation_count,
                "distinct_months_12m": distinct_months,
                "max_observation_gap_days": max_gap,
                "modellability_proxy_status": "pass" if passes_proxy else "review",
                "regulatory_rfet": False,
            }
        )
    return pd.DataFrame(rows)


def frtb_expected_shortfall_report(
    asset_returns: pd.DataFrame,
    raw_prices: pd.DataFrame,
    weights: dict[str, float],
    liquidity_horizons: dict[str, int],
    portfolio_value: float,
    confidence_level: float = 0.975,
) -> FrtbEsResult:
    liquidity_es, buckets = liquidity_horizon_expected_shortfall(
        asset_returns,
        weights,
        liquidity_horizons,
        confidence_level,
    )
    ten_day_returns = _ten_day_pnl_returns(
        asset_returns[list(weights)].dropna(), pd.Series(weights, dtype=float)
    )
    scalar, current_es, stress_es, start_date, end_date = stressed_es_scalar(
        ten_day_returns, confidence_level
    )
    summary = pd.DataFrame(
        [
            {
                "confidence_level": confidence_level,
                "base_horizon_days": 10,
                "current_full_portfolio_es_return": current_es,
                "stress_window_es_return": stress_es,
                "stress_scaling_factor": scalar,
                "stress_window_start": start_date,
                "stress_window_end": end_date,
                "liquidity_adjusted_es_return": liquidity_es,
                "stress_scaled_es_return": liquidity_es * scalar,
                "liquidity_adjusted_es_aud": liquidity_es * portfolio_value,
                "stress_scaled_es_aud": liquidity_es * scalar * portfolio_value,
                "regulatory_capital_measure": False,
            }
        ]
    )
    buckets = buckets.copy()
    buckets["scaled_es_component_aud"] = buckets["scaled_es_component"] * portfolio_value
    return FrtbEsResult(
        summary=summary,
        liquidity_buckets=buckets,
        modellability_proxy=risk_factor_modellability_proxy(raw_prices, liquidity_horizons),
    )
