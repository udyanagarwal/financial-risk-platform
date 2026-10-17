import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from dotenv import load_dotenv
import os
import sys

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.db import get_engine

load_dotenv()

# Page config
st.set_page_config(
    page_title="Financial Risk Intelligence Platform",
    page_icon="📈",
    layout="wide"
)

# Sidebar
st.sidebar.title("⚙️ Controls")

default_api_url = os.getenv("API_URL")
if not default_api_url:
    try:
        if "API_URL" in st.secrets:
            default_api_url = st.secrets["API_URL"]
    except Exception:
        pass
if not default_api_url:
    default_api_url = "http://127.0.0.1:8000"

API_URL = st.sidebar.text_input("FastAPI Backend URL", value=default_api_url).rstrip("/")

STOCKS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "KOTAKBANK.NS"
]
selected_stock = st.sidebar.selectbox("Select Stock", STOCKS)

# Database connection
@st.cache_resource
def get_db():
    return get_engine()

engine = get_db()

# Title
st.title("📈 Financial Risk Intelligence Platform")
st.markdown("Real-time stock analytics powered by ML — Volatility, Anomaly Detection, Sentiment & Portfolio Risk")
st.divider()

# ── SECTION 1: Stock Price Chart ──
st.subheader(f"📊 Price History — {selected_stock}")

