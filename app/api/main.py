from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.models.volatility import predict_volatility, train_model
from app.models.anomaly import detect_anomalies
from app.models.sentiment import analyze_sentiment

app = FastAPI(
    title="Financial Risk Intelligence API",
    description="Real-time stock volatility prediction and anomaly detection",
    version="1.0.0"
)

# Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

STOCKS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "KOTAKBANK.NS"
]

@app.get("/")
def root():
    return {
        "message": "Financial Risk Intelligence API",
        "version": "1.0.0",
        "endpoints": [
            "/predict/volatility/{symbol}",
            "/detect/anomaly/{symbol}",
            "/stocks/summary"
        ]
    }

@app.get("/predict/volatility/{symbol}")
def get_volatility(symbol: str):
    """
    Predict tomorrow's volatility for a given stock symbol
    Example: /predict/volatility/TCS.NS
    """
    try:
        symbol = symbol.upper()
        if symbol not in STOCKS:
            raise HTTPException(
                status_code=404,
                detail=f"Symbol {symbol} not found. Available: {STOCKS}"
            )
        
        prediction = predict_volatility(symbol)
        
        # Interpret the volatility level
        if prediction < 0.01:
            risk_level = "LOW"
        elif prediction < 0.02:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"
        
        return {
            "symbol": symbol,
            "predicted_volatility": prediction,
            "risk_level": risk_level,
            "interpretation": f"{symbol} is expected to move ~{round(prediction*100, 2)}% tomorrow"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/detect/anomaly/{symbol}")
def get_anomaly(symbol: str):
    """
    Detect if today's trading is anomalous for a given stock
    Example: /detect/anomaly/RELIANCE.NS
    """
    try:
        symbol = symbol.upper()
        if symbol not in STOCKS:
            raise HTTPException(
                status_code=404,
                detail=f"Symbol {symbol} not found. Available: {STOCKS}"
            )
        
        result = detect_anomalies(symbol)
        result["is_anomaly"] = bool(result["is_anomaly"])
        
        if result["is_anomaly"]:
            result["alert"] = "UNUSUAL trading activity detected!"
        else:
            result["alert"] = "Normal trading activity"
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stocks/summary")
def get_summary():
    """
    Get volatility and anomaly status for all tracked stocks
    """
    summary = []
    
    for symbol in STOCKS:
        try:
            volatility = predict_volatility(symbol)
            anomaly = detect_anomalies(symbol)
            
            if volatility < 0.01:
                risk_level = "LOW"
            elif volatility < 0.02:
                risk_level = "MEDIUM"
            else:
                risk_level = "HIGH"
            
            summary.append({
                "symbol": symbol,
                "predicted_volatility": volatility,
                "risk_level": risk_level,
                "is_anomaly": bool(anomaly["is_anomaly"]),
                "anomaly_score": anomaly["anomaly_score"]
            })
        
        except Exception as e:
            summary.append({
                "symbol": symbol,
                "error": str(e)
            })
@app.get("/news/sentiment/{symbol}")
def get_sentiment(symbol: str):
    """
    Get news sentiment for a stock based on latest headlines
    Example: /news/sentiment/TCS.NS
    """
    try:
        symbol = symbol.upper()
        if symbol not in STOCKS:
            raise HTTPException(
                status_code=404,
                detail=f"Symbol {symbol} not found. Available: {STOCKS}"
            )
        
        result = analyze_sentiment(symbol)
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))    
    return {"stocks": summary, "total": len(summary)}