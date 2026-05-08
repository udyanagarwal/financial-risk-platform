# Financial Risk Intelligence Platform

A production-grade financial risk analytics platform that delivers real-time ML-powered predictions for Indian NSE stocks via a live REST API.

## Live Demo
- **API:** https://financial-risk-platform-production.up.railway.app
- **Interactive Docs:** https://financial-risk-platform-production.up.railway.app/docs

## Features
- **Volatility Predictor** — Random Forest model predicting next-day stock price movement
- **Anomaly Detector** — Isolation Forest flagging unusual trading activity
- **Sentiment Analyzer** — NLP analysis of live financial news headlines using VADER
- **Portfolio Risk Scorer** — Monte Carlo simulation (10,000 scenarios) for Value-at-Risk calculation
- **Automated ETL Pipeline** — Daily data fetch from Yahoo Finance into cloud PostgreSQL

## Tech Stack
| Component | Technology |
|-----------|-----------|
| Backend API | FastAPI + Uvicorn |
| Database | PostgreSQL (Railway) |
| ML Models | Scikit-learn (Random Forest, Isolation Forest) |
| NLP | VADER Sentiment + feedparser |
| Data Pipeline | yfinance + Pandas + SQLAlchemy |
| Dashboard | Streamlit + Plotly |
| Deployment | Railway (Cloud) |
| Scheduling | Python schedule library |

## API Endpoints
| Endpoint | Description |
|----------|-------------|
| `GET /predict/volatility/{symbol}` | Predict tomorrow's volatility |
| `GET /detect/anomaly/{symbol}` | Detect unusual trading activity |
| `GET /news/sentiment/{symbol}` | Analyze live news sentiment |
| `GET /stocks/summary` | Overview of all 10 tracked stocks |
| `GET /portfolio/risk` | Monte Carlo portfolio risk simulation |

## Example API Response
```json
{
  "symbol": "TCS.NS",
  "predicted_volatility": 0.01394,
  "risk_level": "MEDIUM",
  "interpretation": "TCS.NS is expected to move ~1.39% tomorrow"
}
```

## Tracked Stocks
Reliance, TCS, Infosys, HDFC Bank, ICICI Bank, HUL, SBI, Bharti Airtel, ITC, Kotak Bank

## Architecture
```
Yahoo Finance API → ETL Pipeline → PostgreSQL Database → ML Models → FastAPI → Streamlit Dashboard
```

## How to Run Locally
```bash
git clone https://github.com/udyanagarwal/financial-risk-platform.git
cd financial-risk-platform
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app/pipeline/fetch_data.py
python app/models/volatility.py
python app/models/anomaly.py
uvicorn app.api.main:app --reload
streamlit run dashboard.py
```

## Project Structure
```
financial-risk-platform/
├── app/
│   ├── api/main.py
│   ├── models/
│   │   ├── volatility.py
│   │   ├── anomaly.py
│   │   ├── sentiment.py
│   │   └── portfolio.py
│   └── pipeline/fetch_data.py
├── dashboard.py
├── scheduler.py
├── Procfile
└── requirements.txt
```

## Built By
Udyan Agarwal — Computer Engineering, Bharati Vidyapeeth College of Engineering, Pune