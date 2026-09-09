from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

SNAPSHOT_TABLES = {
    "risk_summary",
    "backtest_summary",
    "model_monitoring",
    "model_performance",
    "stress_results",
    "stress_contributions",
    "reverse_stress",
    "historical_stress",
    "factor_sensitivities",
    "component_var",
    "data_quality",
    "imputation_audit",
    "risk_limits",
    "performance_benchmark",
    "operational_efficiency",
    "run_manifest",
    "treasury_positions",
    "key_rate_dv01",
    "treasury_scenarios",
}


def engine_from_url(database_url: str) -> Engine:
    return create_engine(database_url, future=True)


def sqlite_url(path: str | Path) -> str:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{path.as_posix()}"


def _normalise_for_sql(frame: pd.DataFrame) -> pd.DataFrame:
    sql_frame = frame.copy()
    if sql_frame.index.name or not isinstance(sql_frame.index, pd.RangeIndex):
        sql_frame = sql_frame.reset_index()
    for column in sql_frame.columns:
        if pd.api.types.is_datetime64_any_dtype(sql_frame[column]):
            sql_frame[column] = sql_frame[column].dt.date
    return sql_frame


def persist_report_tables(
    database_url: str,
    tables: dict[str, pd.DataFrame],
    run_id: str,
) -> None:
    engine = engine_from_url(database_url)
    with engine.begin() as connection:
        for table_name, frame in tables.items():
            sql_frame = _normalise_for_sql(frame)
            is_snapshot = table_name in SNAPSHOT_TABLES
            existing_tables = set(inspect(connection).get_table_names())
            existing_columns = (
                {column["name"] for column in inspect(connection).get_columns(table_name)}
                if table_name in existing_tables
                else set()
            )
            if is_snapshot:
                if "run_id" in sql_frame.columns:
                    sql_frame["run_id"] = run_id
                else:
                    sql_frame.insert(0, "run_id", run_id)
                if table_name in existing_tables and "run_id" in existing_columns:
                    connection.execute(
                        text(f'DELETE FROM "{table_name}" WHERE run_id = :run_id'),
                        {"run_id": run_id},
                    )
                    write_mode = "append"
                else:
                    write_mode = "replace"
            else:
                write_mode = "replace"
            sql_frame.to_sql(
                table_name,
                con=connection,
                if_exists=write_mode,
                index=False,
                method="multi",
            )
            if is_snapshot:
                connection.execute(
                    text(
                        f'CREATE INDEX IF NOT EXISTS "idx_{table_name}_run_id" '
                        f'ON "{table_name}" (run_id)'
                    )
                )
