from pathlib import Path

import pandas as pd

from market_risk.config import load_config
from market_risk.controls import data_quality_report
from market_risk.efficiency import scenario_performance_benchmark


def test_data_quality_flags_missing_ticker():
    prices = pd.DataFrame(
        {"A": [10.0, 10.5]},
        index=pd.to_datetime(["2025-01-02", "2025-01-03"]),
    )

    report = data_quality_report(prices, ["A", "B"]).set_index("check")

    assert report.loc["missing_required_tickers", "observed_value"] == 1
    assert report.loc["missing_required_tickers", "status"] == "fail"
    assert report.loc["source_type", "observed_value"] == "unknown"


def test_vectorized_scenario_benchmark_reconciles():
    config = load_config(Path(__file__).resolve().parents[1] / "configs" / "portfolio.yml")

    benchmark = scenario_performance_benchmark(config, scenario_count=1_000, repeats=1).iloc[0]

    assert benchmark["max_absolute_difference"] < 1e-12
    assert benchmark["speedup_x"] > 0
