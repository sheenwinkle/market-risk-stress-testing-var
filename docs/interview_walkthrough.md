# Interview Walkthrough

This document is the interview-facing guide for the project. It explains how to
pitch the work, what to show live on GitHub, which claims are safe to make, and
how to defend the project when challenged.

## 30-second pitch

I built a Python and SQL market-risk control centre for an Australian
bank-style treasury portfolio. It turns reproducible market data into a daily
risk pack covering VaR, Expected Shortfall, stress testing, FRTB-inspired
liquidity-horizon ES, nonlinear option full revaluation, PLA-style desk P&L
attribution, RFET/NMRF evidence, PostgreSQL reporting, and a Streamlit
dashboard. The latest deterministic run produces 37 governed reporting tables,
10,952 rows, 28 passing tests, and a management summary in under seven seconds
of core analytics on my development machine. The value is not just a model; it
is a controlled workflow that makes model validation, stress explanation, data
lineage, and efficiency evidence reproducible.

## APRA-aware framing

This is the safest way to describe the prudential angle:

> I used APRA standards as a framing discipline, not as a compliance claim. The
> project maps outputs to prudential themes such as APS 116, CPS 220, CPS 230,
> CPS 234, and RFET/NMRF evidence, then states the exact boundary of each claim.
> That makes the project more credible for risk analytics interviews because it
> shows I understand both the analytics and the evidence a regulated institution
> would still need.

Show `docs/apra_boundary_framework.md` and `reports/prudential_evidence_map.csv`
when the interviewer asks whether the project is meant to be production-grade.

## GitHub live demo path

Use this order in a live screen share:

1. Open `README.md`.
   Start with the quantified outcome table and the resume bullets. This gives
   the interviewer the business frame before the code.
2. Open `docs/case_study.md`.
   Walk through the six findings: conditional models, liquidity-horizon ES,
   nonlinear hedges, estimation uncertainty, PLA residual P&L, and RFET limits.
3. Open `market_risk/pipeline.py`.
   Show that one controlled pipeline builds data quality checks, risk models,
   validation, stress, Treasury valuation, derivatives, PLA, RFET/NMRF, reports,
   and database persistence.
4. Open `market_risk/risk_models.py`, `market_risk/backtesting.py`, and
   `market_risk/model_validation.py`.
   Use these to show that VaR/ES, coverage tests, ES calibration, and bootstrap
   uncertainty are implemented as tested Python modules rather than notebook
   cells.
5. Open `market_risk/pla.py` and `market_risk/rfet.py`.
   These are the strongest "depth" modules because they address market-risk
   model validation and FRTB-style evidence limitations.
6. Open `sql/report_queries.sql`.
   Show that the outputs are designed for analyst reporting, not only Python
   charts.
7. Open `dashboard/app.py`.
   Show the dashboard tabs as the presentation layer for risk managers.
8. Open `docs/apra_boundary_framework.md`.
   Use this to show that the project is APRA-aware without pretending to be an
   approved regulatory system.
9. Open `tests/`.
   Mention the latest local validation: `28 passed, 1 skipped`; the skipped
   test is PostgreSQL integration gated by `TEST_DATABASE_URL`.

If running live:

```powershell
python -m market_risk.cli run
streamlit run dashboard/app.py
```

For public-data mode:

```powershell
python -m market_risk.cli download
python -m market_risk.cli download-rba
python -m market_risk.cli run
```

## Personal contribution

I designed and implemented the project end to end:

- Defined the scope around Australian market risk, treasury risk, model risk,
  and FinTech risk analytics roles.
- Built the Python package structure, CLI, configuration model, deterministic
  data generator, public-data download path, SQL layer, and Streamlit dashboard.
- Implemented five VaR/ES models: Historical, Parametric Normal, EWMA,
  Filtered Historical Simulation, and Student-t GARCH.
- Added model validation: Kupiec coverage, Christoffersen independence,
  combined coverage, Basel-style traffic light, ES calibration, moving-block
  bootstrap uncertainty, and common-holdout challenger ranking.
- Added Treasury valuation with RBA curves, AUD/USD forward valuation, DV01,
  convexity, key-rate DV01, and full-revaluation scenarios.
- Added nonlinear option risk with Black-Scholes Greeks, full revaluation,
  historical option VaR/ES, and approximation-error analysis.
- Added PLA-style actual, hypothetical, and risk-theoretical P&L attribution.
- Added RFET public-data evidence and NMRF fallback stress tables while clearly
  separating public proxy evidence from regulatory real-price evidence.
- Added documentation, case study, resume bullets, methodology notes, tests,
  and iterative GitHub commits.

## Quantified outputs

The deterministic demo currently produces:

