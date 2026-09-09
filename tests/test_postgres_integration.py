import os

import pandas as pd
import pytest
from sqlalchemy import create_engine, text

from market_risk.database import persist_report_tables

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


@pytest.mark.skipif(not TEST_DATABASE_URL, reason="TEST_DATABASE_URL is not configured")
def test_postgres_snapshot_persistence():
    tables = {"risk_summary": pd.DataFrame([{"model": "test", "value_aud": 123.0}])}
    persist_report_tables(TEST_DATABASE_URL, tables, "integration-test")

    engine = create_engine(TEST_DATABASE_URL)
    with engine.connect() as connection:
        count = connection.execute(
            text("select count(*) from risk_summary where run_id = 'integration-test'")
        ).scalar_one()

    assert count == 1
