from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


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


def persist_report_tables(database_url: str, tables: dict[str, pd.DataFrame]) -> None:
    engine = engine_from_url(database_url)
    with engine.begin() as connection:
        for table_name, frame in tables.items():
            _normalise_for_sql(frame).to_sql(
                table_name,
                con=connection,
                if_exists="replace",
                index=False,
                method="multi",
            )

