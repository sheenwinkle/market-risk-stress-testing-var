from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter

import pandas as pd

from market_risk.backtesting import run_backtest
from market_risk.challenger import garch_t_forecasts, garch_t_var_es, model_performance_report
from market_risk.config import PortfolioConfig, load_config
from market_risk.controls import data_quality_report, model_monitoring_report, risk_limit_report
from market_risk.data import (
    impute_prices,
    load_data_metadata,
    load_prices,
    make_demo_prices,
    portfolio_returns,
    simple_returns,
)
from market_risk.database import persist_report_tables, sqlite_url
from market_risk.efficiency import (
    operational_efficiency_report,
    render_management_summary,
    scenario_performance_benchmark,
)
from market_risk.governance import build_run_manifest
from market_risk.risk_models import (
    component_var,
    ewma_var_es,
    historical_var_es,
    parametric_var_es,
    rolling_var_forecasts,
)
from market_risk.stress import (
    configured_stress_scenarios,
    factor_sensitivities,
    historical_stress_windows,
    reverse_stress_results,
    stress_position_contributions,
)
from market_risk.treasury import value_treasury_book


@dataclass(frozen=True)
class PipelineResult:
    report_dir: Path
    database_url: str
    risk_summary: pd.DataFrame
    backtests: pd.DataFrame
    stress_results: pd.DataFrame
    risk_limits: pd.DataFrame
    efficiency: pd.DataFrame


def _risk_summary(
    portfolio_returns_: pd.Series,
    config: PortfolioConfig,
) -> pd.DataFrame:
    as_of_date = portfolio_returns_.index.max().date()
    measures = [
        historical_var_es(portfolio_returns_, config.confidence_level),
        parametric_var_es(portfolio_returns_, config.confidence_level),
        ewma_var_es(portfolio_returns_, config.confidence_level, config.ewma_decay),
        garch_t_var_es(portfolio_returns_, config.confidence_level),
    ]
    rows = []
    for measure in measures:
        for metric, value in [
            ("var", measure.var),
            ("expected_shortfall", measure.expected_shortfall),
        ]:
            rows.append(
                {
                    "as_of_date": as_of_date,
                    "portfolio": config.name,
                    "model": measure.model,
                    "metric": metric,
                    "confidence_level": measure.confidence_level,
                    "value_as_return": value,
                    "value_aud": value * config.value_aud,
                }
            )
    return pd.DataFrame(rows)


def _write_reports(report_dir: Path, tables: dict[str, pd.DataFrame]) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    for table_name, frame in tables.items():
        frame.to_csv(report_dir / f"{table_name}.csv", index=False)


