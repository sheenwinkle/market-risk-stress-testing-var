from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from arch import arch_model
from scipy.stats import t

from market_risk.risk_models import TailRiskMeasure


@dataclass(frozen=True)
class GarchParameters:
    mu: float
    omega: float
    alpha: float
    beta: float
    nu: float


def fit_garch_t(returns: pd.Series) -> GarchParameters:
    clean_pct = returns.dropna().astype(float) * 100.0
    if len(clean_pct) < 250:
        raise ValueError("GARCH-t requires at least 250 observations.")
    fitted = arch_model(
        clean_pct,
        mean="Constant",
        vol="GARCH",
        p=1,
        q=1,
        dist="StudentsT",
        rescale=False,
    ).fit(disp="off", show_warning=False)
    parameters = fitted.params
    return GarchParameters(
        mu=float(parameters["mu"]),
        omega=float(parameters["omega"]),
        alpha=float(parameters["alpha[1]"]),
        beta=float(parameters["beta[1]"]),
        nu=float(parameters["nu"]),
    )


def _standardized_t_tail(confidence_level: float, nu: float) -> tuple[float, float]:
    alpha = 1.0 - confidence_level
    raw_quantile = float(t.ppf(alpha, nu))
    scale = np.sqrt(nu / (nu - 2.0))
    quantile = raw_quantile / scale
    es = ((nu + raw_quantile**2) / (nu - 1.0)) * t.pdf(raw_quantile, nu) / alpha / scale
    return quantile, float(es)


def _recursive_variance(values_pct: np.ndarray, parameters: GarchParameters) -> np.ndarray:
    variances = np.empty(len(values_pct), dtype=float)
    unconditional = parameters.omega / max(1.0 - parameters.alpha - parameters.beta, 1e-6)
    variances[0] = max(unconditional, np.var(values_pct))
    for index in range(1, len(values_pct)):
        residual = values_pct[index - 1] - parameters.mu
        variances[index] = (
            parameters.omega
            + parameters.alpha * residual**2
            + parameters.beta * variances[index - 1]
        )
    return variances


def garch_t_var_es(returns: pd.Series, confidence_level: float) -> TailRiskMeasure:
    clean = returns.dropna().astype(float)
    parameters = fit_garch_t(clean)
    variances = _recursive_variance(clean.to_numpy() * 100.0, parameters)
    quantile, es_multiplier = _standardized_t_tail(confidence_level, parameters.nu)
    sigma = np.sqrt(variances[-1])
    var = -(parameters.mu + sigma * quantile) / 100.0
    expected_shortfall = (-parameters.mu + sigma * es_multiplier) / 100.0
    return TailRiskMeasure("garch_t", confidence_level, float(max(var, 0)), float(max(expected_shortfall, 0)))


def garch_t_forecasts(
    returns: pd.Series,
    confidence_level: float,
    training_observations: int = 500,
) -> pd.DataFrame:
    """Fit once on the training period, then recursively forecast an untouched holdout."""
    clean = returns.dropna().astype(float)
    if len(clean) <= training_observations:
        raise ValueError("Not enough observations for the GARCH training and holdout periods.")
    parameters = fit_garch_t(clean.iloc[:training_observations])
    values_pct = clean.to_numpy() * 100.0
    variances = _recursive_variance(values_pct, parameters)
    quantile, es_multiplier = _standardized_t_tail(confidence_level, parameters.nu)
    rows = []
    for index in range(training_observations, len(clean)):
        sigma = np.sqrt(variances[index])
        var = max(-(parameters.mu + sigma * quantile) / 100.0, 0.0)
        expected_shortfall = max((-parameters.mu + sigma * es_multiplier) / 100.0, 0.0)
        actual = float(clean.iloc[index])
        rows.append(
            {
                "date": clean.index[index],
                "model": "garch_t",
                "var": var,
                "expected_shortfall": expected_shortfall,
                "actual_return": actual,
                "is_exception": actual < -var,
            }
        )
    return pd.DataFrame(rows)


def model_performance_report(forecasts: pd.DataFrame, confidence_level: float) -> pd.DataFrame:
    alpha = 1.0 - confidence_level
    date_sets = [set(frame["date"]) for _, frame in forecasts.groupby("model")]
    common_dates = set.intersection(*date_sets)
    rows = []
    for model, frame in forecasts.groupby("model"):
        frame = frame[frame["date"].isin(common_dates)]
        quantile = -frame["var"]
        actual = frame["actual_return"]
        pinball = (alpha - (actual < quantile).astype(float)) * (actual - quantile)
        exception_losses = -actual[frame["is_exception"]]
        rows.append(
            {
                "model": model,
                "forecast_observations": len(frame),
                "mean_quantile_loss": float(pinball.mean()),
                "mean_var": float(frame["var"].mean()),
                "exception_count": int(frame["is_exception"].sum()),
                "mean_exception_loss": float(exception_losses.mean()) if len(exception_losses) else 0.0,
                "mean_expected_shortfall": float(frame["expected_shortfall"].mean()),
            }
        )
    result = pd.DataFrame(rows).sort_values("mean_quantile_loss")
    result["quantile_loss_rank"] = range(1, len(result) + 1)
    return result
