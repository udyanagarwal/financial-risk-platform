import numpy as np
import pandas as pd
from dotenv import load_dotenv
import os
import sys

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app.db import get_engine

load_dotenv()

def load_returns():
    """
    Load all stock data and calculate daily returns matrix
    """
    engine = get_engine()
    query = "SELECT date, close, symbol FROM stock_prices ORDER BY date"
    df = pd.read_sql(query, engine)
    
    if df.empty:
        raise ValueError("No stock price data found in database. Run fetch_data pipeline first.")
    
    # Pivot table — rows=dates, columns=stocks, values=close price
    pivot = df.pivot_table(index='date', columns='symbol', values='close')
    
    # Calculate daily returns for each stock
    returns = pivot.pct_change().dropna()
    
    return returns

def monte_carlo_simulation(symbols, weights, investment=100000, days=30, simulations=10000):
    """
    Run Monte Carlo simulation for a portfolio
    
    Parameters:
    - symbols: list of stock symbols e.g. ["TCS.NS", "INFY.NS"]
    - weights: allocation e.g. [0.5, 0.5] means 50% each
    - investment: amount in INR (default 1 lakh)
    - days: forecast horizon in days (default 30)
    - simulations: number of scenarios to simulate (default 10,000)
    """
    
    # Validate weights sum to 1
    weights = np.array(weights, dtype=float)
    if weights.sum() == 0:
        raise ValueError("Sum of weights cannot be 0")
    weights = weights / weights.sum()
    
    # Load historical returns
    all_returns = load_returns()
    
    # Filter only requested symbols
    available = [s for s in symbols if s in all_returns.columns]
    if not available:
        raise ValueError(f"No valid symbols from {symbols} found in database. Available: {list(all_returns.columns)}")
    
    returns = all_returns[available]
    
    # Calculate mean returns and covariance matrix
    mean_returns = returns.mean()
    cov_matrix = returns.cov()
    
    print(f"Running {simulations:,} Monte Carlo simulations...")
    print(f"Portfolio: {dict(zip(available, weights[:len(available)]))}")
    print(f"Investment: INR {investment:,} | Horizon: {days} days")
    
    # Generate random daily returns based on historical patterns using multivariate normal
    # Shape: (simulations, days, num_stocks)
    # Using numpy vectorization for lightning fast simulation
    num_stocks = len(available)
    sub_weights = weights[:num_stocks]
    sub_weights = sub_weights / sub_weights.sum()
    
    daily_returns_sim = np.random.multivariate_normal(
        mean_returns[available].values,
        cov_matrix[available].loc[available].values,
        size=(simulations, days)
    )  # shape: (simulations, days, num_stocks)
    
    # Portfolio daily returns for each simulation: (simulations, days)
    portfolio_daily = np.dot(daily_returns_sim, sub_weights)
    
    # Final value for each simulation: investment * prod(1 + daily_returns)
    final_values = investment * np.prod(1 + portfolio_daily, axis=1)
    profits_losses = final_values - investment
    
    # Value at Risk (VaR) at 95% confidence
    var_95 = float(np.percentile(profits_losses, 5))
    
    # VaR at 99% confidence
    var_99 = float(np.percentile(profits_losses, 1))
    
    # Expected Shortfall — average loss in worst 5% scenarios
    worst_5 = profits_losses[profits_losses <= var_95]
    es_95 = float(worst_5.mean()) if len(worst_5) > 0 else var_95
    
    portfolio_alloc = {s: round(float(w), 3) for s, w in zip(available, sub_weights)}
    
    results = {
        "portfolio": portfolio_alloc,
        "investment_inr": int(investment),
        "horizon_days": int(days),
        "simulations_run": int(simulations),
        "metrics": {
            "expected_value": round(float(np.mean(final_values)), 2),
            "expected_profit_loss": round(float(np.mean(profits_losses)), 2),
            "best_case": round(float(np.percentile(final_values, 95)), 2),
            "worst_case": round(float(np.percentile(final_values, 5)), 2),
            "var_95": round(var_95, 2),
            "var_99": round(var_99, 2),
            "expected_shortfall": round(es_95, 2),
            "probability_of_profit": round(float(np.mean(profits_losses > 0) * 100), 2),
            "max_gain": round(float(profits_losses.max()), 2),
            "max_loss": round(float(profits_losses.min()), 2)
        },
        "interpretation": {
            "var_95_text": f"95% chance loss won't exceed INR {abs(round(var_95, 2)):,}",
            "var_99_text": f"99% chance loss won't exceed INR {abs(round(var_99, 2)):,}",
            "profit_chance": f"{round(float(np.mean(profits_losses > 0) * 100), 2)}% probability of profit in {days} days"
        }
    }
    
    return results

if __name__ == "__main__":
    symbols = ["TCS.NS", "INFY.NS", "HDFCBANK.NS", "RELIANCE.NS"]
    weights = [0.3, 0.3, 0.2, 0.2]
    
    result = monte_carlo_simulation(symbols, weights, investment=100000, days=30)
    print("\n--- PORTFOLIO RISK REPORT ---")
    print(f"Expected value after 30 days: INR {result['metrics']['expected_value']:,}")
    print(f"Expected P&L: INR {result['metrics']['expected_profit_loss']:,}")
    print(f"VaR (95%): {result['interpretation']['var_95_text']}")