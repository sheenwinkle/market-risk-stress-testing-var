# Case Study: Australian Treasury Market Risk Control Pack

## Decision question

Would a risk manager receive the same decision from a simple VaR model and a volatility-sensitive challenger, and how would the risk change after including an AUD rates and FX hedge book?

## Evidence base

- Deterministic listed-asset portfolio: 1,303 business-day observations and A$1 million market value.
- Official RBA data: 926 AUD exchange-rate observations and 2,426 zero-curve observations across nine maturities.
- Treasury book: three signed Australian Government bond positions and one AUD/USD forward.
- Validation: 802 common untouched holdout days for four-model comparison.

The listed-asset demo is synthetic so that every test is reproducible. The Treasury valuation uses the locally downloaded RBA F11.1 and F17 files, with 31 August 2026 as the latest common market date.

## Finding 1: challenger choice changes the limit decision

| Model | Current 99% VaR | Holdout quantile loss | Rank | Coverage | Independence |
|---|---:|---:|---:|---|---|
| GARCH-t | A$35,571 | 0.0003874 | 1 | Pass | Pass |
| Parametric Normal | A$31,611 | 0.0004188 | 2 | Fail | Fail |
| EWMA | A$33,119 | 0.0004253 | 3 | Fail | Pass |
| Historical | A$32,777 | 0.0004531 | 4 | Pass | Fail |

GARCH-t reduces common-holdout quantile loss by 14.5% relative to Historical VaR and is the only model that passes both coverage and independence checks. It also estimates A$35,571 VaR against the illustrative A$35,000 limit, creating a A$571 breach that the three simpler models do not identify.

The management response is not to accept GARCH automatically. The risk owner should investigate the breach, review the synthetic shock design, and assess whether the Student-t volatility response better represents the intended portfolio before changing limits or model status.

## Finding 2: maturity risk and hedge offsets are visible

The Treasury book has approximately A$2.54 million net market value and A$437 net DV01. The long 2028 and 2031 bonds contribute positive DV01, while the short 2035 bond removes approximately A$490 per basis point of long-end exposure.

Under a parallel 100bp increase, the two long bonds lose approximately A$91.0k while the 2035 hedge gains A$47.0k. Including the FX-forward and discounting effects produces a net loss of approximately A$43.7k. A bear-steepener combined with 3% AUD depreciation is close to neutral because the long-end bond hedge and USD receipt offset rates losses.

## Finding 3: automation preserves challenge, not just speed

One run produces 22 governed tables and more than 8,000 rows in under two seconds of core analytics on the development machine. Data source, pre-imputation missingness, fill counts, configuration hash, input hash, model status, breaches, and Treasury sensitivities are generated from the same run ID.

The configured 130-to-10 minute workflow comparison remains a business-case assumption. It is not treated as realised employer savings. The defensible technical performance claim is processing 50,000 eight-position scenarios with exact reconciliation to a transparent reference algorithm.

## Recommended action

1. Escalate the GARCH-t VaR limit breach for review rather than suppressing the challenger result.
2. Monitor net and key-rate DV01 because aggregate DV01 hides the 2031 long versus 2035 hedge profile.
3. Replace the synthetic listed-asset portfolio with approved desk positions and actual/hypothetical P&L before using the framework for production decisions.
4. Validate PostgreSQL history and concurrency in CI before treating the reporting store as production-ready.
