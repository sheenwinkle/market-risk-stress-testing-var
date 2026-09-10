# Australian Treasury Market Risk Control Centre

A production-shaped Python and SQL portfolio project for Australian bank, treasury risk, FinTech risk analytics, and model-risk roles. It turns market data into a governed daily risk pack: five VaR/ES models, FRTB-inspired ES, nonlinear derivatives revaluation, statistical backtesting, stress and reverse-stress analysis, position attribution, risk-limit monitoring, data-quality controls, PostgreSQL reporting, and an interactive dashboard.

This is an analytics demonstrator, not a regulatory capital calculator or investment product.

## Quantified outcome

The deterministic demo run gives every result below from one command, so the claims can be reproduced in an interview or CI job.

| Area | Demonstrated result |
|---|---:|
| Core analytics | Under 7 seconds on the development machine |
| Batch scenario valuation | 50,000 scenarios x 8 positions |
| Vectorisation benchmark | More than 400x faster than the transparent Python row-loop baseline on the development machine |
| Automated reporting | 31 CSV/SQL-ready tables and approximately 9,600 rows per run |
| Data controls | Raw completeness, freshness, source, validity, gaps, and imputation lineage |
| Model validation | 5 models, VaR coverage/independence plus ES calibration and uncertainty |
| Risk monitoring | 9 configurable VaR, ES, and stress-limit tests |

Measured timings are machine-dependent and are regenerated in `reports/performance_benchmark.csv`. Numerical reconciliation against the reference scenario algorithm is also recorded.

The workflow model in `configs/portfolio.yml` estimates 130 minutes for seven spreadsheet-style preparation activities and retains 10 minutes for analyst review. That implies a **modelled 92.3% preparation-time reduction** and **44 hours of monthly capacity** over 22 reporting days. These are transparent planning assumptions, not claimed production savings. See `docs/efficiency_methodology.md`.

## Where efficiency improves

The project targets the repeated preparation work around risk analysis, not the accountable risk decision:

1. Raw market data, pre-imputation quality checks, return construction, portfolio mapping, and fill lineage run as one controlled flow.
2. Five VaR/ES models, including FHS and GARCH-t, are calculated and backtested together instead of in separate spreadsheets.
3. Stress P&L, hedge offsets, position contributions, reverse-stress distance, and limits reconcile from the same configuration.
4. The same governed tables feed CSV, SQLite/PostgreSQL, SQL queries, the dashboard, and a management summary.
5. A run manifest hashes the input data and configuration, reducing time spent proving which inputs produced a report.
6. A trade-level AUD rates/FX book converts RBA zero curves into bond value, DV01, convexity, key-rate DV01, and full-revaluation scenario P&L.
7. A trade-level Australian equity-option overlay compares Greeks-based approximation with full revaluation and quantifies model error.

Human review, breach explanation, exception classification, and escalation remain deliberately outside automation.

## Demo results

For the included A$1 million synthetic Australian financials/treasury proxy book:

| Model | 99% one-day VaR | 99% one-day ES | Backtest exceptions | Latest 250-day zone |
|---|---:|---:|---:|---|
| Historical | A$32,777 | A$41,775 | 17 / 1,052 | Green |
| Parametric Normal | A$31,611 | A$36,111 | 19 / 1,052 | Green |
| EWMA (lambda 0.94) | A$33,119 | A$37,944 | 19 / 1,052 | Green |
| Filtered Historical | A$35,653 | A$42,924 | 11 / 1,052 | Green |
| GARCH-t challenger | A$35,571 | A$41,439 | 14 / 802 holdout days | Green |

The demo intentionally includes clustered shocks. Filtered Historical Simulation records 11 exceptions over 1,052 rolling forecasts and passes unconditional coverage, exception independence, combined coverage, and the Z2-style ES diagnostic. GARCH-t also passes VaR validation on its untouched holdout. The FHS current A$35,653 VaR creates a transparent A$653 limit breach for escalation.

