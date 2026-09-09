import pandas as pd
from sqlalchemy import create_engine, text

from market_risk.database import persist_report_tables


def test_snapshot_tables_are_idempotent_and_preserve_new_runs(tmp_path):
    database_url = f"sqlite:///{(tmp_path / 'history.db').as_posix()}"
    tables = {
        "risk_summary": pd.DataFrame([{"model": "historical", "value_aud": 100.0}]),
        "prices": pd.DataFrame([{"date": "2025-01-01", "A": 10.0}]),
    }

    persist_report_tables(database_url, tables, "run-one")
    persist_report_tables(database_url, tables, "run-one")
    persist_report_tables(database_url, tables, "run-two")

    engine = create_engine(database_url)
    with engine.connect() as connection:
        snapshot_count = connection.execute(text("select count(*) from risk_summary")).scalar_one()
        run_count = connection.execute(
            text("select count(distinct run_id) from risk_summary")
        ).scalar_one()
        price_count = connection.execute(text("select count(*) from prices")).scalar_one()

    assert snapshot_count == 2
    assert run_count == 2
    assert price_count == 1
