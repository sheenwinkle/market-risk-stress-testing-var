# Model Methodology and Governance Note

## Purpose

This project demonstrates the daily analytics and control workflow around a stylised Australian treasury market-risk portfolio. It is designed for portfolio evidence in market risk, treasury risk, model risk, and risk analytics recruitment. It must not be represented as an APRA-compliant regulatory capital implementation.

APRA lists APS 116 Capital Adequacy: Market Risk as in force from 1 January 2025 and describes it as requiring authorised deposit-taking institutions to maintain adequate capital for market risk: [APRA banking prudential and reporting standards](https://www.apra.gov.au/banking/Prudential-and-reporting-standards). The implemented portfolio and controls are aligned to that professional context, but no claim of regulatory compliance is made.

## Measures

### Historical VaR and Expected Shortfall

Historical VaR is the empirical left-tail quantile of portfolio returns. Expected Shortfall is the mean loss conditional on crossing that quantile. The approach preserves observed non-normality but assumes the selected history is representative and gives equal weight to old and new observations.

### Parametric Normal VaR and Expected Shortfall

Parametric VaR and ES use sample mean and volatility with a normal distribution. This is transparent and fast, but it can understate skew, fat tails, volatility clustering, and nonlinear position behaviour.

### EWMA VaR and Expected Shortfall

The EWMA model recursively weights squared returns with lambda 0.94 by default. It responds more quickly to recent volatility and is useful as a challenger to equally weighted history. It still assumes conditional normality and a zero one-day conditional mean.

### Student-t GARCH challenger

The challenger estimates a constant-mean GARCH(1,1) process with standardized Student-t innovations on the first 500 observations. Estimated parameters are frozen, and conditional variance is then updated recursively using only information available before each holdout return. This prevents future parameter information leaking into the 802-day out-of-sample backtest.

Models are ranked on the common holdout using quantile loss, so different forecast start dates do not create an unfair comparison. Statistical test results remain separate from the loss ranking: a model can produce a low loss while still requiring review for coverage or clustered exceptions.

### Component VaR and factors

Component VaR uses covariance allocation and reconciles to total volatility VaR. OLS factor sensitivity estimates portfolio beta to the configured ASX 200, AUD/USD, and rates proxies. These are linear local approximations and should not be interpreted as trade-level Greeks.

## Validation controls

Every model is tested with rolling one-day-ahead forecasts. The pack reports:

- Exception count and rate.
- Kupiec unconditional coverage.
- Christoffersen exception independence.
- Combined conditional coverage.
- Latest 250-observation traffic-light status.

The Basel Framework uses 250 observations for 99% VaR backtesting and places 0-4 exceptions in green, 5-9 in amber, and 10 or more in red: [Basel MAR32 backtesting requirements](https://www.bis.org/basel_framework/chapter/MAR/32.htm). The project uses those thresholds as a management-model indicator. It does not calculate regulatory capital multipliers.

## Stress and reverse stress

Configured scenarios apply transparent position shocks and report both gross loss contributions and net P&L after offsets. Reverse stress scales each scenario to a configurable loss threshold. Linear scaling is appropriate for the current cash-instrument proxy book; nonlinear products would require full revaluation or delta-gamma approximations.

### FRTB-inspired Expected Shortfall

The pipeline also produces a 97.5% Expected Shortfall view using overlapping 10-day P&L returns. Positions are assigned to 10, 20, 40, 60, or 120-day liquidity horizons. Incremental horizon buckets are aggregated by the MAR33 square-root-of-sum-of-squares structure. A transparent stress scalar compares full-history ES with the worst contiguous 250-observation window.

The output includes a data-availability proxy showing trailing observations, represented months, and maximum gaps. It is deliberately labelled as a proxy rather than the regulatory risk-factor eligibility test because public closing prices do not prove real-price observations, committed quotes, or the other evidence an approved trading desk would require.

The Basel market-risk framework specifies 97.5% ES, a 10-day base horizon, prescribed liquidity horizons, stress calibration, and risk-factor modellability in the internal-models approach: [Basel Framework MAR33](https://www.bis.org/basel_framework/chapter/MAR/33.htm). This implementation is a governed management-risk demonstrator, not an FRTB capital number.

## AUD rates and FX valuation

The Treasury module discounts signed fixed-rate bond cash flows against the latest common-date RBA zero curve. Zero rates are linearly interpolated by maturity and applied with continuous compounding. Parallel one-basis-point revaluation produces DV01; symmetric up/down bumps produce convexity; individual pillar bumps produce key-rate DV01.

The AUD/USD forward is represented as receipt of a USD notional against a contracted AUD amount. Mark-to-market is the discounted difference between the current AUD value of the USD receipt and contracted AUD payment. This is a transparent educational valuation and omits cross-currency basis, collateral discounting, settlement conventions, and counterparty adjustments.

Curve scenarios use full cash-flow revaluation after parallel or tenor-shaped zero-rate shocks. This makes the scenario result sensitive to maturity and hedge positions rather than applying a fixed percentage directly to each instrument.

## Governance and reproducibility

Each run records SHA-256 hashes for the input price file and portfolio configuration, a deterministic run ID, source date range, dimensions, UTC generation time, and pipeline version. Data-quality, model-monitoring, limit, and efficiency tables are written to the same database as risk results.

Known limitations must be visible in any demonstration:

- Synthetic demo prices contain designed volatility clusters and are not evidence of real portfolio performance.
- Public end-of-day adjusted prices do not represent intraday trading P&L or instrument revaluation.
- Static weights omit trading, cash flows, corporate actions beyond adjusted-price handling, and FX translation of non-AUD holdings.
- Backtesting uses modelled portfolio returns rather than separate actual and hypothetical desk P&L.
- Risk limits are illustrative configuration, not an approved risk appetite statement.
