import feedparser
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime
import os
import json

# Initialize VADER sentiment analyzer
# VADER is specifically designed for financial and social media text
analyzer = SentimentIntensityAnalyzer()

# Map stock symbols to company names for better news search
STOCK_NAMES = {
    "RELIANCE.NS": "Reliance Industries",
    "TCS.NS": "TCS Tata Consultancy",
    "INFY.NS": "Infosys",
    "HDFCBANK.NS": "HDFC Bank",
    "ICICIBANK.NS": "ICICI Bank",
    "HINDUNILVR.NS": "Hindustan Unilever",
    "SBIN.NS": "State Bank India SBI",
    "BHARTIARTL.NS": "Bharti Airtel",
    "ITC.NS": "ITC Limited",
    "KOTAKBANK.NS": "Kotak Mahindra Bank"
}

def fetch_news(symbol):
    """
    Fetch latest news headlines from Google News RSS
    No API key needed — completely free
    """
    company_name = STOCK_NAMES.get(symbol, symbol)
    
    # Google News RSS URL
    query = company_name.replace(" ", "+")
    url = f"https://news.google.com/rss/search?q={query}+stock&hl=en-IN&gl=IN&ceid=IN:en"
    
    feed = feedparser.parse(url)
    
    headlines = []
    for entry in feed.entries[:10]:  # Get top 10 headlines
        headlines.append({
            "title": entry.title,
            "published": entry.get("published", ""),
            "link": entry.get("link", "")
        })
    
    return headlines

def analyze_sentiment(symbol):
    """
    Fetch news and analyze sentiment for a stock
    """
    print(f"Analyzing sentiment for {symbol}...")
    
    headlines = fetch_news(symbol)
    
    if not headlines:
        return {
            "symbol": symbol,
            "sentiment_score": 0,
            "sentiment_label": "NEUTRAL",
            "headlines_analyzed": 0,
            "message": "No news found"
        }
    
    scores = []
    analyzed_headlines = []
    
    for item in headlines:
        # VADER returns scores between -1 (negative) and +1 (positive)
        score = analyzer.polarity_scores(item["title"])
        compound = score["compound"]  # Overall score
        scores.append(compound)
        
        # Label each headline
        if compound >= 0.05:
            label = "POSITIVE"
        elif compound <= -0.05:
            label = "NEGATIVE"
        else:
            label = "NEUTRAL"
        
        analyzed_headlines.append({
            "headline": item["title"],
            "sentiment": label,
            "score": round(compound, 4)
        })
    
    # Average sentiment across all headlines
    avg_score = sum(scores) / len(scores)
    
    # Overall label
    if avg_score >= 0.05:
        overall_label = "POSITIVE"
        recommendation = "Bullish signal — positive news sentiment"
    elif avg_score <= -0.05:
        overall_label = "NEGATIVE"
        recommendation = "Bearish signal — negative news sentiment"
    else:
        overall_label = "NEUTRAL"
        recommendation = "Neutral — no strong sentiment signal"
    
    return {
        "symbol": symbol,
        "company": STOCK_NAMES.get(symbol, symbol),
        "sentiment_score": round(avg_score, 4),
        "sentiment_label": overall_label,
        "recommendation": recommendation,
        "headlines_analyzed": len(headlines),
        "headlines": analyzed_headlines
    }

if __name__ == "__main__":
    STOCKS = [
        "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"
    ]
    
    for stock in STOCKS:
        result = analyze_sentiment(stock)
        print(f"\n{stock} -> {result['sentiment_label']} ({result['sentiment_score']})")
        print(f"Recommendation: {result['recommendation']}")
        print(f"Headlines analyzed: {result['headlines_analyzed']}")
        print("-" * 50)