import numpy as np
import pandas as pd

from market_risk.frtb import (
    frtb_expected_shortfall_report,
    liquidity_horizon_expected_shortfall,
)


def _returns() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    index = pd.bdate_range("2018-01-01", periods=1_300)
    common = rng.standard_t(6, len(index)) * 0.008
    return pd.DataFrame(
        {
            "LIQUID": common + rng.normal(0, 0.002, len(index)),
            "ILLIQUID": 1.2 * common + rng.normal(0, 0.003, len(index)),
        },
        index=index,
    )


def test_liquidity_horizon_aggregation_reconciles_to_bucket_components():
    result, buckets = liquidity_horizon_expected_shortfall(
        _returns(),
        {"LIQUID": 0.6, "ILLIQUID": 0.4},
        {"LIQUID": 10, "ILLIQUID": 60},
    )

    assert set(buckets["liquidity_horizon_days"]) == {10, 20, 40, 60}
    assert np.isclose(result**2, buckets["squared_contribution"].sum())
    assert result > buckets.iloc[0]["ten_day_es_return"]


def test_frtb_report_identifies_stress_window_and_modellability_evidence():
    returns = _returns()
    prices = 100 * (1 + returns).cumprod()
    report = frtb_expected_shortfall_report(
        returns,
        prices,
        {"LIQUID": 0.6, "ILLIQUID": 0.4},
        {"LIQUID": 10, "ILLIQUID": 60},
        1_000_000,
    )

    summary = report.summary.iloc[0]
    assert summary["stress_scaling_factor"] >= 1.0
    assert summary["stress_scaled_es_aud"] >= summary["liquidity_adjusted_es_aud"]
    assert not bool(summary["regulatory_capital_measure"])
    assert set(report.modellability_proxy["modellability_proxy_status"]) == {"pass"}
