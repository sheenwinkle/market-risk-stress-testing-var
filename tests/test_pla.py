import numpy as np
import pandas as pd

from market_risk.pla import pnl_attribution_report


def test_pnl_attribution_produces_daily_summary_and_betas():
    rng = np.random.default_rng(42)
    dates = pd.bdate_range("2022-01-03", periods=260)
    factors = pd.DataFrame(
        {
            "market": rng.normal(0, 0.01, len(dates)),
            "fx": rng.normal(0, 0.004, len(dates)),
            "rates": rng.normal(0, 0.002, len(dates)),
        },
        index=dates,
    )
    asset_returns = pd.DataFrame(
        {
            "CBA.AX": 1.1 * factors["market"] + 0.2 * factors["fx"] + rng.normal(0, 0.002, len(dates)),
            "NAB.AX": 0.9 * factors["market"] - 0.1 * factors["rates"] + rng.normal(0, 0.002, len(dates)),
        },
        index=dates,
    )

    result = pnl_attribution_report(
        asset_returns=asset_returns,
        factor_returns=factors,
        weights={"CBA.AX": 0.6, "NAB.AX": 0.4},
        portfolio_value_aud=1_000_000,
    )

    assert len(result.daily) == len(dates)
    assert set(result.summary["comparison"]) == {
        "actual_vs_hypothetical",
        "hypothetical_vs_risk_theoretical",
    }
    assert set(result.summary["pla_status"]) <= {"pass", "watch", "review"}
    assert (
        result.summary.set_index("comparison").loc[
            "hypothetical_vs_risk_theoretical", "spearman_correlation"
        ]
        > 0.9
    )
    assert len(result.factor_betas) == 6
    assert result.daily["actual_minus_hypothetical_aud"].abs().mean() > 0
