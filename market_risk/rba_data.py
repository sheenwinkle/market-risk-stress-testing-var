from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

RBA_BASE_URL = "https://www.rba.gov.au"
RBA_DATASETS = {
    "aud_exchange_rates": "/statistics/tables/csv/f11.1-data.csv",
    "aud_zero_curve": "/statistics/tables/csv/f17-yields.csv",
}


def parse_rba_csv(source: str | Path) -> pd.DataFrame:
    """Parse RBA statistical-table CSV files with their metadata header rows."""
    frame = pd.read_csv(source, skiprows=1, encoding="utf-8-sig")
    date_column = frame.columns[0]
    parsed_dates = pd.to_datetime(frame[date_column], format="%d-%b-%Y", errors="coerce")
    data = frame.loc[parsed_dates.notna()].copy()
    data.index = pd.DatetimeIndex(parsed_dates[parsed_dates.notna()], name="date")
    data = data.drop(columns=[date_column]).apply(pd.to_numeric, errors="coerce")
    return data.dropna(how="all").sort_index()


def _select_exchange_rates(frame: pd.DataFrame) -> pd.DataFrame:
    selected = frame.iloc[:, :2].copy()
    selected.columns = ["AUDUSD", "AUD_TWI"]
    return selected


def _select_zero_curve(frame: pd.DataFrame) -> pd.DataFrame:
    maturities = {0.0, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0}
    selected: dict[str, pd.Series] = {}
    for column in frame.columns:
        label = str(column).replace("–", "-").replace("—", "-")
        maturity_text = label.split("-")[-1].strip().split(" yr")[0]
        try:
            maturity = float(maturity_text)
        except ValueError:
            continue
        if maturity in maturities:
            suffix = str(maturity).replace(".0", "").replace(".", "P")
            selected[f"AUD_ZC_{suffix}Y"] = frame[column]
    if not selected:
        raise ValueError("No configured zero-curve maturities found in RBA F17 data.")
    return pd.DataFrame(selected)


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def download_rba_market_data(output_dir: str | Path) -> pd.DataFrame:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    catalog_rows = []
    for dataset, relative_url in RBA_DATASETS.items():
        url = f"{RBA_BASE_URL}{relative_url}"
        raw = parse_rba_csv(url)
        curated = _select_exchange_rates(raw) if dataset == "aud_exchange_rates" else _select_zero_curve(raw)
        path = output_dir / f"{dataset}.csv"
        curated.to_csv(path, index_label="date")
        catalog_rows.append(
            {
                "dataset": dataset,
                "provider": "Reserve Bank of Australia",
                "source_url": url,
                "retrieved_at_utc": datetime.now(timezone.utc),
                "rows": len(curated),
                "series": len(curated.columns),
                "start_date": curated.index.min().date(),
                "end_date": curated.index.max().date(),
                "sha256": _file_sha256(path),
            }
        )
    catalog = pd.DataFrame(catalog_rows)
    catalog.to_csv(output_dir / "data_catalog.csv", index=False)
    return catalog
