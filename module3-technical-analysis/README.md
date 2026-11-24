

\# MarketAI – Technical Analysis Agent



\## 1. Overview



The Technical Analysis Agent is a component of the MarketAI project. It analyzes historical stock market data using technical indicators, generates trading signals, identifies technical conditions, and creates visual charts.



It retrieves actual historical stock data from Module 2 through a REST API.



\## 2. Features



\- Fetches historical stock data from Module 2.

\- Calculates Simple Moving Average (SMA).

\- Calculates Exponential Moving Average (EMA).

\- Calculates Relative Strength Index (RSI).

\- Calculates Moving Average Convergence Divergence (MACD).

\- Calculates annualized historical volatility.

\- Generates bullish, bearish, and neutral signals.

\- Detects technical events and crossover conditions.

\- Generates four technical analysis charts.

\- Preserves data validation and provider metadata.

\- Exposes analysis through a FastAPI endpoint.

\- Uses Pydantic models for structured request and response validation.



\## 3. Technology Stack



\- Python 3.13

\- FastAPI

\- Pandas

\- NumPy

\- Matplotlib

\- TA

\- Pydantic

\- Requests

\- Pytest

\- Uvicorn



\## 4. Project Structure



```text

module3-technical-analysis/

│

├── app/

│   ├── main.py

│   │

│   ├── models/

│   │   └── technical\_analysis.py

│   │

│   ├── services/

│   │   ├── indicators.py

│   │   ├── market\_data\_client.py

│   │   ├── signals.py

│   │   ├── conditions.py

│   │   ├── technical\_analysis.py

│   │   └── charts.py

│

├── tests/

│   ├── test\_api.py

│   ├── test\_indicators.py

│   ├── test\_real\_data.py

│   ├── test\_signals.py

│   ├── test\_conditions.py

│   ├── test\_technical\_analysis.py

│   ├── test\_charts.py

│   └── test\_independent\_validation.py

│

├── outputs/

│   └── charts/

│

└── README.md

```



\## 5. Technical Indicators



| Indicator | Purpose |

|---|---|

| SMA | Identifies average price trends |

| EMA | Gives more weight to recent prices |

| RSI | Measures price momentum |

| MACD | Identifies momentum and trend changes |

| Historical Volatility | Measures historical price fluctuations |



\## 6. API Integration



The agent retrieves historical stock data from Module 2.



Module 2 API:

`http://127.0.0.1:8001`



Module 3 API:

`http://127.0.0.1:8002`



\### Run the application



Activate the virtual environment and start the server:



```bash

.venv\\Scripts\\activate

python -m uvicorn app.main:app --reload --port 8002

```



\### API Documentation



Open:



`http://127.0.0.1:8002/docs`



\### Technical Analysis Endpoint



`POST /api/technical-analysis`



Example request:



```json

{

&nbsp; "symbol": "INFY",

&nbsp; "market": "NSE",

&nbsp; "period": "1Y"

}

```



The response includes:

\- Latest technical indicators

\- Individual and overall signals

\- Detected technical conditions

\- Data quality and source metadata

\- Analysis status



\## 7. Chart Generation



The chart service generates four visualizations:



1\. Stock price with SMA and EMA

2\. RSI chart

3\. MACD chart

4\. Historical volatility chart



Generated charts are saved in:



`outputs/charts/`



\## 8. Testing



Run all automated tests:



```bash

python -m pytest -v

```



Run indicator tests:



```bash

python -m pytest tests/test\_indicators.py -v

```



\## 9. Data Validation



The agent preserves Module 2 validation information and checks historical records for:

\- Missing values

\- Invalid dates

\- Non-numeric OHLCV values

\- Insufficient historical records

\- Unusable data returned by Module 2



\## 10. Project Integration



The Technical Analysis Agent is designed as an independent component of MarketAI.



It can be integrated with the Module 4 Supervisor Agent when the supervisor workflow is developed.



\## 11. Disclaimer



Technical indicators and generated signals describe historical market behaviour. They do not guarantee future price movements or investment returns.



