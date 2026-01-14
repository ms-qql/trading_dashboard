import numpy as np
import pandas as pd
from scipy.stats import norm

def calculate_metrics(returns, risk_free_rate=0.0):
    """
    Calculates performance metrics for a series of returns.
    Assumes daily returns (or whatever the interval is, we'll annualize based on 252 assumption for now, 
    though user said 8h interval, so 3 bars per day? -> 252 * 3 = 756?)
    
    User said "date with 8h interval". standard market year is ~252 days.
    If 8h interval (3 per day), annual_factor should be 252 * 3 = 756.
    Let's assume 3 periods per day.
    """
    
    # Determine annualization factor based on data frequency roughly
    # If we don't know for sure, we can guess or stick to standard.
    # Let's standardize to the count of periods.
    # If user didn't specify, standard practice for crypto/24h assets is 365, for stocks 252.
    # With 8h interval = 3 per day. 
    # Let's use 365 * 3 = 1095 for crypto/24h or 252 * 3 = 756 for TradFi using 8h bars?
    # Let's err on side of "Annualized" means scaling up mean and std.
    # We'll default to 252*3 (approx 756) if it looks like intraday, or just 252 if daily.
    # For robust code, let's just use 252 * 3 = 756 as a default for "8h" data.
    
    ANNUAL_FACTOR = 756 
    
    total_return = (1 + returns).prod() - 1
    n_years = len(returns) / ANNUAL_FACTOR
    cagr = (1 + total_return) ** (1 / n_years) - 1 if n_years > 0 else 0
    
    mean_return = returns.mean() * ANNUAL_FACTOR
    volatility = returns.std() * np.sqrt(ANNUAL_FACTOR)
    
    sharpe = (mean_return - risk_free_rate) / volatility if volatility != 0 else 0
    
    # Sortino
    downside_returns = returns[returns < 0]
    downside_std = downside_returns.std() * np.sqrt(ANNUAL_FACTOR)
    sortino = (mean_return - risk_free_rate) / downside_std if downside_std != 0 else 0
    
    # Max Drawdown
    cum_returns = (1 + returns).cumprod()
    peak = cum_returns.cummax()
    drawdown = (cum_returns - peak) / peak
    max_drawdown = drawdown.min()
    avg_drawdown = drawdown[drawdown < 0].mean()
    
    # Calmar
    calmar = cagr / abs(max_drawdown) if max_drawdown != 0 else 0
    
    # CVaR (95%)
    cvar_95 = returns.quantile(0.05)
    
    return {
        "Total Return": total_return,
        "CAGR": cagr,
        "Volatility": volatility,
        "Sharpe Ratio": sharpe,
        "Sortino Ratio": sortino,
        "Calmar Ratio": calmar,
        "Max Drawdown": max_drawdown,
        "Avg Drawdown": avg_drawdown,
        "CVaR (95%)": cvar_95
    }

def calculate_trade_metrics(trades_df):
    """
    Calculates metrics based on the list of discrete trades.
    """
    if trades_df.empty:
        return {
            "Total Trades": 0,
            "Win Rate": 0,
            "Avg Trade": 0,
            "Profit Factor": 0,
            "Expectancy": 0
        }
        
    wins = trades_df[trades_df['pnl'] > 0]
    losses = trades_df[trades_df['pnl'] < 0]
    
    num_trades = len(trades_df)
    win_rate = len(wins) / num_trades
    
    avg_win = wins['pnl'].mean() if not wins.empty else 0
    avg_loss = losses['pnl'].mean() if not losses.empty else 0
    avg_trade = trades_df['pnl'].mean()
    
    # Profit Factor: Gross Profit / Gross Loss
    gross_profit = wins['pnl_abs'].sum()
    gross_loss = abs(losses['pnl_abs'].sum())
    
    profit_factor = gross_profit / gross_loss if gross_loss != 0 else np.inf
    
    return {
        "Total Trades": num_trades,
        "Win Rate": win_rate,
        "Avg Trade": avg_trade,
        "Avg Win": avg_win,
        "Avg Loss": avg_loss,
        "Avg Duration": trades_df['duration'].mean(),
        "Profit Factor": profit_factor
    }
