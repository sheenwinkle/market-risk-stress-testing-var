# APRA-Aware Boundary Framework

This project is a public job-application portfolio, not an APRA-regulated
production system. The goal is to show that the analytics workflow is organised
using prudential language, evidence discipline, and honest boundaries.

## Positioning

Use this wording in interviews:

> I did not build this as a production or regulatory capital system. I built it
> as an APRA-aware market-risk analytics portfolio. The project maps each major
> output to a prudential theme, shows the evidence produced by the code, and
> states exactly what is not claimed. That lets me demonstrate risk analytics
> capability while keeping a clean boundary between public portfolio evidence
> and regulated-bank evidence.

## APRA-Aware Design Principles

| Principle | How the project applies it |
|---|---|
| Use prudential language carefully | README, case study, methodology, and SQL distinguish demonstrator evidence from regulatory approval. |
| Produce evidence, not just charts | Each run writes CSV/SQL-ready tables, run hashes, validation outputs, limits, dashboard views, and a management summary. |
| Keep risk appetite visible | VaR, ES, and stress limits are configurable and show utilisation, headroom, and breach status. |
| Separate model result from model approval | Backtesting, ES diagnostics, bootstrap intervals, challenger ranking, and PLA residuals are evidence, not automatic approval. |
| Separate public proxy data from regulated evidence | RFET public-frequency proxy is not treated as regulatory RFET real-price evidence. |
| Make operational assumptions explicit | Efficiency claims are modelled assumptions plus measured local runtime, not realised bank savings. |
| Preserve reproducibility | Deterministic demo data and source hashes let an interviewer rerun the result without licensed data. |

## Prudential Evidence Map

The pipeline writes `prudential_evidence_map.csv` and persists it to SQL. This
table maps APRA-style themes to portfolio evidence, claim boundaries, and the
extra evidence a bank would need internally.

| Reference | Project evidence | Safe claim |
|---|---|---|
| APS 116 | VaR/ES, FRTB-inspired ES, RFET/NMRF tables | Market-risk measurement demonstrator, not regulatory capital. |
| CPS 220 | Limits, monitoring, model methodology, management summary | Risk framework thinking, not Board-approved risk management framework. |
| CPS 230 | Run manifest, data controls, runtime evidence | Operational discipline, not critical-operation resilience. |
| CPS 234 | Data lineage, hashes, source transparency | Data governance evidence, not full information-security capability. |
| APS 330 | README, case study, interview walkthrough | Transparent public disclosure style, not ADI Pillar 3 disclosure. |

References:

- APRA banking prudential standards: https://www.apra.gov.au/banking/Prudential-and-reporting-standards
- CPS 220 Risk Management: https://www.apra.gov.au/standards/cps-220
- CPS 230 Operational Risk Management: https://www.apra.gov.au/consultations/operational-risk-management
- Basel market-risk framework: https://www.bis.org/committees/bcbs/basel-framework/standard/mar

## What This Project Should Claim

- I can build a reproducible market-risk analytics pipeline.
- I understand market-risk model validation and reporting workflows.
- I can structure code, SQL, dashboard, and documentation around prudential
  review questions.
- I can separate public demonstrator evidence from regulated production
  evidence.
- I can quantify model performance, limit utilisation, stress impacts,
  nonlinear risk, PLA residuals, RFET evidence limits, and workflow efficiency.

## What This Project Should Not Claim

- It is not an APRA-compliant market-risk capital engine.
- It is not an approved internal model approach implementation.
- It does not establish regulatory RFET pass status.
- It does not use official trading-desk actual or hypothetical P&L.
- It does not provide CPS 230 critical-operation resilience.
- It does not provide CPS 234 information-security assurance.
- It does not replace independent model validation or internal audit.

## Interview Defence

If asked why the project includes APRA language:

> I included APRA language to structure the evidence and boundaries, not to claim
> compliance. A good risk analyst needs to know what their model proves, what it
> does not prove, and what evidence a regulated institution would still need.

If asked why not build production governance:

> That would be inappropriate for a public GitHub project because production
> governance depends on internal data, policies, ownership, and approvals. I
> instead built a transparent evidence map that shows how the analytics would
> plug into that governance.

If asked what the project contributes beyond a normal quant notebook:

> The project connects analytics to controls: run lineage, data quality, model
> monitoring, backtesting, ES calibration, PLA, RFET/NMRF boundaries, SQL
> reporting, dashboard presentation, and documented limitations.

## Best Next Portfolio Iteration

The next useful job-market iteration is not another pricing model. It is a
lightweight model validation report template generated from existing outputs:

- model purpose and scope;
- key assumptions and limitations;
- validation tests and results;
- challenger comparison;
- PLA and RFET findings;
- open issues and approval recommendation.

That would make the project stronger for model risk, market risk, and risk
analytics interviews without pretending to be a production system.
