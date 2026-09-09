from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from market_risk.config import PortfolioConfig


def download_adjusted_close(
    tickers: list[str],
    start_date: str,
    end_date: str | None,
    output_path: str | Path,
) -> pd.DataFrame:
    """Download adjusted close prices from Yahoo Finance via yfinance."""
    try:
        import yfinance as yf
    except ImportError as exc:
        raise RuntimeError("Install yfinance or run the offline demo data generator.") from exc

    prices = yf.download(
        tickers=tickers,
        start=start_date,
        end=end_date,
        auto_adjust=True,
        progress=False,
        group_by="column",
        threads=True,
    )

    if isinstance(prices.columns, pd.MultiIndex):
        if "Close" in prices.columns.get_level_values(0):
            close = prices["Close"]
        elif "Adj Close" in prices.columns.get_level_values(0):
            close = prices["Adj Close"]
        else:
            raise ValueError("Downloaded data did not include close prices.")
    else:
        close = prices.to_frame(name=tickers[0]) if len(tickers) == 1 else prices

    close = close.dropna(how="all").ffill().dropna(axis=1, how="all")
    if close.empty:
        raise ValueError("No price data was downloaded.")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    close.to_csv(output_path, index_label="date")
    write_data_metadata(output_path, "yahoo_finance", tickers)
    return close


def make_demo_prices(config: PortfolioConfig, output_path: str | Path, seed: int = 42) -> pd.DataFrame:
    """Create deterministic demo prices so the project runs without network access."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2021-01-04", "2025-12-31")
    tickers = config.all_tickers

    market = rng.normal(0.00022, 0.0105, len(dates))
    rates = rng.normal(0.00005, 0.0035, len(dates))
    fx = rng.normal(-0.00001, 0.0065, len(dates))
    shock = np.zeros(len(dates))
    shock_windows = [(270, 282, -0.035), (720, 725, -0.028), (1035, 1042, -0.032)]
    for start, end, daily_shock in shock_windows:
        shock[start:end] = daily_shock

    returns: dict[str, np.ndarray] = {}
    for ticker in tickers:
        if ticker == "AUDUSD=X":
            ret = 0.25 * market + fx + rng.normal(0, 0.003, len(dates))
        elif ticker == "^AXJO":
            ret = market + shock * 0.65
        elif ticker == "IAF.AX":
            ret = rates - 0.22 * market - shock * 0.15 + rng.normal(0, 0.002, len(dates))
        else:
            beta = 1.05 + 0.35 * rng.random()
            idio_vol = 0.006 + 0.005 * rng.random()
            ret = beta * market + shock + rng.normal(0, idio_vol, len(dates))
        returns[ticker] = ret

    price_frame = pd.DataFrame(index=dates)
    for ticker, ret in returns.items():
        start_price = 50 + 70 * rng.random()
        price_frame[ticker] = start_price * np.exp(np.cumsum(ret))

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    price_frame.to_csv(output_path, index_label="date")
    write_data_metadata(output_path, "synthetic_demo", tickers)
    return price_frame


def load_prices(path: str | Path) -> pd.DataFrame:
    prices = pd.read_csv(path, parse_dates=["date"]).set_index("date").sort_index()
    return prices.dropna(how="all")


def impute_prices(prices: pd.DataFrame, limit: int = 3) -> tuple[pd.DataFrame, pd.DataFrame]:
    missing_before = prices.isna()
    cleaned = prices.ffill(limit=limit)
    imputed = missing_before & cleaned.notna()
    audit = pd.DataFrame(
        {
            "ticker": prices.columns,
            "raw_missing_count": missing_before.sum().values,
            "imputed_count": imputed.sum().values,
            "remaining_missing_count": cleaned.isna().sum().values,
            "imputation_rate": imputed.sum().values / max(len(prices), 1),
            "method": f"forward_fill_limit_{limit}",
        }
    )
    return cleaned, audit


def metadata_path(data_path: str | Path) -> Path:
    path = Path(data_path)
    return path.with_suffix(path.suffix + ".metadata.json")


def write_data_metadata(path: str | Path, source_type: str, series: list[str]) -> None:
    payload = {
        "source_type": source_type,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "series": series,
    }
    metadata_path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_data_metadata(path: str | Path) -> dict[str, object]:
    sidecar = metadata_path(path)
    if not sidecar.exists():
        return {"source_type": "unknown", "retrieved_at_utc": None, "series": []}
    return json.loads(sidecar.read_text(encoding="utf-8"))


def simple_returns(prices: pd.DataFrame) -> pd.DataFrame:
    returns = prices.pct_change(fill_method=None)
    return returns.replace([np.inf, -np.inf], np.nan).dropna(how="all")


def portfolio_returns(asset_returns: pd.DataFrame, weights: dict[str, float]) -> pd.Series:
    missing = sorted(set(weights) - set(asset_returns.columns))
    if missing:
        raise ValueError(f"Missing asset return columns: {missing}")
    weight_vector = pd.Series(weights).reindex(asset_returns.columns).fillna(0.0)
    return asset_returns.mul(weight_vector, axis=1).sum(axis=1).rename("portfolio_return")
