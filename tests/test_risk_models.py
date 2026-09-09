import numpy as np
import pandas as pd

from market_risk.risk_models import (
    component_var,
    ewma_var_es,
    historical_var_es,
    parametric_var_es,
)


def test_ewma_var_reacts_to_recent_volatility():
    calm_then_volatile = pd.Series([0.001] * 100 + [0.04, -0.05, 0.03, -0.04])
    volatile_then_calm = pd.Series([0.04, -0.05, 0.03, -0.04] + [0.001] * 100)

    recent_shock = ewma_var_es(calm_then_volatile, 0.99)
    old_shock = ewma_var_es(volatile_then_calm, 0.99)

    assert recent_shock.var > old_shock.var
    assert recent_shock.expected_shortfall > recent_shock.var


def test_historical_var_es_uses_left_tail_losses():
    returns = pd.Series([-0.08, -0.04, -0.02, 0.0, 0.01, 0.02, 0.03])

    measure = historical_var_es(returns, confidence_level=0.95)

    assert measure.var == 0.08
    assert measure.expected_shortfall >= measure.var


def test_parametric_var_es_is_positive_for_volatile_series():
    rng = np.random.default_rng(7)
    returns = pd.Series(rng.normal(0.0001, 0.012, 1000))

    measure = parametric_var_es(returns, confidence_level=0.99)

    assert measure.var > 0
    assert measure.expected_shortfall > measure.var


def test_component_var_reconciles_to_total_parametric_vol_var():
    rng = np.random.default_rng(11)
    asset_returns = pd.DataFrame(
        {
            "A": rng.normal(0, 0.010, 600),
            "B": rng.normal(0, 0.012, 600),
            "C": rng.normal(0, 0.008, 600),
        }
    )
    weights = {"A": 0.5, "B": 0.3, "C": 0.2}

    result = component_var(asset_returns, weights, 0.99, 1_000_000)

    assert set(result["ticker"]) == set(weights)
    assert result["component_var_aud"].sum() > 0
    assert abs(result["pct_of_total"].sum() - 1.0) < 1e-9
