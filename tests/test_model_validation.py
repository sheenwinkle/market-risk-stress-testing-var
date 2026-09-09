import numpy as np
import pandas as pd

from market_risk.model_validation import (
    block_bootstrap_tail_uncertainty,
    es_calibration_backtest,
)


def test_es_calibration_flags_material_understatement():
    rng = np.random.default_rng(9)
    actual = rng.normal(0, 0.01, 2_000)
    forecasts = pd.DataFrame(
        {
            "model": "understated",
            "actual_return": actual,
            "var": 0.005,
            "expected_shortfall": 0.006,
        }
    )

    result = es_calibration_backtest(forecasts, 0.99, bootstrap_samples=500).iloc[0]

    assert result["z2_statistic"] > 0
    assert result["underestimation_p_value"] < 0.05
    assert result["es_calibration_status"] == "review"


def test_block_bootstrap_reports_ordered_nonzero_interval():
    rng = np.random.default_rng(11)
    returns = pd.Series(rng.standard_t(5, 800) * 0.01)

    result = block_bootstrap_tail_uncertainty(
        returns, 0.99, 1_000_000, bootstrap_samples=100
    )

    assert set(result["metric"]) == {"var", "expected_shortfall"}
    assert (result["ci_95_lower_aud"] < result["point_estimate_aud"]).all()
    assert (result["point_estimate_aud"] < result["ci_95_upper_aud"]).all()
    assert (result["relative_interval_width"] > 0).all()
