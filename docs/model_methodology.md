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

The Basel market-risk framework uses stressed Expected Shortfall and includes market illiquidity and risk-factor modellability in the internal-models approach: [BCBS minimum capital requirements for market risk](https://www.bis.org/publications/201901-standards-minimum-capital-requirements-market-risk). Those regulatory elements are deliberately outside this project's current scope.

## Governance and reproducibility

Each run records SHA-256 hashes for the input price file and portfolio configuration, a deterministic run ID, source date range, dimensions, UTC generation time, and pipeline version. Data-quality, model-monitoring, limit, and efficiency tables are written to the same database as risk results.

Known limitations must be visible in any demonstration:

- Synthetic demo prices contain designed volatility clusters and are not evidence of real portfolio performance.
- Public end-of-day adjusted prices do not represent intraday trading P&L or instrument revaluation.
- Static weights omit trading, cash flows, corporate actions beyond adjusted-price handling, and FX translation of non-AUD holdings.
- Backtesting uses modelled portfolio returns rather than separate actual and hypothetical desk P&L.
- Risk limits are illustrative configuration, not an approved risk appetite statement.