Historical VaR is A$32,777, but a 500-sample moving-block bootstrap places its 95% interval at approximately A$28,756 to A$41,751. Reporting that interval makes sampling uncertainty visible instead of presenting a point estimate as certain.

The largest configured stress is `offshore_funding_freeze`, with a net loss of A$120,750 against a A$125,000 limit. Position-level P&L separates gross loss contributors from the positive bond-proxy offset, and reverse stress shows the shock multiplier required to reach a A$100,000 loss threshold.

The FRTB-inspired view reports A$273,262 of 97.5% liquidity-adjusted ES. The worst contiguous 250-observation calibration window runs from February 2021 to February 2022 and produces a 1.415 stress scalar, taking stress-scaled ES to A$386,601. These are method-demonstration outputs rather than regulatory capital figures.

The three-position options overlay has A$901 of 99% full-revaluation VaR and A$1,050 of ES over 500 historical shocks. In the equity-selloff/volatility-spike scenario it gains A$8,394, while delta-gamma-vega estimates A$7,829 and understates the hedge benefit by A$564. The explicit A$564 approximation error demonstrates when full revaluation matters.

## Architecture

```text
Yahoo Finance or deterministic demo prices
                   |
        quality checks + run hashes
                   |
          returns and portfolio P&L
                   |
     +-------------+--------------+
     |             |              |
 VaR / ES      stress engine   factor / component
 3 models      + reverse test      attribution
     |             |              |
 backtesting ---- risk limits -----+
                   |
       CSV + SQLite/PostgreSQL
                   |
      dashboard + management summary
```

## Risk methods and controls

- Historical VaR and tail-average Expected Shortfall.
- Parametric Normal VaR/ES using sample mean and volatility.
- RiskMetrics-style EWMA VaR/ES with configurable decay.
- Student-t GARCH(1,1) challenger calibrated on the training period and recursively forecast over an untouched holdout.
- EWMA-filtered historical simulation that rescales non-parametric innovations to the current volatility regime.
- Rolling one-day-ahead forecasts and exception capture.
- Kupiec unconditional coverage, Christoffersen independence, and combined conditional coverage tests.
- Z2-style ES calibration with deterministic bootstrap inference and moving-block VaR/ES confidence intervals.
- Basel-style 99% VaR traffic-light classification over the latest 250 observations.
- Configured Australian scenarios, historical 10-day stress windows, position P&L attribution, and reverse stress.
- Covariance component VaR and OLS factor sensitivities to ASX 200, AUD/USD, and an Australian rates proxy.
- Configurable risk appetite limits with utilisation, headroom, and breach status.
- Input/config SHA-256 hashes, run ID, data lineage dates, and pipeline version.
- Cash-flow valuation for AUD fixed-rate bonds, AUD/USD forward mark-to-market, parallel and shaped curve scenarios, DV01, convexity, and key-rate DV01.
- Black-Scholes equity-option valuation, signed delta/gamma/vega/theta, historical full-revaluation VaR/ES, and approximation-error analysis.
- FRTB-inspired 97.5% ES with 10-day returns, prescribed liquidity-horizon aggregation, stress-window scaling, and an explicitly non-regulatory modellability proxy.

The scope and regulatory limitations are documented in `docs/model_methodology.md`.

The quantified management narrative is available in `docs/case_study.md`.

## Portfolio and data

The default configuration uses listed Australian financial names and liquid proxies: `CBA.AX`, `NAB.AX`, `WBC.AX`, `ANZ.AX`, `MQG.AX`, `QBE.AX`, `SUN.AX`, and `IAF.AX`. Risk factors are `^AXJO`, `AUDUSD=X`, and `IAF.AX`. A separate options book adds CBA and Macquarie protective, covered-call, and tail-risk structures using reproducible realised-volatility inputs.

Three reproducible data sources are supported:

1. Public adjusted prices downloaded through `yfinance` from Yahoo Finance.
2. Deterministic synthetic prices generated locally when no price file exists.
3. Official RBA F11.1 AUD exchange rates and F17 zero-coupon yields, with URL, retrieval timestamp, date range, dimensions, and SHA-256 recorded in a data catalog.

