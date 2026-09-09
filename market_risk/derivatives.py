from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml
from scipy.stats import norm

from market_risk.risk_models import historical_var_es


@dataclass(frozen=True)
class OptionAnalytics:
    price: float
    delta: float
    gamma: float
    vega: float
    theta: float


def black_scholes_option(
    spot: float,
    strike: float,
    maturity_years: float,
    risk_free_rate: float,
    volatility: float,
    option_type: str,
    dividend_yield: float = 0.0,
) -> OptionAnalytics:
    if min(spot, strike, maturity_years, volatility) <= 0:
        raise ValueError("Spot, strike, maturity, and volatility must be positive.")
    if option_type not in {"call", "put"}:
        raise ValueError(f"Unsupported option type: {option_type}")

    sqrt_t = np.sqrt(maturity_years)
    d1 = (
        np.log(spot / strike)
        + (risk_free_rate - dividend_yield + 0.5 * volatility**2) * maturity_years
    ) / (volatility * sqrt_t)
    d2 = d1 - volatility * sqrt_t
    discount_r = np.exp(-risk_free_rate * maturity_years)
    discount_q = np.exp(-dividend_yield * maturity_years)
    if option_type == "call":
        price = spot * discount_q * norm.cdf(d1) - strike * discount_r * norm.cdf(d2)
        delta = discount_q * norm.cdf(d1)
        theta = (
            -(spot * discount_q * norm.pdf(d1) * volatility) / (2 * sqrt_t)
            - risk_free_rate * strike * discount_r * norm.cdf(d2)
            + dividend_yield * spot * discount_q * norm.cdf(d1)
        )
    else:
        price = strike * discount_r * norm.cdf(-d2) - spot * discount_q * norm.cdf(-d1)
        delta = discount_q * (norm.cdf(d1) - 1)
        theta = (
            -(spot * discount_q * norm.pdf(d1) * volatility) / (2 * sqrt_t)
            + risk_free_rate * strike * discount_r * norm.cdf(-d2)
            - dividend_yield * spot * discount_q * norm.cdf(-d1)
        )
    gamma = discount_q * norm.pdf(d1) / (spot * volatility * sqrt_t)
    vega = spot * discount_q * norm.pdf(d1) * sqrt_t
    return OptionAnalytics(float(price), float(delta), float(gamma), float(vega), float(theta))


def _position_inputs(
    position: dict[str, Any],
    spot: float,
    volatility: float,
    risk_free_rate: float,
) -> tuple[OptionAnalytics, float, float]:
    strike = spot * float(position["strike_moneyness"])
    analytics = black_scholes_option(
        spot,
        strike,
        float(position["maturity_years"]),
        risk_free_rate,
        volatility,
        str(position["option_type"]),
        float(position.get("dividend_yield", 0.0)),
    )
    scale = float(position["quantity"]) * float(position.get("contract_multiplier", 1.0))
    return analytics, strike, scale


def _realised_volatility(returns: pd.Series, lookback: int) -> float:
    volatility = float(returns.dropna().tail(lookback).std(ddof=1) * np.sqrt(252))
    return max(volatility, 0.05)


