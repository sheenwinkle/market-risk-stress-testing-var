from io import StringIO

import numpy as np
import pandas as pd

from market_risk.data import impute_prices
from market_risk.rba_data import parse_rba_csv


def test_imputation_audit_preserves_raw_missing_evidence():
    prices = pd.DataFrame({"A": [10.0, np.nan, 11.0], "B": [20.0, 20.5, 21.0]})

    cleaned, audit = impute_prices(prices)

    assert cleaned.loc[1, "A"] == 10.0
    assert audit.set_index("ticker").loc["A", "raw_missing_count"] == 1
    assert audit.set_index("ticker").loc["A", "imputed_count"] == 1


def test_parse_rba_csv_removes_metadata_rows():
    source = StringIO(
        "F11 TEST\n"
        "Title,A$1=USD,Index\n"
        "Description,FX,TWI\n"
        "Frequency,Daily,Daily\n"
        "Series ID,FXRUSD,FXRTWI\n"
        "03-Jan-2025,0.62,60.1\n"
        "06-Jan-2025,0.63,60.5\n"
    )

    result = parse_rba_csv(source)

    assert len(result) == 2
    assert result.index.min() == pd.Timestamp("2025-01-03")
