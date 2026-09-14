from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from market_risk.risk_models import historical_var_es


@dataclass(frozen=True)
class RiskFactorEvidenceResult:
    observation_evidence: pd.DataFrame
    nmrf_fallback: pd.DataFrame


def _observed_gap_days(observed_dates: pd.DatetimeIndex) -> tuple[int, float]:
    gaps = observed_dates.to_series().diff().dt.days.dropna()
    if gaps.empty:
        return 365, 365.0
    return int(gaps.max()), float(gaps.median())


def _public_proxy_status(
    observations: int,
    distinct_months: int,
    max_gap_days: int,
) -> str:
    if observations >= 24 and distinct_months >= 12 and max_gap_days <= 31:
        return "pass"
    if observations >= 24 and max_gap_days <= 90:
        return "watch"
    return "review"


def rfet_observation_evidence(
    raw_prices: pd.DataFrame,
    liquidity_horizons: dict[str, int],
) -> pd.DataFrame:
    """Build public-data RFET proxy evidence.

    Basel RFET requires real-price evidence. Public closing prices can show
    frequency and gaps, but they cannot prove executable trades or committed
    quotes, so regulatory RFET remains false by design.
    """
    latest = raw_prices.index.max()
    trailing = raw_prices.loc[raw_prices.index > latest - pd.Timedelta(days=365)]
    rows = []
    for risk_factor, horizon in liquidity_horizons.items():
        observed_dates = trailing.index[trailing[risk_factor].notna()]
        max_gap, median_gap = _observed_gap_days(observed_dates)
        observations = len(observed_dates)
        distinct_months = observed_dates.to_period("M").nunique()
        proxy_status = _public_proxy_status(observations, distinct_months, max_gap)
        rows.append(
            {
                "risk_factor": risk_factor,
                "liquidity_horizon_days": horizon,
                "public_observations_12m": observations,
                "distinct_months_12m": distinct_months,
                "max_gap_days": max_gap,
                "median_gap_days": median_gap,
                "public_frequency_proxy_status": proxy_status,
                "evidence_type": "public_closing_price",
                "missing_real_price_evidence": True,
                "regulatory_rfet_pass": False,
                "regulatory_limitation": (
                    "public closes do not prove trades, committed quotes, or "
                    "other real-price observations"
                ),
            }
        )
    return pd.DataFrame(rows)


def nmrf_stress_fallback(
    asset_returns: pd.DataFrame,
    weights: dict[str, float],
    liquidity_horizons: dict[str, int],
    observation_evidence: pd.DataFrame,
    portfolio_value_aud: float,
    confidence_level: float = 0.975,
) -> pd.DataFrame:
    rows = []
    evidence = observation_evidence.set_index("risk_factor")
    for risk_factor, weight in weights.items():
        returns = asset_returns[risk_factor].dropna()
        horizon_days = int(liquidity_horizons[risk_factor])
        ten_day_loss = historical_var_es(returns.rolling(10).sum().dropna(), confidence_level)
        scaled_loss_aud = (
            ten_day_loss.expected_shortfall
            * abs(float(weight))
            * portfolio_value_aud
            * np.sqrt(horizon_days / 10.0)
        )
        proxy_status = str(evidence.loc[risk_factor, "public_frequency_proxy_status"])
        rows.append(
            {
                "risk_factor": risk_factor,
                "portfolio_weight": float(weight),
                "liquidity_horizon_days": horizon_days,
                "confidence_level": confidence_level,
                "fallback_nmrf_stress_loss_aud": float(scaled_loss_aud),
                "fallback_triggered_by_public_proxy": proxy_status != "pass",
                "public_frequency_proxy_status": proxy_status,
                "capital_measure": False,
            }
        )
    return pd.DataFrame(rows).sort_values(
        "fallback_nmrf_stress_loss_aud", ascending=False
    ).reset_index(drop=True)


def risk_factor_evidence_report(
    raw_prices: pd.DataFrame,
    asset_returns: pd.DataFrame,
    weights: dict[str, float],
    liquidity_horizons: dict[str, int],
    portfolio_value_aud: float,
) -> RiskFactorEvidenceResult:
    observation_evidence = rfet_observation_evidence(raw_prices, liquidity_horizons)
    fallback = nmrf_stress_fallback(
        asset_returns,
        weights,
        liquidity_horizons,
        observation_evidence,
        portfolio_value_aud,
    )
    return RiskFactorEvidenceResult(
        observation_evidence=observation_evidence,
        nmrf_fallback=fallback,
    )
