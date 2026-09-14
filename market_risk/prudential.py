from __future__ import annotations

import pandas as pd


def prudential_evidence_map() -> pd.DataFrame:
    """Map project evidence to APRA-style prudential themes without claiming compliance."""
    rows = [
        {
            "prudential_reference": "APS 116",
            "theme": "market risk capital and measurement",
            "project_evidence": "frtb_es_summary; frtb_liquidity_buckets; risk_summary",
            "demonstrated_capability": (
                "VaR/ES, liquidity-horizon ES, stress scaling, and risk-factor evidence"
            ),
            "boundary_statement": (
                "FRTB-inspired management evidence only; not a regulatory market-risk "
                "capital calculation"
            ),
            "production_evidence_needed": (
                "approved trading-book boundary, capital aggregation, standardised approach "
                "or IMA approval, DRC, RRAO, and regulatory return mapping"
            ),
            "portfolio_claim_status": "portfolio_evidence_only",
            "source_url": "https://www.apra.gov.au/banking/Prudential-and-reporting-standards",
        },
        {
            "prudential_reference": "CPS 220",
            "theme": "risk management framework",
            "project_evidence": (
                "risk_limits; model_monitoring; management_summary; "
                "docs/model_methodology.md"
            ),
            "demonstrated_capability": (
                "risk identification, measurement, monitoring, reporting, and transparent "
                "risk appetite limits"
            ),
            "boundary_statement": (
                "demonstrates analyst-level risk framework thinking; not a Board-approved "
                "risk management framework"
            ),
            "production_evidence_needed": (
                "Board risk appetite statement, risk management strategy, RACI, independent "
                "review, breach escalation, and risk committee minutes"
            ),
            "portfolio_claim_status": "portfolio_evidence_only",
            "source_url": "https://www.apra.gov.au/standards/cps-220",
        },
        {
            "prudential_reference": "CPS 230",
            "theme": "operational risk and resilience",
            "project_evidence": "operational_efficiency; run_manifest; data_quality",
            "demonstrated_capability": (
                "controlled run evidence, runtime metrics, input hashes, data controls, "
                "and repeatable reporting"
            ),
            "boundary_statement": (
                "shows operational discipline for a portfolio project; not critical "
                "operation resilience"
            ),
            "production_evidence_needed": (
                "critical operation mapping, tolerance levels, BCP tests, incident process, "
                "material service provider register, and recovery evidence"
            ),
            "portfolio_claim_status": "portfolio_evidence_only",
            "source_url": "https://www.apra.gov.au/consultations/operational-risk-management",
        },
        {
            "prudential_reference": "CPS 234",
            "theme": "information security",
            "project_evidence": "data_quality; run_manifest; docs/data_dictionary.md",
            "demonstrated_capability": (
                "data lineage, source transparency, deterministic hashes, and raw-data "
                "redistribution boundaries"
            ),
            "boundary_statement": (
                "data-governance evidence only; not an information-security control environment"
            ),
            "production_evidence_needed": (
                "role-based access, encryption, secrets management, audit logs, vulnerability "
                "management, incident response, and control attestations"
            ),
            "portfolio_claim_status": "portfolio_evidence_only",
            "source_url": "https://www.apra.gov.au/banking/Prudential-and-reporting-standards",
        },
        {
            "prudential_reference": "APS 330",
            "theme": "public disclosure discipline",
            "project_evidence": "README.md; docs/case_study.md; docs/interview_walkthrough.md",
            "demonstrated_capability": (
                "public-facing risk profile, methods, quantified outputs, limitations, "
                "and safe claim boundaries"
            ),
            "boundary_statement": (
                "transparent portfolio disclosure; not an ADI Pillar 3 disclosure"
            ),
            "production_evidence_needed": (
                "approved capital templates, governance review, external audit alignment, "
                "and formal disclosure sign-off"
            ),
            "portfolio_claim_status": "portfolio_evidence_only",
            "source_url": "https://www.apra.gov.au/banking/Prudential-and-reporting-standards",
        },
        {
            "prudential_reference": "model risk good practice",
            "theme": "independent model validation",
            "project_evidence": (
                "backtest_summary; es_backtesting; tail_risk_uncertainty; "
                "pnl_attribution_summary"
            ),
            "demonstrated_capability": (
                "coverage testing, independence testing, ES diagnostics, bootstrap uncertainty, "
                "PLA-style residual analysis, and challenger comparison"
            ),
            "boundary_statement": (
                "self-contained validation evidence; not independent second-line model approval"
            ),
            "production_evidence_needed": (
                "independent validation report, implementation review, model inventory, "
                "approval conditions, issue tracking, and periodic review"
            ),
            "portfolio_claim_status": "portfolio_evidence_only",
            "source_url": "https://www.apra.gov.au/standards/cps-220",
        },
        {
            "prudential_reference": "FRTB RFET/NMRF",
            "theme": "risk-factor modellability evidence",
            "project_evidence": "rfet_observation_evidence; nmrf_stress_fallback",
            "demonstrated_capability": (
                "public-frequency proxy, observation gap review, real-price limitation flag, "
                "and standalone fallback stress estimate"
            ),
            "boundary_statement": (
                "public frequency evidence only; public closes do not prove real-price evidence"
            ),
            "production_evidence_needed": (
                "trade or committed-quote evidence, observation policy, approved data vendors, "
                "retention controls, and formal NMRF capital treatment"
            ),
            "portfolio_claim_status": "portfolio_evidence_only",
            "source_url": "https://www.bis.org/committees/bcbs/basel-framework/standard/mar",
        },
        {
            "prudential_reference": "valuation control",
            "theme": "pricing and independent price verification",
            "project_evidence": "treasury_positions; derivative_positions; derivative_scenarios",
            "demonstrated_capability": (
                "cash-flow valuation, DV01, key-rate DV01, option Greeks, full revaluation, "
                "and approximation-error analysis"
            ),
            "boundary_statement": (
                "transparent valuation demonstrator; not independent price verification"
            ),
            "production_evidence_needed": (
                "approved market data, IPV tolerances, valuation reserves, curve construction "
                "standards, and independent sign-off"
            ),
            "portfolio_claim_status": "portfolio_evidence_only",
            "source_url": "https://www.apra.gov.au/banking/Prudential-and-reporting-standards",
        },
    ]
    return pd.DataFrame(rows)
