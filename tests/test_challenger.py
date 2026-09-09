import numpy as np
import pandas as pd

from market_risk.challenger import garch_t_forecasts, model_performance_report


def test_garch_t_forecasts_are_holdout_only_and_positive():
    rng = np.random.default_rng(33)
    values = rng.standard_t(df=6, size=800) * 0.01
    returns = pd.Series(values, index=pd.bdate_range("2022-01-03", periods=800))

    forecasts = garch_t_forecasts(returns, 0.99, training_observations=500)

    assert len(forecasts) == 300
    assert forecasts["date"].min() == returns.index[500]
    assert (forecasts["var"] > 0).all()
    assert (forecasts["expected_shortfall"] > forecasts["var"]).all()


def test_model_performance_ranks_lower_quantile_loss_first():
    forecasts = pd.DataFrame(
        {
            "date": pd.to_datetime(["2025-01-02", "2025-01-03"] * 2),
            "model": ["a", "a", "b", "b"],
            "var": [0.03, 0.03, 0.20, 0.20],
            "expected_shortfall": [0.04, 0.04, 0.25, 0.25],
            "actual_return": [-0.01, -0.02, -0.01, -0.02],
            "is_exception": [False, False, False, False],
        }
    )

    result = model_performance_report(forecasts, 0.99)

    assert result.iloc[0]["model"] == "a"
    assert result.iloc[0]["quantile_loss_rank"] == 1
