"""Built-in list of well-known companies so search works instantly and offline,
and still works when Yahoo's search is down. Yahoo search adds everything else.

Each entry: (ticker, display name, extra search aliases, market(s))
Indian companies are expanded into both NSE (.NS) and BSE (.BO) entries.
"""

_INDIA = [
    ("RELIANCE", "Reliance Industries Limited", ["reliance industries", "ril"]),
    ("TCS", "Tata Consultancy Services Limited", ["tata consultancy services", "tata consultancy"]),
    ("INFY", "Infosys Limited", ["infosys"]),
    ("HDFCBANK", "HDFC Bank Limited", ["hdfc bank", "hdfc"]),
    ("ICICIBANK", "ICICI Bank Limited", ["icici bank", "icici"]),
    ("SBIN", "State Bank of India", ["sbi", "state bank"]),
    ("ITC", "ITC Limited", ["itc"]),
    ("WIPRO", "Wipro Limited", ["wipro"]),
    ("HCLTECH", "HCL Technologies Limited", ["hcl technologies", "hcl tech", "hcl"]),
    ("LT", "Larsen & Toubro Limited", ["larsen and toubro", "larsen toubro", "l&t"]),
    ("AXISBANK", "Axis Bank Limited", ["axis bank", "axis"]),
    ("KOTAKBANK", "Kotak Mahindra Bank Limited", ["kotak mahindra bank", "kotak bank", "kotak"]),
    ("MARUTI", "Maruti Suzuki India Limited", ["maruti suzuki", "maruti"]),
    ("SUNPHARMA", "Sun Pharmaceutical Industries Limited", ["sun pharma", "sun pharmaceutical"]),
    ("BHARTIARTL", "Bharti Airtel Limited", ["bharti airtel", "airtel"]),
    ("ASIANPAINT", "Asian Paints Limited", ["asian paints"]),
    ("BAJFINANCE", "Bajaj Finance Limited", ["bajaj finance"]),
    ("HINDUNILVR", "Hindustan Unilever Limited", ["hindustan unilever", "hul"]),
    ("TITAN", "Titan Company Limited", ["titan company", "titan"]),
    ("ULTRACEMCO", "UltraTech Cement Limited", ["ultratech cement", "ultratech"]),
]

# (ticker, name, aliases, market)
_US = [
    ("AAPL", "Apple Inc.", ["apple"], "NASDAQ"),
    ("MSFT", "Microsoft Corporation", ["microsoft"], "NASDAQ"),
    ("GOOGL", "Alphabet Inc.", ["alphabet", "google"], "NASDAQ"),
    ("AMZN", "Amazon.com, Inc.", ["amazon"], "NASDAQ"),
    ("META", "Meta Platforms, Inc.", ["meta", "facebook"], "NASDAQ"),
    ("NVDA", "NVIDIA Corporation", ["nvidia"], "NASDAQ"),
    ("TSLA", "Tesla, Inc.", ["tesla"], "NASDAQ"),
    ("NFLX", "Netflix, Inc.", ["netflix"], "NASDAQ"),
    ("INTC", "Intel Corporation", ["intel"], "NASDAQ"),
    ("JPM", "JPMorgan Chase & Co.", ["jpmorgan", "jp morgan", "jpmorgan chase"], "NYSE"),
    ("WMT", "Walmart Inc.", ["walmart"], "NYSE"),
    ("KO", "The Coca-Cola Company", ["coca cola", "coca-cola", "coke"], "NYSE"),
    ("DIS", "The Walt Disney Company", ["disney", "walt disney"], "NYSE"),
    ("BA", "The Boeing Company", ["boeing"], "NYSE"),
    ("V", "Visa Inc.", ["visa"], "NYSE"),
    ("XOM", "Exxon Mobil Corporation", ["exxon mobil", "exxon"], "NYSE"),
    ("JNJ", "Johnson & Johnson", ["johnson and johnson", "j&j"], "NYSE"),
    ("PG", "The Procter & Gamble Company", ["procter and gamble", "procter & gamble"], "NYSE"),
    ("BAC", "Bank of America Corporation", ["bank of america"], "NYSE"),
]


def _build() -> list[dict]:
    entries: list[dict] = []
    for ticker, name, aliases in _INDIA:
        for market, suffix in (("NSE", ".NS"), ("BSE", ".BO")):
            entries.append({"symbol": ticker + suffix, "ticker": ticker, "name": name,
                            "aliases": aliases, "market": market, "currency": "INR"})
    for ticker, name, aliases, market in _US:
        entries.append({"symbol": ticker, "ticker": ticker, "name": name,
                        "aliases": aliases, "market": market, "currency": "USD"})
    return entries


UNIVERSE: list[dict] = _build()
