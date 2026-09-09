from __future__ import annotations

import argparse
from pathlib import Path

from market_risk.config import load_config
from market_risk.data import download_adjusted_close, make_demo_prices
from market_risk.pipeline import run_pipeline
from market_risk.rba_data import download_rba_market_data

DEFAULT_CONFIG = Path("configs/portfolio.yml")
DEFAULT_PRICES = Path("data/raw/prices.csv")
DEFAULT_REPORTS = Path("reports")


def _download(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    prices = download_adjusted_close(
        tickers=config.all_tickers,
        start_date=config.start_date,
        end_date=config.end_date,
        output_path=args.output,
    )
    print(f"Downloaded {len(prices):,} rows to {args.output}")


def _demo_data(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    prices = make_demo_prices(config, args.output)
    print(f"Created deterministic demo prices with {len(prices):,} rows at {args.output}")


def _run(args: argparse.Namespace) -> None:
    result = run_pipeline(
        config_path=args.config,
        prices_path=args.prices,
        report_dir=args.reports,
        database_url=args.database_url,
    )
    print(f"Reports written to {result.report_dir}")
    print(f"Database written to {result.database_url}")
    print(result.risk_summary.to_string(index=False))
    print(result.backtests.to_string(index=False))
    print("\nRisk limits:")
    print(result.risk_limits.to_string(index=False))
    print("\nOperating efficiency:")
    print(result.efficiency.to_string(index=False))
    print(f"\nManagement summary: {result.report_dir / 'management_summary.md'}")


def _download_rba(args: argparse.Namespace) -> None:
    catalog = download_rba_market_data(args.output_dir)
    print(catalog.to_string(index=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="market-risk",
        description="Australian market risk VaR, stress testing, backtesting, and SQL reporting.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    download = subparsers.add_parser("download", help="Download public market prices via yfinance.")
    download.add_argument("--config", default=DEFAULT_CONFIG)
    download.add_argument("--output", default=DEFAULT_PRICES)
    download.set_defaults(func=_download)

    demo = subparsers.add_parser("demo-data", help="Create deterministic offline demo prices.")
    demo.add_argument("--config", default=DEFAULT_CONFIG)
    demo.add_argument("--output", default=DEFAULT_PRICES)
    demo.set_defaults(func=_demo_data)

    rba = subparsers.add_parser("download-rba", help="Download official RBA FX and AUD zero-curve data.")
    rba.add_argument("--output-dir", default=Path("data/raw/rba"))
    rba.set_defaults(func=_download_rba)

    run = subparsers.add_parser("run", help="Run the full VaR/stress/backtesting/reporting pipeline.")
    run.add_argument("--config", default=DEFAULT_CONFIG)
    run.add_argument("--prices", default=DEFAULT_PRICES)
    run.add_argument("--reports", default=DEFAULT_REPORTS)
    run.add_argument(
        "--database-url",
        default=None,
        help="Optional SQLAlchemy URL, e.g. postgresql+psycopg2://risk_user:risk_password@localhost:5432/market_risk",
    )
    run.set_defaults(func=_run)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
