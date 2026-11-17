"""Data validation for OHLCV data (pandas + NumPy).

Checks: missing values, duplicate dates, inconsistent prices, bad date formats,
non-numeric values and unexpected records. Returns the CLEANED data plus a
report describing every problem found and what was done about it.
"""
from datetime import date
from typing import Optional

import numpy as np
import pandas as pd

PRICE_COLS = ["Open", "High", "Low", "Close"]
NUMERIC_COLS = PRICE_COLS + ["Adj Close", "Volume"]
TOLERANCE = 1e-6  # relative tolerance for floating point comparisons

CHECKS_PERFORMED = [
    "Date format validity",
    "Non-numeric values",
    "Future-dated records",
    "Duplicate trading dates",
    "Missing values (Open/High/Low/Close/Volume)",
    "Non-positive prices",
    "High price lower than Low price",
    "Open price outside the High-Low range",
    "Close price outside the High-Low range",
    "Negative volume",
    "Weekend trading dates",
    "Extreme one-day price moves",
    "Stale data (latest date too old)",
]


def _sample_dates(series: pd.Series, n: int = 10) -> list[str]:
    return [d.strftime("%Y-%m-%d") for d in pd.to_datetime(series).head(n)]


def _issue(type_, severity, description, action, count, dates=None, **extra) -> dict:
    d = {
        "type": type_,
        "severity": severity,  # "error" -> rows removed/changed, "warning" -> kept but flagged
        "description": description,
        "action": action,
        "count": int(count),
        "sample_dates": dates or [],
    }
    d.update(extra)
    return d


def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename = {}
    for c in df.columns:
        key = str(c).strip().lower().replace("_", " ")
        rename[c] = {
            "date": "Date", "open": "Open", "high": "High", "low": "Low",
            "close": "Close", "adj close": "Adj Close", "adjclose": "Adj Close",
            "volume": "Volume",
        }.get(key, c)
    return df.rename(columns=rename)


