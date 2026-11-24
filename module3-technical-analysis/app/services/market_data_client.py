
import requests
import pandas as pd


MODULE2_API_URL = "http://127.0.0.1:8001"


def fetch_stock_history(
    symbol: str,
    market: str = "NSE",
    period: str = "1Y"
) -> pd.DataFrame:
    """
    Fetch validated historical stock data from Module 2.

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

        # Extract validation information
        validation = result.get("validation", {})

        if validation.get("status") == "unusable":
            raise ValueError(
                "Module 2 returned unusable historical data."
            )

        # Extract historical records
        rows = result.get("rows", [])

        if not rows:
            raise ValueError(
                "No historical price records were returned."
            )

        df = pd.DataFrame(rows)

        # Check required columns
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

        # Convert dates
        df["date"] = pd.to_datetime(
            df["date"],
            errors="coerce"
        )

        if df["date"].isna().any():
            raise ValueError(
                "Historical data contains invalid dates."
            )

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

        # Invalid stock symbol
        if (
            exc.response is not None
            and exc.response.status_code == 404
        ):
            raise ValueError(
                f"Stock symbol '{symbol}' was not found in Module 2."
            ) from exc

        # Other HTTP errors
        raise RuntimeError(
            f"Module 2 API returned an HTTP error: {exc}"
        ) from exc

    except requests.RequestException as exc:

        # Connection or timeout errors
        raise RuntimeError(
            f"Could not connect to Module 2 API: {exc}"
        ) from exc
