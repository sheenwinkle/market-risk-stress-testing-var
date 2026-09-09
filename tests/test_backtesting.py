import pandas as pd

from market_risk.backtesting import (
    basel_traffic_light,
    christoffersen_independence_test,
    kupiec_pof_test,
    run_backtest,
)


def test_basel_traffic_light_boundaries():
    assert basel_traffic_light(4) == "green"
    assert basel_traffic_light(5) == "yellow"
    assert basel_traffic_light(9) == "yellow"
    assert basel_traffic_light(10) == "red"


def test_kupiec_test_penalises_too_many_exceptions():
    exceptions = pd.Series([True] * 20 + [False] * 80)

    lr, p_value = kupiec_pof_test(exceptions, confidence_level=0.99)

    assert lr > 0
    assert p_value < 0.05


def test_christoffersen_handles_no_exception_series():
    lr, p_value = christoffersen_independence_test(pd.Series([False] * 50))

    assert lr >= 0
    assert 0 <= p_value <= 1


def test_run_backtest_returns_exception_rates():
    forecasts = pd.DataFrame(
        {
            "model": ["historical"] * 5,
            "is_exception": [False, True, False, False, False],
        }
    )

    result = run_backtest(forecasts, confidence_level=0.99)

    assert result.model == "historical"
    assert result.observations == 5
    assert result.exceptions == 1
    assert result.actual_exception_rate == 0.2
