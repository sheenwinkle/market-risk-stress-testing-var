from pathlib import Path

import numpy as np
import pandas as pd

from market_risk.derivatives import black_scholes_option, value_derivatives_book


def test_black_scholes_call_put_parity_and_greeks():
    call = black_scholes_option(100, 100, 1, 0.04, 0.25, "call", 0.02)
    put = black_scholes_option(100, 100, 1, 0.04, 0.25, "put", 0.02)

    parity = 100 * np.exp(-0.02) - 100 * np.exp(-0.04)
    assert np.isclose(call.price - put.price, parity)
    assert call.delta > 0
    assert put.delta < 0
    assert call.gamma > 0
    assert call.vega > 0


def test_derivatives_book_produces_full_revaluation_and_approximation_evidence():
    repo_root = Path(__file__).resolve().parents[1]
    rng = np.random.default_rng(17)
    index = pd.bdate_range("2022-01-01", periods=600)
    returns = pd.DataFrame(
        {
            "CBA.AX": rng.normal(0, 0.012, len(index)),
            "MQG.AX": rng.normal(0, 0.016, len(index)),
        },
        index=index,
    )
    prices = 100 * (1 + returns).cumprod()

    tables = value_derivatives_book(
        repo_root / "configs" / "derivatives_book.yml", prices, returns
    )

    assert len(tables["derivative_positions"]) == 3
    assert len(tables["derivative_scenarios"]) == 9
    assert tables["derivative_scenarios"]["approximation_error_aud"].abs().max() > 0
    risk = tables["derivative_historical_risk"].iloc[0]
    assert risk["observations"] == 500
    assert risk["full_revaluation_expected_shortfall_aud"] >= risk["full_revaluation_var_aud"]
