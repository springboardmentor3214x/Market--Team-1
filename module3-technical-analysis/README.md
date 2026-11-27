
# MarketAI – Technical Analysis Agent

## 1. Overview

The Technical Analysis Agent is an independent component of the MarketAI project.

It analyzes real historical stock market data using technical indicators, generates bullish, bearish, and neutral signals, identifies technical conditions, and produces visual charts.

The agent retrieves historical OHLCV data from Module 2 through a REST API.

## 2. Features

- Fetches real historical stock data from Module 2.
- Validates historical OHLCV records.
- Calculates Simple Moving Average (SMA 20).
- Calculates Exponential Moving Average (EMA 12, 20, 26).
- Calculates Relative Strength Index (RSI 14).
- Calculates MACD using EMA 12, EMA 26, and signal EMA 9.
- Calculates annualized historical volatility.
- Generates bullish, bearish, and neutral signals.
- Classifies trends as upward, downward, or mixed.
- Detects technical events and crossover conditions.
- Provides plain-language explanations of detected conditions.
- Generates four technical analysis charts.
- Preserves data validation and provider metadata.
- Exposes analysis through a FastAPI endpoint.
- Uses Pydantic models for structured request and response validation.

## 3. Technology Stack

- Python 3.13
- FastAPI
- Pandas
- NumPy
- Matplotlib
- TA
- Pydantic
- Requests
- Pytest
- Uvicorn

## 4. Project Structure

```text
module3-technical-analysis/
|
|-- app/
|   |-- main.py
|   |
|   |-- models/
|   |   |-- technical_analysis.py
|   |
|   |-- services/
|       |-- indicators.py
|       |-- market_data_client.py
|       |-- signals.py
|       |-- conditions.py
|       |-- technical_analysis.py
|       |-- charts.py
|
|-- tests/
|   |-- test_api.py
|   |-- test_indicators.py
|   |-- test_real_data.py
|   |-- test_signals.py
|   |-- test_conditions.py
|   |-- test_technical_analysis.py
|   |-- test_charts.py
|   |-- test_independent_validation.py
|
|-- outputs/
|   |-- charts/
|
|-- README.md
```

## 5. Technical Indicators

| Indicator | Configuration | Purpose |
|---|---|---|
| SMA | 20 days | Identifies average price trends |
| EMA | 12, 20, 26 days | Gives more weight to recent prices |
| RSI | 14 periods | Measures price momentum |
| MACD | 12, 26, 9 | Identifies momentum and trend changes |
| Historical Volatility | 20-period window | Measures annualized historical price fluctuations |

### RSI Interpretation

- RSI above 70: Overbought
- RSI below 30: Oversold
- RSI between 30 and 70: Normal range

### MACD Interpretation

- MACD above signal line: Bullish indication
- MACD below signal line: Bearish indication

## 6. API Integration

The agent retrieves historical stock data from Module 2.

Module 2 API:

`http://127.0.0.1:8001`

Technical Analysis Agent API:

`http://127.0.0.1:8002`

### Run the application

Activate the virtual environment:

```bash
.venv\Scripts\activate
```

Start the server:

```bash
python -m uvicorn app.main:app --reload --port 8002
```

### API Documentation

Open:

`http://127.0.0.1:8002/docs`

### Technical Analysis Endpoint

`POST /api/technical-analysis`

Example request:

```json
{
  "symbol": "INFY",
  "market": "NSE",
  "period": "1Y"
}
```

The response includes:

- Latest technical indicator values
- Individual technical signals
- Overall technical signal
- Trend classification
- Detected technical conditions
- Plain-language explanations
- Data quality and source metadata
- Analysis status

## 7. Chart Generation

The chart service generates four visualizations:

1. Stock price with SMA and EMA
2. RSI chart
3. MACD chart
4. Historical volatility chart

Generated charts are saved in:

`outputs/charts/`

## 8. Data Validation

The agent preserves Module 2 validation information and independently validates received historical records.

Checks include:

- Required OHLCV columns
- Valid trading dates
- Missing and non-numeric values
- Infinite values
- Duplicate trading dates
- Chronological sorting
- Positive stock prices
- High-Low price consistency
- Open and Close within the High-Low range
- Nonnegative trading volume
- Sufficient historical records for analysis

The agent rejects invalid or unusable data instead of estimating or inventing missing values.

## 9. Testing

Run all automated tests:

```bash
python -m pytest -v
```

Run indicator tests:

```bash
python -m pytest tests/test_indicators.py -v
```

## 10. Project Integration

The Technical Analysis Agent is designed as an independent component of MarketAI.

It exposes a structured FastAPI response that can be consumed by the Supervisor Agent as part of the overall stock research workflow.

## 11. Disclaimer

Technical indicators and generated signals describe historical market behaviour. They do not guarantee future price movements or investment returns.
