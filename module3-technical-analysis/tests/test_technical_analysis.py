
from app.services.technical_analysis import run_technical_analysis


companies = [
    ("AAPL", "NASDAQ"),
    ("MSFT", "NASDAQ"),
    ("GOOGL", "NASDAQ"),
    ("AMZN", "NASDAQ"),
    ("META", "NASDAQ"),
    ("NVDA", "NASDAQ"),
    ("TSLA", "NASDAQ"),
    ("NFLX", "NASDAQ"),
    ("INTC", "NASDAQ"),
    ("JPM", "NYSE"),
    ("WMT", "NYSE"),
    ("KO", "NYSE"),
    ("DIS", "NYSE"),
    ("BA", "NYSE"),
    ("V", "NYSE"),
    ("XOM", "NYSE"),
    ("JNJ", "NYSE"),
    ("PG", "NYSE"),
    ("BAC", "NYSE"),
]

successful = []
failed = []

for symbol, market in companies:

    print(f"\nAnalyzing {symbol} ({market})")
    print("-" * 45)

    try:
        result = run_technical_analysis(
            symbol=symbol,
            market=market,
            period="1Y"
        )

        print("Status:", result["analysis_status"])
        print("Latest price:", result["indicators"]["close"])
        print("RSI:", result["indicators"]["rsi_14"])
        print("Overall signal:", result["signals"]["overall_signal"])
        print("Records:", result["records_analyzed"])

        successful.append(symbol)

    except Exception as error:
        print("Failed:", error)
        failed.append(symbol)


print("\n========== FOREIGN COMPANY TEST REPORT ==========")
print("Total companies:", len(companies))
print("Successful:", len(successful))
print("Failed:", len(failed))
print("Successful:", successful)
print("Failed:", failed)
