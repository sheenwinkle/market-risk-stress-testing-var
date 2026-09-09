import pandas as pd

from market_risk.treasury import (
    TreasuryMarket,
    bond_risk,
    bump_curve,
    price_fixed_rate_bond,
    price_fx_forward,
)


def _market() -> TreasuryMarket:
    return TreasuryMarket(
        pd.Timestamp("2026-01-01"),
        pd.Series({"AUD_ZC_0Y": 4.0, "AUD_ZC_1Y": 4.0, "AUD_ZC_5Y": 4.0, "AUD_ZC_10Y": 4.0}),
        0.65,
        "test",
    )


def test_bond_price_falls_when_curve_rises():
    position = {
        "face_value_aud": 1_000_000,
        "coupon_rate": 0.03,
        "maturity_date": "2031-01-01",
        "coupon_frequency": 2,
    }
    market = _market()
    higher_market = TreasuryMarket(
        market.as_of_date,
        bump_curve(market.zero_curve, 100),
        market.audusd,
        market.source_type,
    )

    assert price_fixed_rate_bond(position, higher_market) < price_fixed_rate_bond(position, market)
    assert bond_risk(position, market)["dv01_aud"] > 0


def test_fx_forward_gains_when_aud_weakens():
    position = {"receive_notional": 500_000, "contracted_audusd": 0.66, "maturity_years": 0.5}
    market = _market()
    weaker_aud = TreasuryMarket(market.as_of_date, market.zero_curve, 0.60, market.source_type)

    assert price_fx_forward(position, weaker_aud) > price_fx_forward(position, market)
