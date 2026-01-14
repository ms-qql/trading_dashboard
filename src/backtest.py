import pandas as pd
import numpy as np

def load_data(file):
    """
    Loads CSV data and parses dates.
    """
    try:
        df = pd.read_csv(file)
        # Attempt to parse date column. Check for common names.
        date_col = next((col for col in df.columns if col.lower() in ['date', 'time', 'timestamp']), None)
        if date_col:
            df[date_col] = pd.to_datetime(df[date_col])
        return df
    except Exception as e:
        return None

def run_backtest(df, initial_capital=10000.0, leverage=1.0):
    """
    Performs the backtest calculation.
    Assumes columns: 'close', 'forecast'.
    """
    # Ensure column names are lower case for easier access
    df.columns = [c.lower() for c in df.columns]
    
    if 'close' not in df.columns or 'forecast' not in df.columns:
        raise ValueError("CSV must contain 'close' and 'forecast' columns.")

    # Sort by date if available
    if 'date' in df.columns:
        df = df.sort_values('date').reset_index(drop=True)

    # Filter data to start when forecast is available
    df = df[df['forecast'].notna()].reset_index(drop=True)
    
    if df.empty:
        raise ValueError("No valid forecast data found.")

    # Calculate Asset Returns
    df['asset_return'] = df['close'].pct_change().fillna(0)
    
    # Calculate Strategy Position (Lagged by 1 period to avoid lookahead bias)
    # Position = (Forecast / 10) * Leverage
    
    df['position'] = (df['forecast'] / 10.0) * leverage
    df['shifted_position'] = df['position'].shift(1).fillna(0)
    
    # Strategy Return
    df['strategy_return'] = df['asset_return'] * df['shifted_position']
    
    # Cumulative Returns (Equity Curve)
    # Start at initial_capital
    df['asset_equity'] = initial_capital * (1 + df['asset_return']).cumprod()
    df['strategy_equity'] = initial_capital * (1 + df['strategy_return']).cumprod()
    
    # Trade Identification (Zero Crossings)
    # We identify "Trades" as blocks of time where the sign of the Forecast is consistent.
    # When sign changes, we close the previous trade and start a new one.
    
    trades = []
    
    # We need to iterate to capture trade blocks
    # Note: 'sign' column is already created
    
    # 0 is problematic? Prompt says: "crossdown below 0... close, short open". 
    # "entry/exit is when the forcast crosses the 0 line"
    # We assume trade is OPEN as long as sign is consistent.
    
    current_trade = {}
    in_trade = False
    
    # Get indices where sign changes
    # Use integer indices specifically
    # sign != 0. If forecast is 0, we are "not invested".
    
    # Let's iterate through rows for safety and clarity in trade accounting
    # (Vectorization is faster but logic here requires linking equity_start to equity_end)
    
    # Pre-calculate equity values to lookup
    equity_curve = df['strategy_equity'].values
    dates = df['date'].values
    signs = np.sign(df['forecast'].values) # 1, -1, 0
    
    trade_start_idx = 0
    trade_start_equity = initial_capital
    trade_type = 0 # 1 or -1
    
    # Find first non-zero signal
    first_idx = np.argmax(signs != 0)
    if signs[first_idx] == 0:
        # Never invested
        pass
    else:
        trade_start_idx = first_idx
        trade_start_equity = equity_curve[first_idx] # Equity at END of this bar? 
        # Actually, if signal appears at i, we enter, and returns start accruing at i+1?
        # Our backtest logic: returns[i] comes from position[i-1].
        # So trade STARTING at index i effectively captures returns from i+1 onwards?
        # Let's use the Equity Curve directly.
        # Trade Result = Equity(Exit) / Equity(Entry) - 1.
        
        # We need to capture the exact time the signal flips.
        # Position[i] depends on Forecast[i]. Return[i] depends on Position[i-1] (shifted).
        # We calculated 'strategy_equity' using 'strategy_return'.
        # 'strategy_return'[i] is the PnL achieved AT date[i].
        
        # If signal changes at index `i`, the position changes for `i`.
        # The return for the NEW position happens at `i+1`.
        # The return for the OLD position happens at `i`? No, return[i] used pos[i-1].
        
        # So, if sign changes at index `i`:
        # The return[i] belongs to the OLD trade (since it used pos[i-1]).
        # The return[i+1] will belong to the NEW trade.
        
        # Therefore, Trade End Index = i. Trade Start Index = i.
        # Trade PnL = Equity[i] / Equity[Trade_Start] - 1.
        
        trade_type = signs[first_idx]
        trade_start_equity = equity_curve[trade_start_idx] 
        # Wait, if we start at `first_idx`, the equity at `first_idx` already includes return from `first_idx`.
        # We should use Equity[first_idx - 1] as the basis?
        # initial_capital is the basis for the very first trade.
        
        trade_start_equity = initial_capital if trade_start_idx == 0 else equity_curve[trade_start_idx - 1]
        
        start_date = dates[trade_start_idx]

        for i in range(first_idx + 1, len(df)):
            current_sign = signs[i]
            
            # If sign changes or we become flat (0)
            if current_sign != trade_type:
                # Close Trade
                exit_equity = equity_curve[i-1] # The equity after the last return of the trade
                # Warning: check alignment. 
                # return[i] depends on pos[i-1]. pos[i-1] had 'trade_type'.
                # So return[i] IS part of the trade.
                # So Exit Equity is equity_curve[i].
                
                exit_equity = equity_curve[i]
                
                pnl = (exit_equity / trade_start_equity) - 1
                
                trades.append({
                    'start_date': start_date,
                    'end_date': dates[i],
                    'type': 'Long' if trade_type > 0 else 'Short',
                    'pnl': pnl,
                    'pnl_abs': exit_equity - trade_start_equity,
                    'duration': i - trade_start_idx # roughly bars
                })
                
                # Start New Trade (if not 0)
                if current_sign != 0:
                    trade_type = current_sign
                    trade_start_idx = i
                    start_date = dates[i]
                    trade_start_equity = exit_equity # Compounded
                else:
                    trade_type = 0
                    
        # Close last open trade
        if trade_type != 0:
             exit_equity = equity_curve[-1]
             pnl = (exit_equity / trade_start_equity) - 1
             trades.append({
                    'start_date': start_date,
                    'end_date': dates[-1],
                    'type': 'Long' if trade_type > 0 else 'Short',
                    'pnl': pnl,
                    'pnl_abs': exit_equity - trade_start_equity,
                    'duration': len(df) - trade_start_idx
             })

    trades_df = pd.DataFrame(trades)
    
    return df, trades_df
