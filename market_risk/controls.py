from __future__ import annotations

import numpy as np
import pandas as pd

from market_risk.config import PortfolioConfig


def data_quality_report(
    prices: pd.DataFrame,
    required_tickers: list[str],
    source_type: str = "unknown",
    freshness_threshold_days: int = 7,
) -> pd.DataFrame:
    available_tickers = [ticker for ticker in required_tickers if ticker in prices.columns]
    duplicate_dates = int(prices.index.duplicated().sum())
    missing_cells = int(prices[available_tickers].isna().sum().sum())
    nonpositive_prices = int((prices[available_tickers] <= 0).sum().sum())
    date_gaps = prices.index.to_series().sort_values().diff().dt.days.dropna()
    max_calendar_gap = int(date_gaps.max()) if not date_gaps.empty else 0
    as_of = pd.Timestamp.now(tz="UTC").tz_localize(None).normalize()
    latest = pd.Timestamp(prices.index.max()).normalize()
    age_days = max((as_of - latest).days, 0)
    checks = [
        ("missing_required_tickers", len(set(required_tickers) - set(prices.columns)), 0),
        ("duplicate_dates", duplicate_dates, 0),
        ("missing_price_cells", missing_cells, 0),
        ("nonpositive_prices", nonpositive_prices, 0),
        ("max_calendar_gap_days", max_calendar_gap, 5),
        ("data_age_days", age_days, freshness_threshold_days),
    ]
    report = pd.DataFrame(
        [
            {
                "check": name,
                "observed_value": observed,
                "threshold": threshold,
                "status": "pass" if observed <= threshold else "fail",
            }
            for name, observed, threshold in checks
        ]
    )
    source_row = pd.DataFrame(
        [{"check": "source_type", "observed_value": source_type, "threshold": "approved source", "status": "info"}]
    )
    return pd.concat([report, source_row], ignore_index=True)


def risk_limit_report(
    risk_summary: pd.DataFrame,
    stress_results: pd.DataFrame,
    config: PortfolioConfig,
) -> pd.DataFrame:
    rows = []
    mappings = [
        ("var", "var_aud", risk_summary[risk_summary["metric"] == "var"]),
        (
            "expected_shortfall",
            "expected_shortfall_aud",
            risk_summary[risk_summary["metric"] == "expected_shortfall"],
        ),
    ]
    for metric, limit_key, frame in mappings:
        limit = config.risk_limits.get(limit_key)
        if limit is None:
            continue
        for row in frame.itertuples(index=False):
            rows.append(
                {
                    "risk_type": metric,
                    "dimension": row.model,
                    "observed_aud": row.value_aud,
                    "limit_aud": limit,
                    "utilisation_pct": row.value_aud / limit,
                    "headroom_aud": limit - row.value_aud,
                    "status": "pass" if row.value_aud <= limit else "breach",
                }
            )

    stress_limit = config.risk_limits.get("stress_loss_aud")
    if stress_limit is not None:
        for row in stress_results.itertuples(index=False):
            rows.append(
                {
                    "risk_type": "stress_loss",
                    "dimension": row.scenario,
                    "observed_aud": row.loss_aud,
                    "limit_aud": stress_limit,
                    "utilisation_pct": row.loss_aud / stress_limit,
                    "headroom_aud": stress_limit - row.loss_aud,
                    "status": "pass" if row.loss_aud <= stress_limit else "breach",
                }
            )
    return pd.DataFrame(rows).sort_values("utilisation_pct", ascending=False)


def model_monitoring_report(backtests: pd.DataFrame) -> pd.DataFrame:
    frame = backtests.copy()
    frame["exception_rate_gap_bps"] = (
        frame["actual_exception_rate"] - frame["expected_exception_rate"]
    ) * 10_000
    frame["overall_status"] = np.where(
        (frame["coverage_status"] == "pass")
        & (frame["independence_status"] == "pass")
        & (frame["basel_traffic_light"] != "red"),
        "pass",
        "review",
    )
    return frame[
        [
            "model",
            "observations",
            "exceptions",
            "actual_exception_rate",
            "exception_rate_gap_bps",
            "kupiec_p_value",
            "christoffersen_p_value",
            "conditional_coverage_p_value",
            "recent_250_exceptions",
            "basel_traffic_light",
            "coverage_status",
            "independence_status",
            "overall_status",
        ]
    ]