def run_pipeline(
    config_path: str | Path,
    prices_path: str | Path,
    report_dir: str | Path,
    database_url: str | None = None,
    treasury_book_path: str | Path = "configs/treasury_book.yml",
    rba_data_dir: str | Path = "data/raw/rba",
) -> PipelineResult:
    analytics_started = perf_counter()
    config = load_config(config_path)
    prices_path = Path(prices_path)
    if not prices_path.exists():
        make_demo_prices(config, prices_path)

    raw_prices = load_prices(prices_path)
    metadata = load_data_metadata(prices_path)
    source_type = str(metadata.get("source_type", "unknown"))
    run_manifest = build_run_manifest(config_path, prices_path, raw_prices, source_type)
    missing_assets = sorted(set(config.asset_tickers) - set(raw_prices.columns))
    if missing_assets:
        raise ValueError(f"Price file is missing configured assets: {missing_assets}")
    data_quality = data_quality_report(raw_prices, config.all_tickers, source_type)
    prices, imputation_audit = impute_prices(raw_prices)

    returns = simple_returns(prices)
    asset_returns = returns[config.asset_tickers].dropna()
    portfolio_return_series = portfolio_returns(asset_returns, config.weights)
    factor_returns = returns[[ticker for ticker in config.factor_tickers if ticker in returns.columns]]

    risk_summary = _risk_summary(portfolio_return_series, config)
    forecasts = pd.concat(
        [
            rolling_var_forecasts(
                portfolio_return_series,
                config.confidence_level,
                config.rolling_window_days,
                "historical",
            ),
            rolling_var_forecasts(
                portfolio_return_series,
                config.confidence_level,
                config.rolling_window_days,
                "parametric_normal",
            ),
            rolling_var_forecasts(
                portfolio_return_series,
                config.confidence_level,
                config.rolling_window_days,
                "ewma",
                config.ewma_decay,
            ),
            garch_t_forecasts(portfolio_return_series, config.confidence_level),
        ],
        ignore_index=True,
    )
    forecasts["var_aud"] = forecasts["var"] * config.value_aud
    forecasts["expected_shortfall_aud"] = forecasts["expected_shortfall"] * config.value_aud

    backtests = pd.DataFrame(
        [
            asdict(run_backtest(forecasts[forecasts["model"] == "historical"], config.confidence_level)),
            asdict(
                run_backtest(
                    forecasts[forecasts["model"] == "parametric_normal"],
                    config.confidence_level,
                )
            ),
            asdict(
                run_backtest(
                    forecasts[forecasts["model"] == "garch_t"],
                    config.confidence_level,
                )
            ),
            asdict(
                run_backtest(
                    forecasts[forecasts["model"] == "ewma"],
                    config.confidence_level,
                )
            ),
        ]
    )
    model_monitoring = model_monitoring_report(backtests)
    model_performance = model_performance_report(forecasts, config.confidence_level)
    stress_results = configured_stress_scenarios(config)
    stress_contributions = stress_position_contributions(config)
    reverse_stress = reverse_stress_results(config, stress_results)
    historical_stress = historical_stress_windows(portfolio_return_series, config.value_aud)
    sensitivities = factor_sensitivities(portfolio_return_series, factor_returns)
    cvar = component_var(asset_returns, config.weights, config.confidence_level, config.value_aud)
    limits = risk_limit_report(risk_summary, stress_results, config)
    benchmark = scenario_performance_benchmark(config)
    treasury_tables = value_treasury_book(treasury_book_path, rba_data_dir)

    report_dir = Path(report_dir)
    database_url = database_url or sqlite_url(report_dir / "risk_reports.db")
    base_tables = {
        "prices": prices.reset_index(names="date"),
        "asset_returns": asset_returns.reset_index(names="date"),
        "portfolio_returns": portfolio_return_series.reset_index(name="portfolio_return"),
        "risk_summary": risk_summary,
        "var_backtest": forecasts,
        "backtest_summary": backtests,
        "model_monitoring": model_monitoring,
        "model_performance": model_performance,
        "stress_results": stress_results,
        "stress_contributions": stress_contributions,
        "reverse_stress": reverse_stress,
        "historical_stress": historical_stress,
        "factor_sensitivities": sensitivities,
        "component_var": cvar,
        "data_quality": data_quality,
        "imputation_audit": imputation_audit,
        "risk_limits": limits,
        "performance_benchmark": benchmark,
        "run_manifest": run_manifest,
        **treasury_tables,
    }
    efficiency = operational_efficiency_report(
        config,
        perf_counter() - analytics_started,
        benchmark,
        base_tables,
    )
    tables = {**base_tables, "operational_efficiency": efficiency}
    _write_reports(report_dir, tables)
    persist_report_tables(database_url, tables)
    summary = render_management_summary(
        config,
        risk_summary,
        model_monitoring,
        limits,
        stress_results,
        efficiency,
    )
    (report_dir / "management_summary.md").write_text(summary, encoding="utf-8")

    return PipelineResult(
        report_dir=report_dir,
        database_url=database_url,
        risk_summary=risk_summary,
        backtests=backtests,
        stress_results=stress_results,
        risk_limits=limits,
        efficiency=efficiency,
    )
