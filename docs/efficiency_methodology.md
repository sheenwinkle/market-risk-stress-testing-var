# Efficiency Measurement Methodology

## Why measure efficiency

The value of a daily risk platform is not only whether it calculates VaR correctly. It should reduce repeated preparation, produce consistent controls, and preserve analyst time for reviewing exceptions and making escalation decisions.

This project reports two types of efficiency evidence and keeps them separate.

## Measured technical performance

`performance_benchmark.csv` compares the NumPy matrix scenario engine with a transparent Python row-loop reference over 50,000 scenarios and eight positions. Both implementations use identical shocks and weights. The report records median runtimes, speedup, and maximum absolute output difference.

`operational_efficiency.csv` also records core analytics time, output table count, and output row count. Results are machine-dependent and should be regenerated before quoting them.

This benchmark isolates scenario valuation. It does not claim the same speedup over a commercial risk platform or a well-optimised spreadsheet model.

## Modelled workflow capacity

The editable `workflow_assumptions` section in `configs/portfolio.yml` allocates minutes to seven manual activities:

| Activity | Assumed minutes |
|---|---:|
| Market data extract and clean | 20 |
| Position mapping and validation | 15 |
| VaR and ES calculation | 25 |
| Backtesting and exception review preparation | 20 |
| Stress testing and attribution | 20 |
| Limit monitoring and SQL pack | 15 |
| Management report refresh | 15 |
| **Total preparation** | **130** |

The automation still assigns 10 minutes to analyst review. At 22 reporting days per month:

```text
Preparation-time reduction = (130 - 10) / 130 = 92.3%
Monthly capacity released = (130 - 10) x 22 / 60 = 44.0 hours
```

These figures are a transparent business-case scenario. They are not realised savings from an employer. To use this method in a real team, time the current process over several month-end and normal reporting cycles, separate elapsed from active analyst time, include exception days, then replace the configuration assumptions with observed medians.

## Efficiency boundary

Automated work includes ingestion, checks, calculations, attribution, limit comparison, table persistence, dashboard refresh inputs, and summary preparation.

Retained human work includes source approval, exception cause classification, model override decisions, limit-breach approval, escalation, commentary, and sign-off. Removing those controls would not be an efficiency improvement.