def value_derivatives_book(
    book_path: str | Path,
    prices: pd.DataFrame,
    asset_returns: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    config = yaml.safe_load(Path(book_path).read_text(encoding="utf-8"))
    book = config["book"]
    risk_free_rate = float(book.get("risk_free_rate", 0.04))
    volatility_lookback = int(book.get("volatility_lookback_days", 60))
    positions = config["positions"]

    market = {
        ticker: {
            "spot": float(prices[ticker].dropna().iloc[-1]),
            "volatility": _realised_volatility(asset_returns[ticker], volatility_lookback),
        }
        for ticker in {str(position["underlying"]) for position in positions}
    }
    position_rows = []
    base_analytics: dict[str, tuple[OptionAnalytics, float, float]] = {}
    for position in positions:
        ticker = str(position["underlying"])
        spot = market[ticker]["spot"]
        volatility = market[ticker]["volatility"]
        analytics, strike, scale = _position_inputs(
            position, spot, volatility, risk_free_rate
        )
        base_analytics[str(position["trade_id"])] = (analytics, strike, scale)
        position_rows.append(
            {
                **position,
                "spot": spot,
                "strike": strike,
                "realised_volatility": volatility,
                "market_value_aud": analytics.price * scale,
                "delta_aud_per_1pct_spot": analytics.delta * scale * spot * 0.01,
                "gamma_aud_per_1pct_spot_squared": (
                    0.5 * analytics.gamma * scale * (spot * 0.01) ** 2
                ),
                "vega_aud_per_vol_point": analytics.vega * scale * 0.01,
                "theta_aud_per_day": analytics.theta * scale / 365.0,
                "volatility_source": f"{volatility_lookback}d_realised",
            }
        )

    scenario_rows = []
    for scenario_name, scenario in config.get("scenarios", {}).items():
        for position in positions:
            trade_id = str(position["trade_id"])
            ticker = str(position["underlying"])
            base, strike, scale = base_analytics[trade_id]
            spot_shock = float(scenario["spot_shocks"].get(ticker, 0.0))
            volatility_shock = float(scenario.get("volatility_shock", 0.0))
            spot = market[ticker]["spot"]
            volatility = market[ticker]["volatility"]
            stressed_spot = spot * (1.0 + spot_shock)
            stressed_volatility = max(volatility + volatility_shock, 0.01)
            stressed = black_scholes_option(
                stressed_spot,
                strike,
                float(position["maturity_years"]),
                risk_free_rate,
                stressed_volatility,
                str(position["option_type"]),
                float(position.get("dividend_yield", 0.0)),
            )
            spot_change = stressed_spot - spot
            approximation = scale * (
                base.delta * spot_change
                + 0.5 * base.gamma * spot_change**2
                + base.vega * volatility_shock
            )
            full_revaluation = (stressed.price - base.price) * scale
            scenario_rows.append(
                {
                    "scenario": scenario_name,
                    "description": scenario["description"],
                    "trade_id": trade_id,
                    "underlying": ticker,
                    "spot_shock_pct": spot_shock,
                    "volatility_shock_points": volatility_shock,
                    "full_revaluation_pnl_aud": full_revaluation,
                    "delta_gamma_vega_pnl_aud": approximation,
                    "approximation_error_aud": approximation - full_revaluation,
                }
            )

    historical_pnl = []
    aligned_returns = asset_returns[list(market)].dropna().tail(500)
    for date, return_row in aligned_returns.iterrows():
        pnl = 0.0
        for position in positions:
            trade_id = str(position["trade_id"])
            ticker = str(position["underlying"])
            base, strike, scale = base_analytics[trade_id]
            stressed = black_scholes_option(
                market[ticker]["spot"] * (1.0 + float(return_row[ticker])),
                strike,
                float(position["maturity_years"]),
                risk_free_rate,
                market[ticker]["volatility"],
                str(position["option_type"]),
                float(position.get("dividend_yield", 0.0)),
            )
            pnl += (stressed.price - base.price) * scale
        historical_pnl.append({"date": date, "full_revaluation_pnl_aud": pnl})
    pnl_frame = pd.DataFrame(historical_pnl)
    pnl_measure = historical_var_es(
        pnl_frame["full_revaluation_pnl_aud"], float(book.get("confidence_level", 0.99))
    )
    historical_summary = pd.DataFrame(
        [
            {
                "confidence_level": pnl_measure.confidence_level,
                "observations": len(pnl_frame),
                "full_revaluation_var_aud": pnl_measure.var,
                "full_revaluation_expected_shortfall_aud": pnl_measure.expected_shortfall,
                "net_option_market_value_aud": sum(
                    row["market_value_aud"] for row in position_rows
                ),
            }
        ]
    )
    return {
        "derivative_positions": pd.DataFrame(position_rows),
        "derivative_scenarios": pd.DataFrame(scenario_rows),
        "derivative_historical_pnl": pnl_frame,
        "derivative_historical_risk": historical_summary,
    }
