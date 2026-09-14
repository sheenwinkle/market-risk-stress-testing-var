import numpy as np
import pandas as pd

from market_risk.rfet import risk_factor_evidence_report


def test_risk_factor_evidence_flags_public_proxy_and_nmrf_fallback():
    rng = np.random.default_rng(7)
    index = pd.bdate_range("2023-01-02", periods=280)
    returns = pd.DataFrame(
        {
            "LIQUID": rng.normal(0, 0.01, len(index)),
            "SPARSE": rng.normal(0, 0.012, len(index)),
        },
        index=index,
    )
    prices = 100 * (1 + returns).cumprod()
    prices.loc[index[-180:-40], "SPARSE"] = np.nan

    result = risk_factor_evidence_report(
        raw_prices=prices,
        asset_returns=returns,
        weights={"LIQUID": 0.7, "SPARSE": 0.3},
        liquidity_horizons={"LIQUID": 10, "SPARSE": 60},
        portfolio_value_aud=1_000_000,
    )

    evidence = result.observation_evidence.set_index("risk_factor")
    assert evidence.loc["LIQUID", "public_frequency_proxy_status"] == "pass"
    assert evidence.loc["SPARSE", "public_frequency_proxy_status"] == "review"
    assert not bool(evidence.loc["LIQUID", "regulatory_rfet_pass"])
    assert bool(evidence.loc["SPARSE", "missing_real_price_evidence"])

    fallback = result.nmrf_fallback.set_index("risk_factor")
    assert fallback.loc["SPARSE", "fallback_triggered_by_public_proxy"]
    assert not bool(fallback.loc["LIQUID", "fallback_triggered_by_public_proxy"])
    assert fallback.loc["SPARSE", "fallback_nmrf_stress_loss_aud"] > 0
