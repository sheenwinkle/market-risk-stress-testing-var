from __future__ import annotations

import numpy as np
import pandas as pd

from market_risk.risk_models import historical_var_es


def es_calibration_backtest(
    forecasts: pd.DataFrame,
    confidence_level: float,
    bootstrap_samples: int = 2_000,
    seed: int = 42,
) -> pd.DataFrame:
    """Acerbi-Szekely Z2-style unconditional ES calibration with a bootstrap p-value."""
    if forecasts.empty:
        raise ValueError("Forecast dataframe is empty.")
    alpha = 1.0 - confidence_level
    rng = np.random.default_rng(seed)
    rows = []
    for model, frame in forecasts.groupby("model"):
        clean = frame.dropna(subset=["actual_return", "var", "expected_shortfall"])
        loss = -clean["actual_return"].to_numpy(dtype=float)
        var = clean["var"].to_numpy(dtype=float)
        es = clean["expected_shortfall"].to_numpy(dtype=float)
        exceptions = loss > var
        contributions = np.where(exceptions, loss / np.maximum(alpha * es, 1e-12), 0.0)
        z2_statistic = float(contributions.mean() - 1.0)

        null_contributions = contributions - contributions.mean() + 1.0
        bootstrap_means = np.empty(bootstrap_samples)
        for index in range(bootstrap_samples):
            sample = rng.choice(null_contributions, size=len(null_contributions), replace=True)
            bootstrap_means[index] = sample.mean() - 1.0
        p_value = float((1 + np.sum(bootstrap_means >= z2_statistic)) / (bootstrap_samples + 1))
        exception_losses = loss[exceptions]
        forecast_es_on_exceptions = es[exceptions]
        calibration_ratio = (
            float(exception_losses.sum() / forecast_es_on_exceptions.sum())
            if len(exception_losses)
            else 0.0
        )
        rows.append(
            {
                "model": model,
                "observations": len(clean),
                "exceptions": int(exceptions.sum()),
                "z2_statistic": z2_statistic,
                "underestimation_p_value": p_value,
                "realised_to_forecast_es_ratio": calibration_ratio,
                "es_calibration_status": "pass" if p_value >= 0.05 else "review",
                "bootstrap_samples": bootstrap_samples,
            }
        )
    return pd.DataFrame(rows).sort_values("z2_statistic", ascending=False)


def block_bootstrap_tail_uncertainty(
    returns: pd.Series,
    confidence_level: float,
    portfolio_value: float,
    bootstrap_samples: int = 500,
    block_length: int = 10,
    seed: int = 42,
) -> pd.DataFrame:
    """Moving-block bootstrap confidence intervals for historical VaR and ES."""
    clean = returns.dropna().astype(float).to_numpy()
    if len(clean) < block_length * 2:
        raise ValueError("Return history is too short for the requested block bootstrap.")
    rng = np.random.default_rng(seed)
    starts = np.arange(len(clean) - block_length + 1)
    estimates = np.empty((bootstrap_samples, 2), dtype=float)
    blocks_needed = int(np.ceil(len(clean) / block_length))
    for sample_index in range(bootstrap_samples):
        selected_starts = rng.choice(starts, size=blocks_needed, replace=True)
        sample = np.concatenate(
            [clean[start : start + block_length] for start in selected_starts]
        )[: len(clean)]
        measure = historical_var_es(pd.Series(sample), confidence_level)
        estimates[sample_index] = measure.var, measure.expected_shortfall

    point = historical_var_es(pd.Series(clean), confidence_level)
    rows = []
    for column, metric, estimate in [
        (0, "var", point.var),
        (1, "expected_shortfall", point.expected_shortfall),
    ]:
        lower, upper = np.quantile(estimates[:, column], [0.025, 0.975])
        rows.append(
            {
                "model": "historical",
                "metric": metric,
                "confidence_level": confidence_level,
                "point_estimate_aud": estimate * portfolio_value,
                "ci_95_lower_aud": lower * portfolio_value,
                "ci_95_upper_aud": upper * portfolio_value,
                "relative_interval_width": (upper - lower) / max(estimate, 1e-12),
                "bootstrap_samples": bootstrap_samples,
                "block_length_days": block_length,
            }
        )
    return pd.DataFrame(rows)
