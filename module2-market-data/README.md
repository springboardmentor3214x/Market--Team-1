# Module 2 – Stock Search & Market Data Collection

FastAPI backend + React frontend that lets a user **search a company by name or ticker**, then collects
**historical OHLCV prices, company profile and financial statements**, **validates** the data, records the
**source and retrieval timestamp**, stores everything in a database and returns a clean, structured result
for the later analysis agents (Modules 3-6).

Supported markets: **NSE (.NS), BSE (.BO), NYSE, Nasdaq**.  Currency is tracked (INR for India, USD for US).
Data source: **Yahoo Finance via the `yfinance` library** (free, no API key).

> Module 2 only *collects, validates and prepares* data. It does not calculate RSI/MACD, ratios, sentiment
> or reports - those belong to later modules.

## Run the backend (Windows, no `pip.exe` needed)
```
cd module2-market-data
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
venv\Scripts\python.exe -m pytest -v
venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8001
```
Open http://127.0.0.1:8001/docs to try every endpoint.

## Run the frontend
```
cd frontend
copy .env.example .env
npm install
npm run dev
```
Open http://localhost:5173

## API
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/markets` | Supported markets, currencies, analysis periods |
| GET | `/api/search?q=infosys&market=NSE` | Search by company name or ticker (market optional) |
| GET | `/api/stocks/{symbol}/overview?period=1Y&market=NSE` | Profile + validated OHLCV + financial statements (main endpoint) |
| GET | `/api/stocks/{symbol}/history?period=1Y` | Validated OHLCV only |
| GET | `/api/stocks/{symbol}/profile` | Company profile only |
| GET | `/api/stocks/{symbol}/financials` | Income statement, balance sheet, cash flow |
| GET | `/api/stocks/{symbol}/fetch-log` | Audit trail: source + retrieval time of each download |

Periods: `1M 3M 6M 1Y 3Y 5Y` (same values as the Module 1 user preferences).
Typing `INFY` with market `NSE` becomes `INFY.NS` automatically.

## Error handling
| Situation | Response |
|---|---|
| Empty / invalid search text, bad market or period, bad ticker format | 400 with a clear message |
| Ticker on an unsupported exchange (e.g. `VOD.L`) | 400 |
| Company not found / no price data for the ticker | 404 |
| Yahoo is down or rate-limited | 502 (search falls back to the built-in list with a warning) |
| Profile or some statements unavailable | Still 200; that section says `available: false` + a warning |

## How search works
1. Built-in list of ~40 well-known companies is scored: exact ticker > exact name > prefix > contains > typo match
   (`infosis` -> Infosys). Works instantly and offline.
2. Yahoo Finance search adds all other companies.
3. Only equities on NSE/BSE/NYSE/Nasdaq are kept, duplicates removed, best matches first.

## Data validation (`app/services/validation.py`)
| Check | Action |
|---|---|
| Invalid dates / future dates | Row removed |
| Non-numeric price cells | Treated as missing |
| **Duplicate dates** | One row kept per date (the most complete one) |
| **Missing** Open/High/Low/Close | Row removed (never estimated) |
| Missing volume | Kept as `null` (flagged) |
| **Inconsistent**: High < Low, Open or Close outside High-Low, zero/negative price | Row removed |
| Negative volume | Set to `null` |
| Weekend dates, >50% one-day move, stale data (>7 days old) | Kept but **flagged as warnings** |

OHLC are **raw (unadjusted)** prices so the "inside the High-Low range" rule is checked on one price basis;
the split/dividend-adjusted price is kept separately as `adj_close`.
The result includes a report (`status`: clean / cleaned / unusable, each issue with count, sample dates, action).

## Source and timestamps
Every section returns `metadata.source`, `metadata.source_url` and `metadata.retrieved_at` (UTC).
`retrieved_at` (when we downloaded) is stored separately from each row's trading `date`.

## Database (SQLite by default, PostgreSQL by changing `DATABASE_URL`)
`companies`, `price_history` (unique per symbol+date), `financial_statements`, `data_fetch_log`.
Re-fetching updates rows instead of duplicating them.

## Tests
`pytest -v` -> 67 tests (validation rules, search, API behaviour, error cases, DB storage, Yahoo adapter).
They use a fake data provider, so they run without internet.

## Connecting to Module 1
Market/period preferences saved in Module 1 pre-fill the search page when the user is logged in
(token in `localStorage["token"]`). To protect these endpoints with login later, add
`Depends(get_current_user)` from Module 1 to the routes.

## Known limitations
- Yahoo Finance is an unofficial free source: it can be delayed, rate-limited or change format.
  `app/providers/base.py` defines an interface, so another provider (Alpha Vantage, NSE API) can be added.
- Financial statements are annual and some companies have fewer periods or missing items.
- Built-in list covers popular names only; everything else relies on Yahoo search.
