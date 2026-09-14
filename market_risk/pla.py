from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp, pearsonr, spearmanr


@dataclass(frozen=True)
class PnlAttributionResult:
    daily: pd.DataFrame
    summary: pd.DataFrame
    factor_betas: pd.DataFrame


def _ols_predictions(y: pd.Series, x: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    aligned = pd.concat([y.rename("target"), x], axis=1).dropna()
    if len(aligned) < max(30, x.shape[1] + 5):
        raise ValueError("Not enough overlapping observations for P&L attribution.")
    design = np.column_stack([np.ones(len(aligned)), aligned[x.columns].to_numpy(dtype=float)])
    coefficients, *_ = np.linalg.lstsq(design, aligned["target"].to_numpy(dtype=float), rcond=None)
    fitted = design @ coefficients
    beta = pd.Series(coefficients[1:], index=x.columns, name=y.name)
    return pd.Series(fitted, index=aligned.index, name=y.name), beta


def _deterministic_actual_adjustment(hypothetical_pnl: pd.Series, residual_pnl: pd.Series) -> pd.Series:
    rolling_vol = hypothetical_pnl.rolling(20, min_periods=5).std().fillna(0.0)
    funding_carry = 0.015 * rolling_vol * np.sin(np.linspace(0, 4 * np.pi, len(hypothetical_pnl)))
    residual_leakage = 0.08 * residual_pnl.rolling(5, min_periods=1).mean()
    return pd.Series(
        funding_carry + residual_leakage,
        index=hypothetical_pnl.index,
        name="desk_adjustment_aud",
    )


def _pair_metrics(reference: pd.Series, challenger: pd.Series, pair_name: str) -> dict[str, object]:
    aligned = pd.concat([reference.rename("reference"), challenger.rename("challenger")], axis=1).dropna()
    if len(aligned) < 30:
        raise ValueError(f"Not enough observations for {pair_name} PLA diagnostics.")
    error = aligned["reference"] - aligned["challenger"]
    average_abs_reference = float(aligned["reference"].abs().mean())
    pearson = float(pearsonr(aligned["reference"], aligned["challenger"]).statistic)
    spearman = float(spearmanr(aligned["reference"], aligned["challenger"]).statistic)
    ks_result = ks_2samp(aligned["reference"], aligned["challenger"])
    left_tail_reference = aligned["reference"].nsmallest(max(int(len(aligned) * 0.05), 1)).mean()
    left_tail_challenger = aligned["challenger"].nsmallest(max(int(len(aligned) * 0.05), 1)).mean()
    mean_abs_error_ratio = float(error.abs().mean() / max(average_abs_reference, 1e-12))
    variance_ratio = float(
        aligned["challenger"].var(ddof=1) / max(aligned["reference"].var(ddof=1), 1e-12)
    )
    tail_capture_ratio = float(
        left_tail_challenger / left_tail_reference if abs(left_tail_reference) > 1e-12 else np.nan
    )

    if spearman >= 0.9 and ks_result.statistic <= 0.12 and mean_abs_error_ratio <= 0.25:
        status = "pass"
    elif spearman >= 0.8 and ks_result.statistic <= 0.2 and mean_abs_error_ratio <= 0.45:
        status = "watch"
    else:
        status = "review"

    return {
        "comparison": pair_name,
        "observations": len(aligned),
        "pearson_correlation": pearson,
        "spearman_correlation": spearman,
        "ks_statistic": float(ks_result.statistic),
        "ks_p_value": float(ks_result.pvalue),
        "mean_abs_error_aud": float(error.abs().mean()),
        "p95_abs_error_aud": float(error.abs().quantile(0.95)),
        "mean_abs_error_pct_of_avg_abs_pnl": mean_abs_error_ratio,
        "variance_ratio": variance_ratio,
        "left_tail_capture_ratio": tail_capture_ratio,
        "pla_status": status,
    }


def pnl_attribution_report(
    asset_returns: pd.DataFrame,
    factor_returns: pd.DataFrame,
    weights: dict[str, float],
    portfolio_value_aud: float,
) -> PnlAttributionResult:
    """Build desk-level actual, hypothetical, and risk-theoretical P&L diagnostics.

    Actual P&L is a deterministic demonstrator: hypothetical P&L plus a small
    desk adjustment derived from model residuals and rolling volatility. In a
    production desk, this input would come from the official front-office P&L.
    """
    ordered_assets = list(weights)
    returns = asset_returns[ordered_assets].dropna()
    factors = factor_returns.dropna()
    common_index = returns.index.intersection(factors.index)
    returns = returns.loc[common_index]
    factors = factors.loc[common_index]
    if returns.empty or factors.empty:
        raise ValueError("Asset returns and factor returns must overlap for PLA.")

    predicted_returns = pd.DataFrame(index=returns.index)
    beta_rows = []
    for ticker in ordered_assets:
        fitted, beta = _ols_predictions(returns[ticker].rename(ticker), factors)
        predicted_returns[ticker] = fitted.reindex(returns.index)
        for factor_name, value in beta.items():
            beta_rows.append(
                {
                    "ticker": ticker,
                    "factor": factor_name,
                    "beta": float(value),
                    "weight": float(weights[ticker]),
                }
            )

    weight_vector = pd.Series(weights, dtype=float).reindex(ordered_assets)
    hypothetical = (returns[ordered_assets] @ weight_vector) * portfolio_value_aud
    risk_theoretical = (predicted_returns[ordered_assets] @ weight_vector) * portfolio_value_aud
    residual = hypothetical - risk_theoretical
    adjustment = _deterministic_actual_adjustment(hypothetical, residual)
    actual = hypothetical + adjustment

    daily = pd.DataFrame(
        {
            "date": returns.index,
            "actual_pnl_aud": actual.values,
            "hypothetical_pnl_aud": hypothetical.values,
            "risk_theoretical_pnl_aud": risk_theoretical.values,
            "desk_adjustment_aud": adjustment.values,
            "actual_minus_hypothetical_aud": (actual - hypothetical).values,
            "hypothetical_minus_risk_theoretical_aud": residual.values,
        }
    )
    summary = pd.DataFrame(
        [
            _pair_metrics(actual, hypothetical, "actual_vs_hypothetical"),
            _pair_metrics(hypothetical, risk_theoretical, "hypothetical_vs_risk_theoretical"),
        ]
    )
    factor_betas = pd.DataFrame(beta_rows).sort_values(["ticker", "factor"]).reset_index(drop=True)
    return PnlAttributionResult(
        daily=daily.reset_index(drop=True),
        summary=summary,
        factor_betas=factor_betas,
    )
