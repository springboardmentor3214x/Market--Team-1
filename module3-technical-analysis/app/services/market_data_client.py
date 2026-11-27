
import requests
import pandas as pd
import numpy as np


MODULE2_API_URL = "http://127.0.0.1:8001"


def fetch_stock_history(
    symbol: str,
    market: str = "NSE",
    period: str = "1Y"
) -> pd.DataFrame:
    """
    Fetch and independently validate historical OHLCV data from Module 2.

    Preserves:
    - Historical OHLCV records
    - Module 2 validation report
    - Data provider metadata
    - Retrieval timestamp
    """

    url = f"{MODULE2_API_URL}/api/stocks/{symbol}/history"

    params = {
        "market": market,
        "period": period
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=30
        )

        response.raise_for_status()
        result = response.json()

        validation = result.get("validation", {})

        if validation.get("status") == "unusable":
            raise ValueError(
                "Module 2 returned unusable historical data."
            )

        rows = result.get("rows", [])

        if not rows:
            raise ValueError(
                "No historical price records were returned."
            )

        df = pd.DataFrame(rows)

        required_columns = [
            "date", "open", "high", "low", "close", "volume"
        ]

        missing_columns = [
            column for column in required_columns
            if column not in df.columns
        ]

        if missing_columns:
            raise ValueError(
                f"Missing historical data columns: {missing_columns}"
            )

        # Validate dates
        df["date"] = pd.to_datetime(
            df["date"],
            errors="coerce"
        )

        if df["date"].isna().any():
            raise ValueError(
                "Historical data contains invalid dates."
            )

        # Normalize dates to trading days
        df["date"] = df["date"].dt.normalize()

        # Validate numeric OHLCV values
        numeric_columns = [
            "open", "high", "low", "close", "volume"
        ]

        for column in numeric_columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

        if df[numeric_columns].isna().any().any():
            raise ValueError(
                "Historical data contains missing or non-numeric OHLCV values."
            )

        # Reject infinite values
        if not np.isfinite(df[numeric_columns].to_numpy()).all():
            raise ValueError(
                "Historical data contains infinite OHLCV values."
            )

        # Reject duplicate trading dates
        if df["date"].duplicated().any():
            raise ValueError(
                "Historical data contains duplicate trading dates."
            )

        # Validate positive prices
        price_columns = ["open", "high", "low", "close"]

        if (df[price_columns] <= 0).any().any():
            raise ValueError(
                "Historical data contains zero or negative prices."
            )

        # Validate High and Low consistency
        if (df["high"] < df["low"]).any():
            raise ValueError(
                "Historical data contains High prices below Low prices."
            )

        if (
            (df["open"] > df["high"] * (1 + 1e-6))
            | (df["open"] < df["low"] * (1 - 1e-6))
        ).any():
            raise ValueError(
                "Historical data contains Open prices outside the High-Low range."
            )

        if (
            (df["close"] > df["high"] * (1 + 1e-6))
            | (df["close"] < df["low"] * (1 - 1e-6))
        ).any():
            raise ValueError(
                "Historical data contains Close prices outside the High-Low range."
            )

        # Validate volume
        if (df["volume"] < 0).any():
            raise ValueError(
                "Historical data contains negative trading volume."
            )

        # Sort records chronologically
        df = df.sort_values(
            by="date"
        ).reset_index(drop=True)

        # Preserve Module 2 metadata
        df.attrs.update({
            "symbol": symbol,
            "market": market,
            "period": period,
            "validation": validation,
            "metadata": result.get("metadata", {})
        })

        return df

    except requests.HTTPError as exc:

        if (
            exc.response is not None
            and exc.response.status_code == 404
        ):
            raise ValueError(
                f"Stock symbol '{symbol}' was not found in Module 2."
            ) from exc

        raise RuntimeError(
            f"Module 2 API returned an HTTP error: {exc}"
        ) from exc

    except requests.RequestException as exc:

        raise RuntimeError(
            f"Could not connect to Module 2 API: {exc}"
        ) from exc
