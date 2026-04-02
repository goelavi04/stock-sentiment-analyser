import requests
import os
from dotenv import load_dotenv

load_dotenv()

HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

API_URL = API_URL = "https://router.huggingface.co/hf-inference/models/ProsusAI/finbert"
headers = {
    "Authorization": f"Bearer {HF_API_KEY}"
}

def analyse_sentiment(headline: str):
    payload = {"inputs": headline}
    
    response = requests.post(API_URL, headers=headers, json=payload)
    result = response.json()
    
    if isinstance(result, list) and len(result) > 0:
        scores = result[0]
        best = max(scores, key=lambda x: x["score"])
        return {
            "label": best["label"],
            "score": round(best["score"], 4)
        }
    else:
        print(f"Unexpected response: {result}")
        return {"label": "UNKNOWN", "score": 0.0}


if __name__ == "__main__":
    test_headlines = [
        "Apple hits record revenue in Q4",
        "Stock market crashes on recession fears",
        "Fed holds interest rates steady"
    ]
    
    for headline in test_headlines:
        result = analyse_sentiment(headline)
        print(f"Headline: {headline}")
        print(f"Sentiment: {result['label']} | Score: {result['score']}\n")