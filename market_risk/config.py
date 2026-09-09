from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class PortfolioConfig:
    name: str
    base_currency: str
    value_aud: float
    confidence_level: float
    rolling_window_days: int
    ewma_decay: float
    start_date: str
    end_date: str | None
    assets: dict[str, dict[str, Any]]
    risk_factors: dict[str, dict[str, Any]]
    stress_scenarios: dict[str, dict[str, Any]]
    risk_limits: dict[str, float]
    workflow_assumptions: dict[str, Any]
    frtb: dict[str, Any]

    @property
    def weights(self) -> dict[str, float]:
        return {ticker: float(meta["weight"]) for ticker, meta in self.assets.items()}

    @property
    def asset_tickers(self) -> list[str]:
        return list(self.assets)

    @property
    def factor_tickers(self) -> list[str]:
        return list(self.risk_factors)

    @property
    def all_tickers(self) -> list[str]:
        return sorted(set(self.asset_tickers) | set(self.factor_tickers))


def load_config(path: str | Path) -> PortfolioConfig:
    with Path(path).open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)

    weights = {ticker: float(meta["weight"]) for ticker, meta in raw["assets"].items()}
    total_weight = sum(weights.values())
    if abs(total_weight - 1.0) > 1e-8:
        raise ValueError(f"Portfolio weights must sum to 1.0; got {total_weight:.8f}")

    portfolio = raw["portfolio"]
    ewma_decay = float(portfolio.get("ewma_decay", 0.94))
    if not 0.0 < ewma_decay < 1.0:
        raise ValueError("EWMA decay must be between 0 and 1.")
    return PortfolioConfig(
        name=portfolio["name"],
        base_currency=portfolio["base_currency"],
        value_aud=float(portfolio["value_aud"]),
        confidence_level=float(portfolio["confidence_level"]),
        rolling_window_days=int(portfolio["rolling_window_days"]),
        ewma_decay=ewma_decay,
        start_date=str(portfolio["start_date"]),
        end_date=portfolio.get("end_date"),
        assets=raw["assets"],
        risk_factors=raw.get("risk_factors", {}),
        stress_scenarios=raw.get("stress_scenarios", {}),
        risk_limits={key: float(value) for key, value in raw.get("risk_limits", {}).items()},
        workflow_assumptions=raw.get("workflow_assumptions", {}),
        frtb=raw.get("frtb", {}),
    )
