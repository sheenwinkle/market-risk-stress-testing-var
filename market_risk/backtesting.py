from __future__ import annotations

from dataclasses import dataclass
from math import erfc, log, sqrt

import pandas as pd


@dataclass(frozen=True)
class BacktestResult:
    model: str
    confidence_level: float
    observations: int
    exceptions: int
    expected_exception_rate: float
    actual_exception_rate: float
    kupiec_lr: float
    kupiec_p_value: float
    christoffersen_lr: float
    christoffersen_p_value: float
    conditional_coverage_lr: float
    conditional_coverage_p_value: float
    recent_250_exceptions: int
    basel_traffic_light: str
    coverage_status: str
    independence_status: str


def _chi_square_1_sf(statistic: float) -> float:
    if statistic <= 0:
        return 1.0
    return float(erfc(sqrt(statistic / 2.0)))


def _chi_square_2_sf(statistic: float) -> float:
    if statistic <= 0:
        return 1.0
    return float(pow(2.718281828459045, -statistic / 2.0))


def basel_traffic_light(exception_count: int) -> str:
    """Basel 99% VaR traffic-light thresholds over the latest 250 observations."""
    if exception_count <= 4:
        return "green"
    if exception_count <= 9:
        return "yellow"
    return "red"


def _binomial_log_likelihood(successes: int, trials: int, probability: float) -> float:
    if trials == 0:
        return 0.0
    probability = min(max(probability, 1e-12), 1 - 1e-12)
    return successes * log(probability) + (trials - successes) * log(1 - probability)


def kupiec_pof_test(exceptions: pd.Series, confidence_level: float) -> tuple[float, float]:
    flags = exceptions.astype(bool)
    observations = len(flags)
    exception_count = int(flags.sum())
    expected_rate = 1.0 - confidence_level
    observed_rate = exception_count / observations if observations else 0.0
    ll_null = _binomial_log_likelihood(exception_count, observations, expected_rate)
    ll_alt = _binomial_log_likelihood(exception_count, observations, observed_rate)
    lr = max(-2.0 * (ll_null - ll_alt), 0.0)
    return lr, _chi_square_1_sf(lr)


def christoffersen_independence_test(exceptions: pd.Series) -> tuple[float, float]:
    flags = exceptions.astype(int).reset_index(drop=True)
    if len(flags) < 2:
        return 0.0, 1.0

    previous = flags.shift(1).dropna().astype(int)
    current = flags.iloc[1:].astype(int)
    n00 = int(((previous == 0) & (current == 0)).sum())
    n01 = int(((previous == 0) & (current == 1)).sum())
    n10 = int(((previous == 1) & (current == 0)).sum())
    n11 = int(((previous == 1) & (current == 1)).sum())

    pi = (n01 + n11) / max(n00 + n01 + n10 + n11, 1)
    pi0 = n01 / max(n00 + n01, 1)
    pi1 = n11 / max(n10 + n11, 1)

    ll_null = _binomial_log_likelihood(n01 + n11, n00 + n01 + n10 + n11, pi)
    ll_alt = _binomial_log_likelihood(n01, n00 + n01, pi0) + _binomial_log_likelihood(
        n11, n10 + n11, pi1
    )
    lr = max(-2.0 * (ll_null - ll_alt), 0.0)
    return lr, _chi_square_1_sf(lr)


def run_backtest(forecasts: pd.DataFrame, confidence_level: float) -> BacktestResult:
    if forecasts.empty:
        raise ValueError("Forecast dataframe is empty.")
    model = str(forecasts["model"].iloc[0])
    exceptions = forecasts["is_exception"].astype(bool)
    kupiec_lr, kupiec_p_value = kupiec_pof_test(exceptions, confidence_level)
    christoffersen_lr, christoffersen_p_value = christoffersen_independence_test(exceptions)
    conditional_coverage_lr = kupiec_lr + christoffersen_lr
    conditional_coverage_p_value = _chi_square_2_sf(conditional_coverage_lr)
    observations = len(exceptions)
    exception_count = int(exceptions.sum())
    return BacktestResult(
        model=model,
        confidence_level=confidence_level,
        observations=observations,
        exceptions=exception_count,
        expected_exception_rate=1.0 - confidence_level,
        actual_exception_rate=exception_count / observations,
        kupiec_lr=kupiec_lr,
        kupiec_p_value=kupiec_p_value,
        christoffersen_lr=christoffersen_lr,
        christoffersen_p_value=christoffersen_p_value,
        conditional_coverage_lr=conditional_coverage_lr,
        conditional_coverage_p_value=conditional_coverage_p_value,
        recent_250_exceptions=int(exceptions.tail(250).sum()),
        basel_traffic_light=basel_traffic_light(int(exceptions.tail(250).sum())),
        coverage_status="pass" if kupiec_p_value >= 0.05 else "fail",
        independence_status="pass" if christoffersen_p_value >= 0.05 else "fail",
    )
