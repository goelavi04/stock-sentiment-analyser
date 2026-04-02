import requests
import os
import re
from dotenv import load_dotenv

load_dotenv()

NEWS_API_KEY = os.getenv("NEWSAPI_KEY")

def is_english(text):
    return bool(re.match(r'^[\x00-\x7F]+$', text))

def get_stock_headlines(ticker: str):
    url = "https://newsapi.org/v2/everything"
    
    params = {
        "q": f"{ticker} stock OR shares OR earnings OR market",
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 20,
        "apiKey": NEWS_API_KEY
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if data["status"] != "ok":
        print(f"Error fetching news: {data}")
        return []
    
    headlines = []
    for article in data["articles"]:
        title = article["title"]
        if title and is_english(title):
            headlines.append(title)
    
    return headlines[:10]


if __name__ == "__main__":
    results = get_stock_headlines("AAPL")
    print(f"Found {len(results)} headlines:\n")
    for h in results:
        print("-", h)