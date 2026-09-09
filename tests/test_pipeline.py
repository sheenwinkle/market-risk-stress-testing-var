from pathlib import Path

import pandas as pd

from market_risk.pipeline import run_pipeline


def test_pipeline_creates_reports_and_sqlite_database(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[1]
    result = run_pipeline(
        config_path=repo_root / "configs" / "portfolio.yml",
        prices_path=tmp_path / "prices.csv",
        report_dir=tmp_path / "reports",
    )

    assert (tmp_path / "prices.csv").exists()
    assert (tmp_path / "reports" / "risk_summary.csv").exists()
    assert (tmp_path / "reports" / "risk_reports.db").exists()
    assert not result.risk_summary.empty
    assert set(result.backtests["model"]) == {"historical", "parametric_normal", "ewma"}
    assert (tmp_path / "reports" / "management_summary.md").exists()
    assert (tmp_path / "reports" / "operational_efficiency.csv").exists()
    assert (tmp_path / "reports" / "risk_limits.csv").exists()
    assert (tmp_path / "reports" / "run_manifest.csv").exists()
    assert set(result.risk_limits["status"]) <= {"pass", "breach"}

    stress = pd.read_csv(tmp_path / "reports" / "stress_results.csv")
    assert stress["loss_aud"].max() > 0

    contributions = pd.read_csv(tmp_path / "reports" / "stress_contributions.csv")
    contribution_loss = -contributions.groupby("scenario")["pnl_aud"].sum()
    stress_loss = stress.set_index("scenario")["loss_aud"]
    pd.testing.assert_series_equal(
        contribution_loss.sort_index(),
        stress_loss.sort_index(),
        check_names=False,
    )

    manifest = pd.read_csv(tmp_path / "reports" / "run_manifest.csv")
    assert manifest.loc[0, "price_rows"] > 1_000
    assert len(manifest.loc[0, "prices_sha256"]) == 64