| Evidence | Result |
|---|---:|
| Governed reporting tables | 37 |
| Reporting rows | 10,952 |
| Tests | 28 passed, 1 PostgreSQL test skipped without `TEST_DATABASE_URL` |
| Core analytics runtime | Under 7 seconds on the development machine |
| Scenario benchmark | More than 400x faster than the row-loop reference |
| Portfolio value | A$1,000,000 |
| FHS 99% VaR | A$35,653 |
| FHS rolling exceptions | 11 / 1,052 |
| FRTB-inspired liquidity-adjusted ES | A$273,262 |
| FRTB-inspired stress-scaled ES | A$386,601 |
| Option full-revaluation VaR | A$901 |
| Option approximation error in equity/vol stress | A$564 |
| PLA observations | 1,302 |
| Hypothetical vs risk-theoretical Spearman | 0.952 |
| Hypothetical vs risk-theoretical MAE ratio | 28.8% |
| RFET public-proxy factors | 8 |
| Largest NMRF fallback stress | A$55.6k |
| Modelled preparation-time reduction | 92.3% |
| Modelled monthly capacity released | 44 hours |

The efficiency figures are modelled workflow assumptions plus measured local
runtime and benchmark evidence. They should be presented as demonstrator
evidence, not as realised employer savings.

## A/B boundaries

Use these boundaries to avoid overclaiming.

| A: safe claim | B: do not claim |
|---|---|
| Built a reproducible market-risk analytics demonstrator | Built an approved production risk system |
| Implemented VaR/ES models and validation diagnostics | Built APRA/Basel-compliant market-risk capital |
| Produced FRTB-inspired ES and RFET/NMRF evidence tables | Passed regulatory IMA desk approval or RFET |
| Used public and deterministic data with lineage controls | Used confidential front-office trade/P&L data |
| Demonstrated PostgreSQL-compatible reporting | Deployed enterprise data governance or access control |
| Modelled workflow efficiency with transparent assumptions | Proved realised savings inside a bank |
| Added PLA-style P&L attribution workflow | Used official actual/hypothetical desk P&L |
| Demonstrated option full revaluation and approximation error | Built a full independent price verification platform |

## Defending common challenges

**"Is this real trading-book data?"**  
No. It is a public, reproducible proxy portfolio. That is deliberate because
the project is public GitHub work. The project shows the workflow, controls,
and model-risk thinking that would transfer to approved internal data.

**"Is this regulatory FRTB capital?"**  
No. It is FRTB-inspired management evidence. It implements 97.5% ES,
liquidity-horizon aggregation, stress scaling, RFET-style evidence, and NMRF
fallback concepts, but it does not claim regulatory capital, desk approval, or
default risk charge coverage.

**"Why include synthetic data?"**  
The deterministic generator makes tests and interviews reproducible without
redistributing vendor data. The same pipeline can use Yahoo Finance and RBA
downloads when public data is available.

**"Why does the RFET table say public proxy pass but regulatory RFET false?"**  
Because public closes can show frequency and gaps, but cannot prove real-price
observations such as trades or committed quotes. That separation is the point:
the project is honest about evidence quality.

**"Why is hypothetical vs risk-theoretical PLA only watch, not pass?"**  
The factor model captures direction well, with Spearman 0.952, but the residual
size is material at 28.8% of average absolute P&L. That is a realistic model
validation conclusion: high correlation is not enough to approve explanatory
power.

**"Why use realised volatility for options?"**  
Licensed implied-volatility surfaces cannot be redistributed in a public
portfolio project. Realised volatility keeps the example reproducible while the
methodology clearly states that production valuation needs approved implied vol
surfaces and independent price verification.

**"What is the strongest technical part?"**  
The strongest combination is the governed pipeline plus validation layers:
FHS/GARCH challenger modelling, ES calibration, bootstrap uncertainty,
PLA-style P&L attribution, RFET/NMRF evidence, and SQL/dashboard reporting from
the same run manifest.

**"What would you improve next?"**  
I would add transaction-backed RFET evidence, official desk actual and
hypothetical P&L, implied-volatility surfaces, scheduled orchestration, and
role-based review workflow. Those require internal or licensed data, so they
are documented as next depth rather than simulated as if they were real.

## Project limitations

- Portfolio instruments are public proxies, not an authorised deposit-taking
  institution trading book.
- PLA actual P&L is deterministic demonstrator data, not a front-office ledger.
- RFET evidence uses public closing prices and cannot establish real-price
  evidence.
- Option valuation uses realised volatility, European Black-Scholes assumptions,
  and omits American exercise, transaction costs, and independent price
  verification.
- PostgreSQL support is implemented, but the local automated test only runs
  when `TEST_DATABASE_URL` is available.
- Workflow savings are transparent assumptions, not observed employer metrics.
- The dashboard is designed for portfolio demonstration, not production access
  control, entitlements, or audit workflow.

## Closing line

This project is valuable because it moves beyond a single risk model. It shows
that I can build the surrounding control environment: data lineage, modelling,
validation, stress explanation, SQL reporting, dashboard presentation, and
honest model-risk limitations. That is the part most relevant to market risk,
treasury risk, model risk, and risk analytics roles.