try:
    query = f"SELECT date, close, volume FROM stock_prices WHERE symbol = '{selected_stock}' ORDER BY date"
    df = pd.read_sql(query, engine)
    
    if not df.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['close'],
            mode='lines',
            name='Close Price',
            line=dict(color='#00d4ff', width=2)
        ))
        fig.update_layout(
            template='plotly_dark',
            height=350,
            margin=dict(l=0, r=0, t=30, b=0),
            xaxis_title="Date",
            yaxis_title="Price (INR)"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(f"No price history found for {selected_stock}. Run fetch_data.py to populate.")
except Exception as e:
    st.error(f"Could not load price history: {e}")

# ── SECTION 2: ML Predictions ──
st.subheader("🤖 ML Predictions")
col1, col2, col3 = st.columns(3)

with col1:
    with st.spinner("Getting volatility..."):
        try:
            resp = requests.get(f"{API_URL}/predict/volatility/{selected_stock}", timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                st.metric(
                    label="Predicted Volatility",
                    value=f"{data['predicted_volatility']*100:.2f}%"
                )
                risk_color = {"LOW": "green", "MEDIUM": "orange", "HIGH": "red"}
                st.markdown(f"Risk Level: **:{risk_color.get(data['risk_level'], 'blue')}[{data['risk_level']}]**")
                st.caption(data['interpretation'])
            else:
                st.error(f"API Error ({resp.status_code}): {resp.text}")
        except Exception as e:
            st.error(f"FastAPI not reachable at {API_URL}")

with col2:
    with st.spinner("Checking anomaly..."):
        try:
            resp = requests.get(f"{API_URL}/detect/anomaly/{selected_stock}", timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                if data['is_anomaly']:
                    st.metric(label="Anomaly Status", value="UNUSUAL")
                    st.error(data['alert'])
                else:
                    st.metric(label="Anomaly Status", value="NORMAL")
                    st.success(data['alert'])
                st.caption(f"Score: {data['anomaly_score']}")
            else:
                st.error(f"API Error ({resp.status_code}): {resp.text}")
        except Exception as e:
            st.error(f"FastAPI not reachable at {API_URL}")

with col3:
    with st.spinner("Analyzing sentiment..."):
        try:
            resp = requests.get(f"{API_URL}/news/sentiment/{selected_stock}", timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                sentiment_emoji = {"POSITIVE": "🟢", "NEGATIVE": "🔴", "NEUTRAL": "🟡"}
                st.metric(
                    label="News Sentiment",
                    value=f"{sentiment_emoji.get(data['sentiment_label'], '')} {data['sentiment_label']}"
                )
                st.caption(data['recommendation'])
                st.caption(f"{data['headlines_analyzed']} headlines analyzed")
            else:
                st.error(f"API Error ({resp.status_code}): {resp.text}")
        except Exception as e:
            st.error(f"FastAPI not reachable at {API_URL}")

st.divider()

# ── SECTION 3: Market Overview ──
st.subheader("🌍 Market Overview & Risk Distribution")

col_left, col_right = st.columns(2)

with col_left:
    with st.spinner("Loading market overview..."):
        try:
            query = """
                SELECT symbol,
                       MAX(close) as max_price,
                       MIN(close) as min_price,
                       AVG(close) as avg_price,
                       MAX(date) as latest_date
                FROM stock_prices
                GROUP BY symbol
                ORDER BY symbol
            """
            overview_df = pd.read_sql(query, engine)
            overview_df = overview_df.round(2)
            st.dataframe(overview_df, use_container_width=True, height=260)

            fig_bar = px.bar(
                overview_df,
                x='symbol',
                y='avg_price',
                title="Average Stock Price (1 Year)",
                template="plotly_dark",
                color='avg_price',
                color_continuous_scale='blues'
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        except Exception as e:
            st.error(f"Could not load market overview: {e}")

with col_right:
    with st.spinner("Loading risk distribution across stocks..."):
        try:
            resp = requests.get(f"{API_URL}/stocks/summary", timeout=30)
            if resp.status_code == 200:
                summary_data = resp.json().get("stocks", [])
                summary_df = pd.DataFrame(summary_data)
                
                if not summary_df.empty and "risk_level" in summary_df.columns:
                    display_cols = [c for c in ['symbol', 'predicted_volatility', 'risk_level', 'is_anomaly'] if c in summary_df.columns]
                    st.dataframe(summary_df[display_cols], use_container_width=True, height=260)
                    
                    risk_counts = summary_df['risk_level'].value_counts()
                    fig_pie = px.pie(
                        values=risk_counts.values,
                        names=risk_counts.index,
                        title="Risk Level Distribution",
                        color=risk_counts.index,
                        color_discrete_map={"LOW": "#2ecc71", "MEDIUM": "#f39c12", "HIGH": "#e74c3c"},
                        template="plotly_dark"
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info("No risk summary data available from API.")
            else:
                st.warning("Could not fetch risk summary from API.")
        except Exception as e:
            st.error(f"Could not load risk distribution: {e}")

st.divider()

# ── SECTION 4: Portfolio Risk Simulator ──
st.subheader("💼 Portfolio Risk Simulator")
st.markdown("Simulate 10,000 future scenarios for your portfolio using Monte Carlo")

col_port1, col_port2 = st.columns(2)

with col_port1:
    selected_stocks = st.multiselect(
        "Select stocks for portfolio",
        STOCKS,
        default=["TCS.NS", "INFY.NS", "HDFCBANK.NS", "RELIANCE.NS"]
    )
    investment = st.number_input("Investment Amount (INR)", value=100000, step=10000)
    days = st.slider("Forecast Horizon (days)", min_value=7, max_value=90, value=30)

with col_port2:
    weights = []
    if selected_stocks:
        st.markdown("**Set Portfolio Weights**")
        for stock in selected_stocks:
            w = st.slider(f"{stock}", 0.0, 1.0, 1.0/len(selected_stocks), 0.05)
            weights.append(w)
        total_weight = sum(weights)
        st.caption(f"Total weight: {total_weight:.2f} (will be normalized to 1.0)")

if st.button("Run Monte Carlo Simulation", type="primary"):
    if not selected_stocks:
        st.warning("Please select at least one stock")
    else:
        with st.spinner("Running 10,000 simulations..."):
            try:
                symbols_str = ",".join(selected_stocks)
                weights_str = ",".join([str(w) for w in weights])
                
                resp = requests.get(
                    f"{API_URL}/portfolio/risk",
                    params={
                        "symbols": symbols_str,
                        "weights": weights_str,
                        "investment": investment,
                        "days": days,
                        "simulations": 10000
                    },
                    timeout=120
                )
                
                if resp.status_code == 200:
                    result = resp.json()
                    metrics = result['metrics']

                    # Display metrics
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Expected Value", f"₹{metrics['expected_value']:,.0f}")
                    c2.metric("Expected P&L", f"₹{metrics['expected_profit_loss']:,.0f}")
                    c3.metric("Best Case", f"₹{metrics['best_case']:,.0f}")
                    c4.metric("Worst Case", f"₹{metrics['worst_case']:,.0f}")

                    c5, c6, c7 = st.columns(3)
                    c5.metric("VaR (95%)", f"₹{abs(metrics['var_95']):,.0f}")
                    c6.metric("VaR (99%)", f"₹{abs(metrics['var_99']):,.0f}")
                    c7.metric("Profit Probability", f"{metrics['probability_of_profit']}%")

                    # Interpretation
                    st.info(result['interpretation']['var_95_text'])
                    st.info(result['interpretation']['profit_chance'])
                else:
                    st.error(f"Simulation failed ({resp.status_code}): {resp.text}")

            except Exception as e:
                st.error(f"Simulation failed: {e}")

st.divider()
st.caption("Financial Risk Intelligence Platform | Data from Yahoo Finance")