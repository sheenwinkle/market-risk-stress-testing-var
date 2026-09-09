from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_run_manifest(
    config_path: str | Path,
    prices_path: str | Path,
    prices: pd.DataFrame,
    source_type: str = "unknown",
) -> pd.DataFrame:
    config_path = Path(config_path)
    prices_path = Path(prices_path)
    config_hash = _sha256(config_path)
    prices_hash = _sha256(prices_path)
    run_id = hashlib.sha256(f"{config_hash}:{prices_hash}".encode()).hexdigest()[:16]
    return pd.DataFrame(
        [
            {
                "run_id": run_id,
                "generated_at_utc": datetime.now(timezone.utc),
                "config_sha256": config_hash,
                "prices_sha256": prices_hash,
                "price_rows": len(prices),
                "price_columns": len(prices.columns),
                "price_start_date": prices.index.min().date(),
                "price_end_date": prices.index.max().date(),
                "pipeline_version": "0.3.0",
                "source_type": source_type,
            }
        ]
    )
