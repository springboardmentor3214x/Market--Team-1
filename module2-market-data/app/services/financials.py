"""Convert provider statement DataFrames into clean JSON-friendly dicts."""
from typing import Optional

import numpy as np
import pandas as pd

STATEMENT_LABELS = {
    "income_statement": "Income Statement",
    "balance_sheet": "Balance Sheet",
    "cash_flow": "Cash Flow Statement",
}


def statement_to_dict(df: Optional[pd.DataFrame]) -> Optional[dict]:
    """Rows = line items, columns = period end dates (as yfinance returns).
    Returns {periods: [newest..oldest], items: {item: {period: value|None}}} or None if empty."""
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return None
    df = df.copy()
    try:
        cols = pd.to_datetime(df.columns)
        order = np.argsort(cols.values)[::-1]  # newest first
        df = df.iloc[:, order]
        periods = [pd.Timestamp(c).strftime("%Y-%m-%d") for c in cols[order]]
    except Exception:
        periods = [str(c) for c in df.columns]
    df.columns = periods

    items: dict[str, dict] = {}
    for name, row in df.iterrows():
        vals = pd.to_numeric(row, errors="coerce")
        if vals.isna().all():
            continue  # line item with no data at all
        items[str(name)] = {
            p: (None if pd.isna(v) or np.isinf(v) else float(v)) for p, v in vals.items()
        }
    if not items:
        return None
    return {"periods": periods, "items": items}
