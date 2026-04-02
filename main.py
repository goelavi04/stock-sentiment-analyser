from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pyairtable import Api
from dotenv import load_dotenv
import os
import requests
from datetime import datetime

load_dotenv()

HF_API_KEY       = os.getenv("HUGGINGFACE_API_KEY")
NEWS_API_KEY     = os.getenv("NEWSAPI_KEY")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME       = os.getenv("AIRTABLE_TABLE_NAME", "Headlines")

airtable = Api(AIRTABLE_API_KEY)
table    = airtable.table(AIRTABLE_BASE_ID, TABLE_NAME)

HF_MODEL_URL = "https://router.huggingface.co/hf-inference/models/ProsusAI/finbert"
HF_HEADERS   = {"Authorization": f"Bearer {HF_API_KEY}"}

app = FastAPI(title="Stock Sentiment Analyser")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

class TickerRequest(BaseModel):
    ticker: str

def fetch_headlines(ticker: str):
    url = "https://newsapi.org/v2/everything"
    params = {
        "q":        f"{ticker} stock OR shares OR earnings",
        "language": "en",
        "sortBy":   "publishedAt",
        "pageSize": 20,
        "apiKey":   NEWS_API_KEY
    }
    response = requests.get(url, params=params, timeout=10)
    data     = response.json()

    if data.get("status") != "ok":
        return []

    import re
    def is_english(text):
        return bool(re.match(r'^[\x00-\x7F]+$', text))

    headlines = []
    for article in data.get("articles", []):
        title = article.get("title")
        if title and is_english(title):
            headlines.append({
                "title":       title,
                "publishedAt": article["publishedAt"]
            })

    return headlines[:10]

def analyse_sentiment(text: str):
    try:
        response = requests.post(
            HF_MODEL_URL,
            headers=HF_HEADERS,
            json={"inputs": text},
            timeout=30
        )
        result = response.json()

        if isinstance(result, list) and len(result) > 0:
            scores = result[0]
            best   = max(scores, key=lambda x: x["score"])
            return best["label"], round(best["score"], 4)

        return "neutral", 0.5

    except Exception:
        return "neutral", 0.5

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    with open("templates/index.html", encoding="utf-8") as f:
        return f.read()

@app.post("/analyse")
async def analyse_ticker(req: TickerRequest):
    ticker = req.ticker.upper().strip()

    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker required")

    headlines = fetch_headlines(ticker)

    if not headlines:
        raise HTTPException(status_code=404, detail=f"No headlines found for {ticker}")

    results = []

    for item in headlines:
        headline  = item["title"]
        sentiment, score = analyse_sentiment(headline)

        table.create({
            "Ticker":    ticker,
            "Headline":  headline,
            "Sentiment": sentiment,
            "Score":     score,
            "FetchedAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z")
        })

        results.append({
            "headline":  headline,
            "sentiment": sentiment,
            "score":     score,
            "date":      item["publishedAt"][:10]
        })

    pos   = sum(1 for r in results if r["sentiment"] == "positive")
    neg   = sum(1 for r in results if r["sentiment"] == "negative")
    neu   = sum(1 for r in results if r["sentiment"] == "neutral")
    total = len(results)

    overall = "positive" if pos > neg else "negative" if neg > pos else "neutral"

    return {
        "ticker":  ticker,
        "total":   total,
        "overall": overall,
        "counts":  {"positive": pos, "negative": neg, "neutral": neu},
        "results": results
    }

@app.get("/history/{ticker}")
async def get_history(ticker: str):
    records = table.all(formula="{Ticker}=" + repr(ticker.upper()))
    return [r["fields"] for r in records]

@app.get("/tickers")
async def get_tickers():
    records = table.all()
    tickers = list(set(r["fields"].get("Ticker", "") for r in records))
    return tickers

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)