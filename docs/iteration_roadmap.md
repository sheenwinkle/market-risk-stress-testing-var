# Iteration Roadmap

This repository follows the same portfolio workflow used for the companion Risk
Analytics Portfolio:

1. Baseline the business gap before coding.
2. Add one role-relevant capability per iteration.
3. Quantify the effect with reproducible reports or tests.
4. Surface the result in README, case-study, dashboard, or SQL evidence.
5. Commit and push the iteration as a visible GitHub milestone.

The goal is not to look like a tutorial notebook. The goal is to look like a
controlled market-risk analytics asset that an Australian bank or FinTech team
could recognise: governed inputs, explainable models, challenge evidence,
limits, controls, repeatable reporting, and a clear audit trail.

## Depth And Breadth Scorecard

| Dimension | Current state | Target state | Gap |
|---|---|---|---|
| Market data breadth | Australian equities, listed bond proxy, FX proxy, RBA rates and FX, deterministic offline data | Public reproducibility plus documented source lineage for every risk factor | Medium |
| Tail risk models | Historical, Normal, EWMA, FHS, GARCH-t, ES diagnostics, FRTB-inspired ES | Add desk P&L attribution and eligibility-style evidence | Medium |
| Trading book coverage | Cash equities proxy, AUD rates/FX, equity options | Add desk-level actual/hypothetical/risk-theoretical P&L and NMRF demonstration | High |
| Model validation | Kupiec, Christoffersen, ES calibration, bootstrap uncertainty, challenger ranking | Add PLA-style diagnostics, exception explainability, and model-change evidence | Medium |
| Operations | One-command run, SQL snapshots, dashboard, management summary, run hashes | Add iteration-level release evidence and more decision-ready report tables | Low |
| Resume signal | Strong market risk, treasury risk, and model risk narrative | Make each iteration measurable and interview-ready | Medium |

## Iteration Rules

Every new iteration must leave evidence in at least four places:

- Code: a narrowly scoped module or extension.
- Tests: deterministic checks for the new calculation.
- Output: CSV/SQL/report rows that quantify the result.
- Documentation: README, case study, or methodology update with the business
  meaning and a resume-ready line.

Each iteration is committed and pushed separately so the GitHub history shows
progression from baseline analytics to deeper market-risk controls.

## Planned Iterations

| Iteration | Capability | Why it matters for jobs | Acceptance evidence |
|---|---|---|---|
| 1 | Workflow roadmap and scorecard | Shows the project is managed like a risk analytics portfolio, not a one-off script | This document plus README reference |
| 2 | Desk P&L attribution / PLA-style diagnostics | Connects VaR models to actual desk P&L and model validation conversations | Actual, hypothetical, risk-theoretical P&L tables; correlation/error tests; summary status |
| 3 | RFET / NMRF demonstration | Adds FRTB-style risk-factor evidence and explains data limitations transparently | Observation counts, gap days, eligibility flags, stress fallback |
| 4 | Scenario explainability pack | Makes stress and reverse-stress output interview-friendly for treasury risk | Top drivers, hedges, sensitivity bridge, SQL query |
| 5 | Scheduled control run pack | Makes operational efficiency measurable beyond local manual runs | Run log, exception queue, elapsed-time trend, control-owner summary |

## Current Priority

The next feature iteration is desk P&L attribution. It closes the biggest
remaining gap: the project has strong VaR, ES, stress, options, and treasury
analytics, but it does not yet prove whether modelled risk-theoretical P&L
explains actual or hypothetical desk P&L. That bridge is important for market
risk model validation, especially when discussing front-office versus risk
system reconciliation.
