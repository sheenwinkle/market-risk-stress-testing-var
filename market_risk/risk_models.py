from __future__ import annotations

from dataclasses import dataclass
from statistics import NormalDist

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class TailRiskMeasure:
    model: str
    confidence_level: float
    var: float
    expected_shortfall: float


def historical_var_es(returns: pd.Series, confidence_level: float) -> TailRiskMeasure:
    clean = returns.dropna()
    if clean.empty:
        raise ValueError("Returns series is empty.")

    alpha = 1.0 - confidence_level
    quantile = clean.quantile(alpha, interpolation="lower")
    tail = clean[clean <= quantile]
    return TailRiskMeasure(
        model="historical",
        confidence_level=confidence_level,
        var=float(max(-quantile, 0.0)),
        expected_shortfall=float(max(-tail.mean(), 0.0)),
    )


def parametric_var_es(returns: pd.Series, confidence_level: float) -> TailRiskMeasure:
    clean = returns.dropna()
    if len(clean) < 2:
        raise ValueError("At least two observations are required.")

    alpha = 1.0 - confidence_level
    mu = float(clean.mean())
    sigma = float(clean.std(ddof=1))
    z = NormalDist().inv_cdf(alpha)
    phi = np.exp(-0.5 * z**2) / np.sqrt(2 * np.pi)
    var = -(mu + z * sigma)
    expected_shortfall = -(mu - sigma * phi / alpha)
    return TailRiskMeasure(
        model="parametric_normal",
        confidence_level=confidence_level,
        var=float(max(var, 0.0)),
        expected_shortfall=float(max(expected_shortfall, 0.0)),
    )


def ewma_var_es(
    returns: pd.Series,
    confidence_level: float,
    decay: float = 0.94,
) -> TailRiskMeasure:
    """RiskMetrics-style EWMA volatility with a zero conditional mean."""
    clean = returns.dropna().astype(float)
    if len(clean) < 2:
        raise ValueError("At least two observations are required.")
    if not 0.0 < decay < 1.0:
        raise ValueError("EWMA decay must be between 0 and 1.")

    variance = float(clean.iloc[: min(20, len(clean))].var(ddof=1))
    for value in clean.iloc[1:]:
        variance = decay * variance + (1.0 - decay) * float(value) ** 2

    sigma = float(np.sqrt(max(variance, 0.0)))
    alpha = 1.0 - confidence_level
    z = NormalDist().inv_cdf(alpha)
    phi = np.exp(-0.5 * z**2) / np.sqrt(2 * np.pi)
    return TailRiskMeasure(
        model="ewma",
        confidence_level=confidence_level,
        var=float(-z * sigma),
        expected_shortfall=float(sigma * phi / alpha),
    )


def _ewma_conditional_volatility(values: np.ndarray, decay: float) -> np.ndarray:
    if len(values) < 2:
        raise ValueError("At least two observations are required.")
    variance = max(float(np.var(values[: min(20, len(values))], ddof=1)), 1e-12)
    volatility = np.empty(len(values), dtype=float)
    volatility[0] = np.sqrt(variance)
    for index in range(1, len(values)):
        variance = decay * variance + (1.0 - decay) * values[index - 1] ** 2
        volatility[index] = np.sqrt(max(variance, 1e-12))
    return volatility


def filtered_historical_var_es(
    returns: pd.Series,
    confidence_level: float,
    decay: float = 0.94,
) -> TailRiskMeasure:
    """EWMA-filtered historical simulation using rescaled empirical innovations."""
    clean = returns.dropna().astype(float)
    if len(clean) < 30:
        raise ValueError("Filtered historical simulation requires at least 30 observations.")
    if not 0.0 < decay < 1.0:
        raise ValueError("EWMA decay must be between 0 and 1.")

    values = clean.to_numpy()
    volatility = _ewma_conditional_volatility(values, decay)
    innovations = values / volatility
    next_variance = decay * volatility[-1] ** 2 + (1.0 - decay) * values[-1] ** 2
    scenarios = pd.Series(innovations * np.sqrt(next_variance))
    measure = historical_var_es(scenarios, confidence_level)
    return TailRiskMeasure(
        model="filtered_historical",
        confidence_level=confidence_level,
        var=measure.var,
        expected_shortfall=measure.expected_shortfall,
    )


def rolling_var_forecasts(
    returns: pd.Series,
    confidence_level: float,
    window: int,
    model: str,
    ewma_decay: float = 0.94,
) -> pd.DataFrame:
    clean = returns.dropna()
    if len(clean) <= window:
        raise ValueError("Not enough return observations for the requested rolling window.")

    rows = []
    for idx in range(window, len(clean)):
        history = clean.iloc[idx - window : idx]
        actual = float(clean.iloc[idx])
        if model == "historical":
            measure = historical_var_es(history, confidence_level)
        elif model == "parametric_normal":
            measure = parametric_var_es(history, confidence_level)
        elif model == "ewma":
            measure = ewma_var_es(history, confidence_level, ewma_decay)
        elif model == "filtered_historical":
            measure = filtered_historical_var_es(history, confidence_level, ewma_decay)
        else:
            raise ValueError(f"Unsupported VaR model: {model}")
        rows.append(
            {
                "date": clean.index[idx],
                "model": model,
                "var": measure.var,
                "expected_shortfall": measure.expected_shortfall,
                "actual_return": actual,
                "is_exception": actual < -measure.var,
            }
        )
    return pd.DataFrame(rows)


def component_var(
    asset_returns: pd.DataFrame,
    weights: dict[str, float],
    confidence_level: float,
    portfolio_value: float,
) -> pd.DataFrame:
    returns = asset_returns[list(weights)].dropna()
    covariance = returns.cov()
    weight_vector = pd.Series(weights, dtype=float).reindex(covariance.index)
    portfolio_sigma = float(np.sqrt(weight_vector.T @ covariance.values @ weight_vector))
    if portfolio_sigma <= 0:
        raise ValueError("Portfolio volatility is zero.")

    z_abs = abs(NormalDist().inv_cdf(1.0 - confidence_level))
    marginal = z_abs * (covariance.values @ weight_vector.values) / portfolio_sigma
    component = weight_vector.values * marginal
    total = float(component.sum())

    return pd.DataFrame(
        {
            "ticker": covariance.index,
            "weight": weight_vector.values,
            "component_var_return": component,
            "component_var_aud": component * portfolio_value,
            "pct_of_total": np.divide(component, total, out=np.zeros_like(component), where=total != 0),
        }
    ).sort_values("component_var_aud", ascending=False)