Raw downloaded prices are excluded from Git because redistribution rights depend on the source. The offline data generator keeps tests and portfolio demonstrations reproducible.

## Quick start

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m market_risk.cli run
streamlit run dashboard/app.py
```

Use public market data instead:

```powershell
python -m market_risk.cli download
python -m market_risk.cli download-rba
python -m market_risk.cli run
```

## PostgreSQL

```powershell
docker compose up -d postgres
python -m market_risk.cli run --database-url postgresql+psycopg2://risk_user:risk_password@localhost:5432/market_risk
```

`sql/report_queries.sql` contains management queries for headline risk, exceptions, component VaR, stress losses, risk-limit utilisation, model monitoring, run history, and operational-efficiency evidence. Snapshot tables are append-only by deterministic `run_id`; a retry is idempotent while a changed input or configuration preserves a new historical run. SQLite is used by default for a zero-setup local run. See `docs/database_design.md`.

## Output pack

Each run produces 31 database-ready tables, including model risk, FRTB-inspired ES, stress, controls, rates/FX valuation, and `derivative_positions`, `derivative_scenarios`, `derivative_historical_pnl`, and `derivative_historical_risk`. It also writes `reports/management_summary.md` for a risk-manager view.

## Verification

```powershell
ruff check .
pytest
```

The suite currently reports 25 passing tests plus one environment-gated PostgreSQL integration test. It covers FRTB-style ES reconciliation, FHS regime response, ES calibration, bootstrap uncertainty, Black-Scholes parity and Greeks, option full revaluation, GARCH holdout forecasts, statistical backtesting, data lineage, Treasury valuation, snapshot idempotency, and the end-to-end SQL/reporting flow.

## Resume bullets

- Built an end-to-end Python/PostgreSQL market-risk control pipeline spanning an A$1m Australian financials proxy portfolio plus trade-level rates, FX, and equity-option books, producing 31 governed reporting tables.
- Implemented a governed FRTB-inspired 97.5% ES view across prescribed liquidity horizons; identified a 1.415 stress scalar and reconciled A$273k liquidity-adjusted to A$387k stress-scaled ES.
- Priced fixed-rate bond cash flows and an AUD/USD forward from official RBA market data; calculated DV01, convexity, key-rate DV01, hedge offsets, and full-revaluation curve scenario P&L.
- Built a three-trade Australian equity-options overlay with Black-Scholes Greeks and 500-shock full-revaluation VaR/ES; quantified A$564 delta-gamma-vega approximation error in an equity/volatility stress.
- Implemented five VaR/ES models including Filtered Historical Simulation and Student-t GARCH; FHS produced 11 exceptions across 1,052 forecasts and passed coverage, independence, and ES calibration diagnostics.
- Quantified estimation risk with moving-block bootstrap intervals, showing the A$32.8k historical VaR point estimate had an A$28.8k-A$41.8k 95% interval.
- Benchmarked a vectorised 50,000-scenario, eight-position stress engine at more than 400x the speed of a reconciled Python row-loop reference on the development machine; documented machine-dependent evidence and workflow assumptions separately.
- Automated position-level stress attribution, reverse-stress thresholds, configurable limit monitoring, SQL reporting, input lineage hashes, and a seven-view Streamlit risk dashboard.

## Limitations and next depth

- The listed instruments are portfolio proxies, not an ADI trading book with hypothetical and actual desk P&L.
- The FRTB-inspired layer implements 97.5% stressed and liquidity-adjusted ES, but not regulatory capital aggregation, the default risk charge, or desk approval tests.
- Workflow savings are a configurable business case and require validation against an employer's actual process before use as realised impact.
- The option layer uses trailing realised volatility rather than a licensed implied-volatility surface and omits American exercise, transaction costs, and independent price verification.
- Logical next extensions are desk P&L attribution, transaction-backed modellability evidence, scheduled orchestration, and role-based controls.
