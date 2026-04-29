import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DB_URL)

def load_returns():
    """
    Load all stock data and calculate daily returns matrix
    """
    query = "SELECT date, close, symbol FROM stock_prices ORDER BY date"
    df = pd.read_sql(query, engine)
    
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
    weights = np.array(weights)
    weights = weights / weights.sum()
    
    # Load historical returns
    all_returns = load_returns()
    
    # Filter only requested symbols
    available = [s for s in symbols if s in all_returns.columns]
    if not available:
        raise ValueError("No valid symbols found in database")
    
    returns = all_returns[available]
    
    # Calculate mean returns and covariance matrix
    # Mean return = average daily return for each stock
    mean_returns = returns.mean()
    
    # Covariance matrix = how stocks move together
    # If TCS and Infosys both drop when IT sector is down,
    # they have high covariance — your portfolio is more risky
    cov_matrix = returns.cov()
    
    print(f"Running {simulations:,} Monte Carlo simulations...")
    print(f"Portfolio: {dict(zip(available, weights))}")
    print(f"Investment: INR {investment:,} | Horizon: {days} days")
    
    # Store final portfolio values from each simulation
    simulation_results = []
    
    for _ in range(simulations):
        # Generate random daily returns based on historical patterns
        # We use Cholesky decomposition to maintain correlation between stocks
        daily_returns = np.random.multivariate_normal(
            mean_returns[available],
            cov_matrix[available].loc[available],
            days
        )
        
        # Calculate portfolio return each day
        # Multiply each stock's return by its weight
        portfolio_returns = daily_returns.dot(weights[:len(available)])
        
        # Calculate portfolio value over time
        price_path = investment * np.cumprod(1 + portfolio_returns)
        
        # Store final value after 30 days
        simulation_results.append(price_path[-1])
    
    simulation_results = np.array(simulation_results)
    
    # Calculate risk metrics
    final_values = simulation_results
    profits_losses = final_values - investment
    
    # Value at Risk (VaR) at 95% confidence
    # This means 95% of the time, loss won't exceed this amount
    var_95 = np.percentile(profits_losses, 5)
    
    # VaR at 99% confidence
    var_99 = np.percentile(profits_losses, 1)
    
    # Expected Shortfall — average loss in worst 5% scenarios
    es_95 = profits_losses[profits_losses <= var_95].mean()
    
    results = {
        "portfolio": dict(zip(available, [round(w, 3) for w in weights[:len(available)]])),
        "investment_inr": investment,
        "horizon_days": days,
        "simulations_run": simulations,
        "metrics": {
            "expected_value": round(float(np.mean(final_values)), 2),
            "expected_profit_loss": round(float(np.mean(profits_losses)), 2),
            "best_case": round(float(np.percentile(final_values, 95)), 2),
            "worst_case": round(float(np.percentile(final_values, 5)), 2),
            "var_95": round(float(var_95), 2),
            "var_99": round(float(var_99), 2),
            "expected_shortfall": round(float(es_95), 2),
            "probability_of_profit": round(float(np.mean(profits_losses > 0) * 100), 2),
            "max_gain": round(float(profits_losses.max()), 2),
            "max_loss": round(float(profits_losses.min()), 2)
        },
        "interpretation": {
            "var_95_text": f"95% chance loss won't exceed INR {abs(round(float(var_95), 2)):,}",
            "var_99_text": f"99% chance loss won't exceed INR {abs(round(float(var_99), 2)):,}",
            "profit_chance": f"{round(float(np.mean(profits_losses > 0) * 100), 2)}% probability of profit in {days} days"
        }
    }
    
    return results

if __name__ == "__main__":
    # Test with a sample portfolio
    symbols = ["TCS.NS", "INFY.NS", "HDFCBANK.NS", "RELIANCE.NS"]
    weights = [0.3, 0.3, 0.2, 0.2]  # 30% TCS, 30% Infosys, 20% HDFC, 20% Reliance
    
    result = monte_carlo_simulation(symbols, weights, investment=100000, days=30)
    
    print("\n--- PORTFOLIO RISK REPORT ---")
    print(f"Expected value after 30 days: INR {result['metrics']['expected_value']:,}")
    print(f"Expected P&L: INR {result['metrics']['expected_profit_loss']:,}")
    print(f"Best case (95th percentile): INR {result['metrics']['best_case']:,}")
    print(f"Worst case (5th percentile): INR {result['metrics']['worst_case']:,}")
    print(f"\nRisk Metrics:")
    print(f"VaR (95%): {result['interpretation']['var_95_text']}")
    print(f"VaR (99%): {result['interpretation']['var_99_text']}")
    print(f"Profit probability: {result['interpretation']['profit_chance']}")