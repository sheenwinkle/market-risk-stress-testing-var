# Case Study: Australian Treasury Market Risk Control Pack

## Decision question

How do model choice, market liquidity, and nonlinear hedges change the risk decision for an Australian financials and Treasury portfolio?

## Evidence base

- Listed-asset portfolio: 1,303 deterministic business-day observations and A$1 million market value.
- Public-data option: Yahoo Finance adjusted closes plus official RBA AUD exchange rates and zero curves.
- Treasury book: three signed Australian Government bond positions and one AUD/USD forward.
- Derivatives overlay: three CBA/Macquarie equity options with trade-level Greeks and full revaluation.
- Validation: five VaR/ES models, 802 common holdout days, ES calibration, and bootstrap uncertainty.
- Reporting: 31 CSV/SQL-ready tables and approximately 9,600 rows per governed run.

The deterministic market series keeps every result reproducible. Public downloads can replace it without changing the controlled pipeline.

## Finding 1: conditional models improve the decision

| Model | Current 99% VaR | Full rolling exceptions | Coverage | Independence | ES calibration |
|---|---:|---:|---|---|---|
| Filtered Historical | A$35,653 | 11 / 1,052 | Pass | Pass | Pass |
| GARCH-t | A$35,571 | 14 / 802 | Pass | Pass | Review |
| Historical | A$32,777 | 17 / 1,052 | Pass | Fail | Review |
| EWMA | A$33,119 | 19 / 1,052 | Fail | Pass | Review |
| Parametric Normal | A$31,611 | 19 / 1,052 | Fail | Fail | Review |

GARCH-t ranks first on common-holdout quantile loss, reducing loss by 14.5% relative to Historical VaR. FHS is the only model that also passes the Z2-style ES calibration diagnostic and produces an exception rate close to the expected 1%. Both conditional models breach the illustrative A$35,000 VaR limit, while the simpler models do not.

The action is model review and breach investigation, not automatic challenger approval. Ranking, VaR coverage, exception independence, and ES calibration remain separate decision criteria.

## Finding 2: longer liquidity horizons dominate one-day risk

The FRTB-inspired calculation produces A$273,262 of 97.5% liquidity-adjusted ES. The worst contiguous 250-observation period, February 2021 to February 2022, raises the stress scalar to 1.415 and the stress-scaled result to A$386,601.

The output reconciles each liquidity-horizon bucket and records a non-regulatory modellability proxy. This is useful management evidence, but public closing prices cannot establish the transaction and quote evidence required by the regulatory risk-factor eligibility test.

## Finding 3: full revaluation matters for nonlinear hedges

The option overlay has A$901 of 99% full-revaluation VaR and A$1,050 of ES over 500 historical shocks. In the equity-selloff/volatility-spike scenario, protective options gain A$8,394. Delta-gamma-vega estimates A$7,829, understating the hedge benefit by A$564, or 6.7%.

The explicit approximation error provides a controlled threshold for choosing full revaluation. The current use of realised volatility is reproducible but should be replaced by an approved implied-volatility surface for production valuation.

## Finding 4: estimation uncertainty is material

Historical VaR is A$32,777, while its moving-block bootstrap 95% interval is approximately A$28,756 to A$41,751. The interval spans both sides of the A$35,000 limit, showing that a point-estimate-only process can create false precision around escalation decisions.

## Efficiency and control outcome

The expanded run produces 31 tables and approximately 9,600 rows in under seven seconds of core analytics on the development machine. The vectorised scenario benchmark is more than 400 times faster than the reconciled row-loop reference. Database writes now use parameter-budgeted chunks, so adding another rolling model does not exceed SQLite's bind-variable limit.

The configured 130-to-10 minute workflow comparison implies a modelled 92.3% reduction in preparation time and 44 hours of monthly analyst capacity. These remain transparent planning assumptions, not realised employer savings. Accountable review, exception explanation, and escalation are retained as human controls.

## Recommended action

1. Escalate the FHS and GARCH-t VaR breaches and compare conditional-model assumptions before approval.
2. Monitor stress-scaled ES and liquidity buckets alongside one-day VaR.
3. Use full revaluation when nonlinear approximation error exceeds the desk tolerance.
4. Replace synthetic positions, realised option volatility, and modellability proxies with approved desk data before production use.
