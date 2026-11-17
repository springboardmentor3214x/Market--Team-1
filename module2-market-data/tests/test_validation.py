from datetime import date, timedelta

import numpy as np
import pandas as pd

from app.services.validation import df_to_rows, validate_ohlcv
from tests.conftest import sample_history


def issue_types(report):
    return {i["type"] for i in report["issues"]}


def test_clean_data_passes_untouched():
    df = sample_history(30)
    clean, rep = validate_ohlcv(df)
    assert rep["status"] == "clean"
    assert rep["rows_received"] == 30 and rep["rows_valid"] == 30 and rep["rows_removed"] == 0
    assert rep["issues"] == []
    assert list(clean.columns) == ["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]


def test_output_sorted_ascending():
    df = sample_history(10).iloc[::-1].reset_index(drop=True)
    clean, _ = validate_ohlcv(df)
    assert list(clean["Date"]) == sorted(clean["Date"])


def test_missing_close_row_removed():
    df = sample_history(10)
    df.loc[3, "Close"] = np.nan
    clean, rep = validate_ohlcv(df)
    assert len(clean) == 9
    assert "missing_prices" in issue_types(rep)
    assert rep["status"] == "cleaned"


def test_missing_open_high_still_flagged_even_if_close_exists():
    df = sample_history(10)
    df.loc[2, ["Open", "High"]] = np.nan
    clean, rep = validate_ohlcv(df)
    assert len(clean) == 9
    mp = next(i for i in rep["issues"] if i["type"] == "missing_prices")
    assert mp["missing_by_column"] == {"Open": 1, "High": 1}


def test_missing_volume_kept_as_null_not_guessed():
    df = sample_history(10)
    df.loc[4, "Volume"] = np.nan
    clean, rep = validate_ohlcv(df)
    assert len(clean) == 10
    rows = df_to_rows(clean)
    assert rows[4]["volume"] is None
    mv = next(i for i in rep["issues"] if i["type"] == "missing_volume")
    assert mv["severity"] == "warning"
    assert rep["status"] == "clean"  # warnings alone do not make data "cleaned"


def test_duplicate_dates_collapsed_keeping_complete_row():
    df = sample_history(10)
    bad = df.iloc[[5]].copy()
    bad["Close"] = np.nan  # incomplete duplicate placed AFTER the good one
    df = pd.concat([df, bad], ignore_index=True)
    clean, rep = validate_ohlcv(df)
    assert len(clean) == 10
    assert clean["Date"].is_unique
    assert "duplicate_dates" in issue_types(rep)
    assert "missing_prices" not in issue_types(rep)  # the complete row was kept


def test_high_below_low_removed():
    df = sample_history(10)
    df.loc[1, "High"], df.loc[1, "Low"] = 90.0, 110.0
    clean, rep = validate_ohlcv(df)
    assert len(clean) == 9 and "high_below_low" in issue_types(rep)


def test_open_and_close_outside_range_removed():
    df = sample_history(10)
    df.loc[2, "Open"] = df.loc[2, "High"] + 5
    df.loc[6, "Close"] = df.loc[6, "Low"] - 5
    clean, rep = validate_ohlcv(df)
    assert len(clean) == 8
    assert {"open_outside_range", "close_outside_range"} <= issue_types(rep)


def test_open_exactly_on_high_is_valid():
    df = sample_history(5)
    df.loc[1, "Open"] = df.loc[1, "High"]
    clean, rep = validate_ohlcv(df)
    assert len(clean) == 5 and rep["status"] == "clean"


def test_zero_and_negative_prices_removed():
    df = sample_history(10)
    df.loc[0, "Low"] = 0.0
    df.loc[1, "Close"] = -4.0
    clean, rep = validate_ohlcv(df)
    assert "non_positive_price" in issue_types(rep)
    assert len(clean) == 8


def test_negative_volume_set_to_null():
    df = sample_history(5)
    df.loc[2, "Volume"] = -10
    clean, rep = validate_ohlcv(df)
    assert len(clean) == 5
    assert df_to_rows(clean)[2]["volume"] is None
    assert "negative_volume" in issue_types(rep)


def test_future_dates_removed():
    df = sample_history(5)
    fut = df.iloc[[0]].copy()
    fut["Date"] = pd.Timestamp(date.today() + timedelta(days=10))
    clean, rep = validate_ohlcv(pd.concat([df, fut], ignore_index=True))
    assert len(clean) == 5 and "future_dates" in issue_types(rep)


def test_invalid_date_strings_removed():
    df = sample_history(5)
    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
    df.loc[1, "Date"] = "2024-13-45"
    df.loc[2, "Date"] = "not a date"
    clean, rep = validate_ohlcv(df)
    assert len(clean) == 3
    assert next(i for i in rep["issues"] if i["type"] == "invalid_dates")["count"] == 2


def test_non_numeric_values_become_missing_and_row_dropped():
    df = sample_history(5).astype({"Open": object})
    df.loc[1, "Open"] = "abc"
    clean, rep = validate_ohlcv(df)
    assert len(clean) == 4
    assert {"non_numeric_values", "missing_prices"} <= issue_types(rep)


def test_weekend_and_extreme_move_and_stale_are_warnings_only():
    df = sample_history(6)
    df.loc[0, "Date"] = pd.Timestamp("2024-01-06")  # Saturday, and old
    df.loc[3, ["Open", "High", "Low", "Close"]] = [300.0, 301.0, 299.0, 300.0]
    df.loc[4:, ["Open", "High", "Low", "Close"]] = [[301.0, 302.0, 300.0, 301.0]] * 2
    clean, rep = validate_ohlcv(df)
    assert "weekend_dates" in issue_types(rep)
    assert "extreme_price_moves" in issue_types(rep)
    assert all(i["severity"] == "warning" for i in rep["issues"])
    assert rep["status"] == "clean"


def test_stale_data_warning():
    df = sample_history(5)
    df["Date"] = df["Date"] - pd.Timedelta(days=60)
    _, rep = validate_ohlcv(df)
    assert "stale_data" in issue_types(rep)


def test_empty_dataframe_is_unusable():
    clean, rep = validate_ohlcv(sample_history(5).iloc[0:0])
    assert len(clean) == 0 and rep["status"] == "unusable"


def test_missing_required_column_is_unusable():
    clean, rep = validate_ohlcv(sample_history(5).drop(columns=["Close"]))
    assert rep["status"] == "unusable" and "missing_columns" in issue_types(rep)


def test_timezone_aware_dates_keep_local_calendar_day():
    df = sample_history(5)
    df["Date"] = df["Date"].dt.tz_localize("Asia/Kolkata")
    clean, _ = validate_ohlcv(df)
    assert list(clean["Date"]) == [d.date() for d in sample_history(5)["Date"]]


def test_lowercase_columns_accepted():
    df = sample_history(5)
    df.columns = [c.lower().replace(" ", "_") for c in df.columns]
    clean, rep = validate_ohlcv(df)
    assert len(clean) == 5 and rep["status"] == "clean"


def test_report_lists_checks_and_sample_dates():
    df = sample_history(10)
    df.loc[1, "Close"] = np.nan
    _, rep = validate_ohlcv(df)
    assert len(rep["checks_performed"]) >= 10
    assert len(rep["issues"][0]["sample_dates"]) == 1