def validate_ohlcv(
    raw: pd.DataFrame, today: Optional[date] = None
) -> tuple[pd.DataFrame, dict]:
    today = today or date.today()
    issues: list[dict] = []

    df = _normalise_columns(raw.copy())
    if "Date" not in df.columns:  # date may still be the index
        df = df.reset_index().rename(columns={df.index.name or "index": "Date"})
    rows_received = len(df)

    missing_cols = [c for c in ["Date"] + PRICE_COLS if c not in df.columns]
    if missing_cols:
        issues.append(_issue("missing_columns", "error",
                             f"Required columns missing: {', '.join(missing_cols)}",
                             "Dataset rejected", len(missing_cols)))
        return _empty(), _report(rows_received, 0, issues)
    for optional in ("Adj Close", "Volume"):
        if optional not in df.columns:
            df[optional] = np.nan

    # 1. Dates -------------------------------------------------------------
    dates = pd.to_datetime(df["Date"], errors="coerce")
    if getattr(dates.dt, "tz", None) is not None:
        dates = dates.dt.tz_localize(None)
    bad_date = dates.isna()
    if bad_date.any():
        issues.append(_issue("invalid_dates", "error",
                             "Rows whose date is missing or not a valid date",
                             "Rows removed", bad_date.sum()))
    df["Date"] = dates.dt.normalize()
    df = df[~bad_date].copy()

    # 2. Non-numeric values ---------------------------------------------------
    nonnum_total = 0
    for col in NUMERIC_COLS:
        before_null = df[col].isna()
        df[col] = pd.to_numeric(df[col], errors="coerce")
        nonnum_total += int((~before_null & df[col].isna()).sum())
    if nonnum_total:
        issues.append(_issue("non_numeric_values", "error",
                             "Price/volume cells containing text instead of numbers",
                             "Converted to missing values", nonnum_total))
    df[NUMERIC_COLS] = df[NUMERIC_COLS].replace([np.inf, -np.inf], np.nan)

    # 3. Future dates ---------------------------------------------------------
    future = df["Date"] > pd.Timestamp(today)
    if future.any():
        issues.append(_issue("future_dates", "error", "Records dated in the future",
                             "Rows removed", future.sum(), _sample_dates(df.loc[future, "Date"])))
        df = df[~future].copy()

    # 4. Duplicate dates (keep the most complete, then the latest, row) ----------
    df["_complete"] = df[PRICE_COLS].notna().all(axis=1)
    df = df.sort_values(["Date", "_complete"], kind="stable")
    dup = df.duplicated(subset="Date", keep="last")
    if dup.any():
        issues.append(_issue("duplicate_dates", "error",
                             "The same trading date appears more than once",
                             "Kept one row per date (the most complete / latest)",
                             dup.sum(), _sample_dates(df.loc[dup, "Date"])))
        df = df[~dup].copy()
    df = df.drop(columns="_complete")

    # 5. Missing values -----------------------------------------------------------
    per_col = {c: int(df[c].isna().sum()) for c in PRICE_COLS + ["Volume"] if df[c].isna().any()}
    missing_price = df[PRICE_COLS].isna().any(axis=1)
    if missing_price.any():
        issues.append(_issue("missing_prices", "error",
                             "Rows missing Open, High, Low or Close",
                             "Rows removed (a price record without all four prices cannot be used)",
                             missing_price.sum(), _sample_dates(df.loc[missing_price, "Date"]),
                             missing_by_column={k: v for k, v in per_col.items() if k != "Volume"}))
        df = df[~missing_price].copy()
    if df["Volume"].isna().any():
        issues.append(_issue("missing_volume", "warning",
                             "Rows with no traded volume value",
                             "Kept; volume left empty (null), not guessed",
                             df["Volume"].isna().sum(),
                             _sample_dates(df.loc[df["Volume"].isna(), "Date"])))

    # 6. Logical consistency (all on the same raw price basis) -------------------------
    nonpos = (df[PRICE_COLS] <= 0).any(axis=1)
    hl = (df["High"] < df["Low"]) & ~nonpos
    open_bad = ((df["Open"] > df["High"] * (1 + TOLERANCE)) |
                (df["Open"] < df["Low"] * (1 - TOLERANCE))) & ~nonpos & ~hl
    close_bad = ((df["Close"] > df["High"] * (1 + TOLERANCE)) |
                 (df["Close"] < df["Low"] * (1 - TOLERANCE))) & ~nonpos & ~hl
    for mask, t, desc in (
        (nonpos, "non_positive_price", "Zero or negative price"),
        (hl, "high_below_low", "High price is lower than Low price"),
        (open_bad, "open_outside_range", "Open price is outside the High-Low range"),
        (close_bad, "close_outside_range", "Close price is outside the High-Low range"),
    ):
        if mask.any():
            issues.append(_issue(t, "error", desc, "Rows removed (cannot be trusted)",
                                 mask.sum(), _sample_dates(df.loc[mask, "Date"])))
    bad_rows = nonpos | hl | open_bad | close_bad
    df = df[~bad_rows].copy()

    neg_vol = df["Volume"] < 0
    if neg_vol.any():
        issues.append(_issue("negative_volume", "error", "Negative traded volume",
                             "Volume set to empty (null)", neg_vol.sum(),
                             _sample_dates(df.loc[neg_vol, "Date"])))
        df.loc[neg_vol, "Volume"] = np.nan

    # 7. Unexpected-but-kept records (warnings only) ---------------------------------
    df = df.sort_values("Date").reset_index(drop=True)
    weekend = df["Date"].dt.dayofweek >= 5
    if weekend.any():
        issues.append(_issue("weekend_dates", "warning",
                             "Prices dated on a Saturday/Sunday (unusual for these exchanges)",
                             "Kept but flagged", weekend.sum(),
                             _sample_dates(df.loc[weekend, "Date"])))
    if len(df) > 1:
        ret = df["Close"].pct_change().abs()
        extreme = ret > 0.5
        if extreme.any():
            issues.append(_issue("extreme_price_moves", "warning",
                                 "Close price changed by more than 50% in one day "
                                 "(could be a real event, a stock split or bad data)",
                                 "Kept but flagged for review", extreme.sum(),
                                 _sample_dates(df.loc[extreme, "Date"])))
    if len(df) and (pd.Timestamp(today) - df["Date"].iloc[-1]).days > 7:
        issues.append(_issue("stale_data", "warning",
                             "The latest price is more than 7 days old",
                             "Kept; data may be outdated", 1,
                             [df["Date"].iloc[-1].strftime("%Y-%m-%d")]))

    df["Date"] = df["Date"].dt.date
    return df[["Date"] + NUMERIC_COLS], _report(rows_received, len(df), issues)


def _empty() -> pd.DataFrame:
    return pd.DataFrame(columns=["Date"] + NUMERIC_COLS)


def _report(rows_in: int, rows_out: int, issues: list[dict]) -> dict:
    errors = [i for i in issues if i["severity"] == "error"]
    if rows_out == 0:
        status = "unusable"
    elif errors:
        status = "cleaned"
    else:
        status = "clean"
    return {
        "status": status,  # clean | cleaned | unusable
        "rows_received": rows_in,
        "rows_valid": rows_out,
        "rows_removed": rows_in - rows_out,
        "issues": issues,
        "issue_count": len(issues),
        "checks_performed": CHECKS_PERFORMED,
        "policy": (
            "Rows with missing/invalid prices are removed, duplicate dates are collapsed to one row, "
            "and nothing is estimated or invented. Unusual-but-possible records are kept and flagged."
        ),
    }


def _clean(v):
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return None
    return v


def df_to_rows(df: pd.DataFrame) -> list[dict]:
    """Cleaned DataFrame -> JSON-safe list of OHLCV dicts."""
    rows = []
    for r in df.itertuples(index=False):
        vol = _clean(None if pd.isna(r.Volume) else float(r.Volume))
        adj = None if pd.isna(r[5]) else round(float(r[5]), 4)
        rows.append({
            "date": r.Date.isoformat(),
            "open": round(float(r.Open), 4),
            "high": round(float(r.High), 4),
            "low": round(float(r.Low), 4),
            "close": round(float(r.Close), 4),
            "adj_close": adj,
            "volume": int(vol) if vol is not None else None,
        })
    return rows
