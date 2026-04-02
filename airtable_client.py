import os
from pyairtable import Api
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")

def get_table():
    api = Api(AIRTABLE_API_KEY)
    return api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)

def store_result(ticker: str, headline: str, sentiment: str, score: float):
    table = get_table()
    
    record = {
        "Ticker": ticker,
        "Headline": headline,
        "Sentiment": sentiment,
        "Score": score,
        "FetchedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    }
    
    table.create(record)
    print(f"Stored: [{sentiment}] {headline[:50]}...")


if __name__ == "__main__":
    store_result(
        ticker="AAPL",
        headline="Apple hits record revenue in Q4",
        sentiment="positive",
        score=0.9085
    )