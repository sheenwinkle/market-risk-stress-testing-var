from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml


@dataclass(frozen=True)
class TreasuryMarket:
    as_of_date: pd.Timestamp
    zero_curve: pd.Series
    audusd: float
    source_type: str


def tenor_from_column(column: str) -> float:
    return float(column.removeprefix("AUD_ZC_").removesuffix("Y").replace("P", "."))


def interpolate_zero_rate(curve: pd.Series, maturity_years: float) -> float:
    tenors = np.asarray([tenor_from_column(str(column)) for column in curve.index])
    rates = curve.astype(float).to_numpy() / 100.0
    order = np.argsort(tenors)
    return float(np.interp(maturity_years, tenors[order], rates[order]))


def bond_cashflows(
    face_value: float,
    coupon_rate: float,
    maturity_years: float,
    frequency: int,
) -> tuple[np.ndarray, np.ndarray]:
    periods = max(int(np.ceil(maturity_years * frequency)), 1)
    times = maturity_years - np.arange(periods - 1, -1, -1) / frequency
    times = times[times > 0]
    cashflows = np.full(len(times), abs(face_value) * coupon_rate / frequency)
    cashflows[-1] += abs(face_value)
    return times, cashflows * np.sign(face_value)


def price_fixed_rate_bond(position: dict[str, Any], market: TreasuryMarket) -> float:
    maturity = pd.Timestamp(position["maturity_date"])
    years = max((maturity - market.as_of_date).days / 365.25, 1 / 365.25)
    times, cashflows = bond_cashflows(
        float(position["face_value_aud"]),
        float(position["coupon_rate"]),
        years,
        int(position.get("coupon_frequency", 2)),
    )
    rates = np.asarray([interpolate_zero_rate(market.zero_curve, time) for time in times])
    return float(np.sum(cashflows * np.exp(-rates * times)))


def bump_curve(curve: pd.Series, bumps_bp: float | pd.Series) -> pd.Series:
    if np.isscalar(bumps_bp):
        return curve.astype(float) + float(bumps_bp) / 100.0
    return curve.astype(float) + bumps_bp.reindex(curve.index).fillna(0.0) / 100.0


def bond_risk(position: dict[str, Any], market: TreasuryMarket) -> dict[str, float]:
    base = price_fixed_rate_bond(position, market)
    up_market = TreasuryMarket(
        market.as_of_date,
        bump_curve(market.zero_curve, 1.0),
        market.audusd,
        market.source_type,
    )
    down_market = TreasuryMarket(
        market.as_of_date,
        bump_curve(market.zero_curve, -1.0),
        market.audusd,
        market.source_type,
    )
    up = price_fixed_rate_bond(position, up_market)
    down = price_fixed_rate_bond(position, down_market)
    dv01 = (down - up) / 2.0
    convexity = (down + up - 2 * base) / (base * 0.0001**2) if base else 0.0
    modified_duration = dv01 / (base * 0.0001) if base else 0.0
    return {
        "market_value_aud": base,
        "dv01_aud": dv01,
        "modified_duration": modified_duration,
        "convexity": convexity,
    }


def price_fx_forward(position: dict[str, Any], market: TreasuryMarket) -> float:
    notional_usd = float(position["receive_notional"])
    contracted = float(position["contracted_audusd"])
    maturity = float(position.get("maturity_years", 0.5))
    aud_rate = interpolate_zero_rate(market.zero_curve, maturity)
    undiscounted_aud = notional_usd * (1.0 / market.audusd - 1.0 / contracted)
    return float(undiscounted_aud * np.exp(-aud_rate * maturity))


def _demo_market() -> TreasuryMarket:
    curve = pd.Series(
        {
            "AUD_ZC_0Y": 3.85,
            "AUD_ZC_0P25Y": 3.78,
            "AUD_ZC_0P5Y": 3.72,
            "AUD_ZC_1Y": 3.68,
            "AUD_ZC_2Y": 3.74,
            "AUD_ZC_3Y": 3.82,
            "AUD_ZC_5Y": 4.02,
            "AUD_ZC_7Y": 4.18,
            "AUD_ZC_10Y": 4.32,
        }
    )
    return TreasuryMarket(pd.Timestamp("2025-12-31"), curve, 0.65, "synthetic_curve")


