from market_risk.prudential import prudential_evidence_map


def test_prudential_evidence_map_preserves_portfolio_boundaries():
    evidence = prudential_evidence_map()

    assert {"APS 116", "CPS 220", "CPS 230", "CPS 234"} <= set(
        evidence["prudential_reference"]
    )
    assert set(evidence["portfolio_claim_status"]) == {"portfolio_evidence_only"}
    assert evidence["boundary_statement"].str.contains("not|only", case=False).all()
    assert evidence["production_evidence_needed"].str.len().min() > 20
    assert evidence["source_url"].str.startswith("https://").all()