def load_treasury_market(rba_data_dir: str | Path) -> TreasuryMarket:
    directory = Path(rba_data_dir)
    curve_path = directory / "aud_zero_curve.csv"
    fx_path = directory / "aud_exchange_rates.csv"
    if not curve_path.exists() or not fx_path.exists():
        return _demo_market()
    curve = pd.read_csv(curve_path, parse_dates=["date"]).set_index("date").sort_index()
    fx = pd.read_csv(fx_path, parse_dates=["date"]).set_index("date").sort_index()
    common_as_of = min(curve.index.max(), fx.index.max())
    curve_row = curve.loc[:common_as_of].ffill().iloc[-1]
    audusd = float(fx.loc[:common_as_of, "AUDUSD"].ffill().iloc[-1])
    return TreasuryMarket(common_as_of, curve_row, audusd, "rba_official")


def load_treasury_book(path: str | Path) -> dict[str, Any]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def _scenario_curve(curve: pd.Series, short_bp: float, long_bp: float) -> pd.Series:
    tenors = pd.Series({column: tenor_from_column(str(column)) for column in curve.index})
    scaled = short_bp + (long_bp - short_bp) * tenors.clip(0, 10) / 10.0
    return bump_curve(curve, scaled)


def value_treasury_book(
    book_path: str | Path,
    rba_data_dir: str | Path,
) -> dict[str, pd.DataFrame]:
    config = load_treasury_book(book_path)
    market = load_treasury_market(rba_data_dir)
    positions = config["positions"]
    position_rows = []
    key_rate_rows = []

    for position in positions:
        if position["instrument_type"] == "fixed_rate_bond":
            risk = bond_risk(position, market)
            position_rows.append({**position, **risk, "as_of_date": market.as_of_date.date(), "market_source": market.source_type})
            base = risk["market_value_aud"]
            for pillar in market.zero_curve.index:
                bumps = pd.Series(0.0, index=market.zero_curve.index)
                bumps[pillar] = 1.0
                bumped_market = TreasuryMarket(
                    market.as_of_date,
                    bump_curve(market.zero_curve, bumps),
                    market.audusd,
                    market.source_type,
                )
                key_rate_rows.append(
                    {
                        "trade_id": position["trade_id"],
                        "curve_pillar": pillar,
                        "key_rate_dv01_aud": base - price_fixed_rate_bond(position, bumped_market),
                    }
                )
        elif position["instrument_type"] == "fx_forward":
            position_rows.append(
                {
                    **position,
                    "market_value_aud": price_fx_forward(position, market),
                    "dv01_aud": 0.0,
                    "modified_duration": 0.0,
                    "convexity": 0.0,
                    "as_of_date": market.as_of_date.date(),
                    "market_source": market.source_type,
                }
            )

    base_values = {row["trade_id"]: row["market_value_aud"] for row in position_rows}
    scenario_rows = []
    for scenario, details in config.get("curve_scenarios", {}).items():
        stressed_market = TreasuryMarket(
            market.as_of_date,
            _scenario_curve(
                market.zero_curve,
                float(details["short_end_bp"]),
                float(details["long_end_bp"]),
            ),
            market.audusd * (1.0 + float(details.get("fx_spot_shock_pct", 0.0))),
            market.source_type,
        )
        for position in positions:
            stressed_value = (
                price_fixed_rate_bond(position, stressed_market)
                if position["instrument_type"] == "fixed_rate_bond"
                else price_fx_forward(position, stressed_market)
            )
            scenario_rows.append(
                {
                    "scenario": scenario,
                    "description": details["description"],
                    "trade_id": position["trade_id"],
                    "base_value_aud": base_values[position["trade_id"]],
                    "stressed_value_aud": stressed_value,
                    "pnl_aud": stressed_value - base_values[position["trade_id"]],
                }
            )

    return {
        "treasury_positions": pd.DataFrame(position_rows),
        "key_rate_dv01": pd.DataFrame(key_rate_rows),
        "treasury_scenarios": pd.DataFrame(scenario_rows),
    }
