import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

from src.backtest import load_data, run_backtest
from src.metrics import calculate_metrics, calculate_trade_metrics
from src.ui import get_custom_css

# --- Page Config ---
st.set_page_config(
    page_title="ProTrade Backtester",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Sidebar ---
with st.sidebar:
    st.markdown("## 📊 Configuration")
    
    # Theme Toggle
    theme = st.radio(
        "Theme",
        options=['dark', 'light'],
        index=0,
        horizontal=True
    )
    
    st.markdown("---")
    
    uploaded_file = st.file_uploader(
        "Upload Strategy CSV", 
        type=['csv'], 
        help="CSV must contain 'close' and 'forecast' columns."
    )
    
    st.markdown("---")
    st.markdown("### ⚙️ Settings")
    
    # Capital and Leverage
    initial_capital = st.number_input("Starting Capital ($)", value=10000.0, step=1000.0)
    leverage = st.number_input("Strategy Leverage Factor", value=1.0, step=0.1, min_value=0.1, max_value=10.0, help="Multiplier for the strategy position size.")
    
    annual_factor = st.number_input("Annualization Factor", value=756, help="e.g. 252 for daily, 756 for 8h (3x daily)")
    risk_free_rate = st.number_input("Risk Free Rate (%)", value=0.0, step=0.1) / 100
    
    st.markdown("---")
    st.info("💡 **Tip**: Forecast > 0 = Long, < 0 = Short. Position size is scaled by forecast/10 * Leverage.")

# --- Inject CSS with selected theme ---
st.markdown(get_custom_css(theme), unsafe_allow_html=True)

# --- Main Dashboard ---
st.markdown('<h1 class="gradient-text">Trading Strategy Dashboard</h1>', unsafe_allow_html=True)

if uploaded_file is not None:
    # Load Data
    with st.spinner("Processing data..."):
        raw_df = load_data(uploaded_file)
        
        if raw_df is not None:
            try:
                # Run Backtest
                df, trades_df = run_backtest(raw_df, initial_capital=initial_capital, leverage=leverage)
                
                # Calculate Metrics
                strat_metrics = calculate_metrics(df['strategy_return'], risk_free_rate=risk_free_rate)
                asset_metrics = calculate_metrics(df['asset_return'], risk_free_rate=risk_free_rate)
                trade_metrics = calculate_trade_metrics(trades_df)
                
                # --- KPI Row ---
                st.markdown("### 🚀 Performance Overview")
                
                col1, col2, col3, col4, col5 = st.columns(5)
                
                def metric_card(label, value, is_percent=True, sub_value=None, sub_is_percent=False, sub_label="Asset", theme='dark'):
                    fmt = "{:.2%}" if is_percent else "{:.2f}"
                    val_str = fmt.format(value)
                    
                    sub_html = ""
                    if sub_value is not None:
                        sub_fmt = "{:.2%}" if sub_is_percent else "{:.2f}"
                        sub_str = sub_fmt.format(sub_value)
                        # Use theme-appropriate color for sub-value when sub_label is "Win Rate" or "Nb of Trades"
                        if sub_label in ["Win Rate", "Nb of Trades"]:
                            text_color = "white" if theme == 'dark' else "black"
                            sub_html = f'<div class="metric-sub" style="color: {text_color};">{sub_label}: {sub_str}</div>'
                        else:
                            color = "positive" if sub_value > 0 else "negative"
                            sub_html = f'<div class="metric-sub {color}">{sub_label}: {sub_str}</div>'
                        
                    return f"""
                    <div class="metric-card">
                        <div class="metric-label">{label}</div>
                        <div class="metric-value">{val_str}</div>
                        {sub_html}
                    </div>
                    """

                with col1: st.markdown(metric_card("Total Return", strat_metrics['Total Return'], sub_value=asset_metrics['Total Return'], sub_is_percent=True, theme=theme), unsafe_allow_html=True)
                with col2: st.markdown(metric_card("Sortino Ratio", strat_metrics['Sortino Ratio'], is_percent=False, sub_value=asset_metrics['Sortino Ratio'], theme=theme), unsafe_allow_html=True)
                with col3: st.markdown(metric_card("Max Drawdown", strat_metrics['Max Drawdown'], sub_value=asset_metrics['Max Drawdown'], sub_is_percent=True, theme=theme), unsafe_allow_html=True)
                with col4: st.markdown(metric_card("Profit Factor", trade_metrics['Profit Factor'], is_percent=False, sub_value=trade_metrics['Win Rate'], sub_is_percent=True, sub_label="Win Rate", theme=theme), unsafe_allow_html=True)
                with col5: st.markdown(metric_card("Avg Duration", trade_metrics['Avg Duration'], sub_value=trade_metrics['Total Trades'], is_percent=False, sub_label="Nb of Trades", theme=theme), unsafe_allow_html=True)

                st.markdown("---")

                # --- Charts ---
                st.markdown("### 📈 Equity & Drawdown")
                
                # Create Subplots
                fig = make_subplots(
                    rows=4, cols=1, 
                    shared_xaxes=True, 
                    vertical_spacing=0.05,
                    row_heights=[0.3, 0.3, 0.2, 0.2],
                    subplot_titles=("Cumulative Returns (Equity Curve)", "Asset Price (Colored by Forecast)", "Drawdown", "Forecast & Position")
                )
                
                # 1. Equity Curve
                fig.add_trace(go.Scatter(
                    x=df['date'], y=df['strategy_equity'], 
                    name="Strategy", 
                    line=dict(color='#8b5cf6', width=2)
                ), row=1, col=1)
                
                fig.add_trace(go.Scatter(
                    x=df['date'], y=df['asset_equity'], 
                    name="Asset (Buy & Hold)", 
                    line=dict(color='#71717a', width=1, dash='dash')
                ), row=1, col=1)

                # 2. Asset Price Colored by Forecast
                # We use markers to simulate the gradient line
                fig.add_trace(go.Scatter(
                    x=df['date'], y=df['close'],
                    name="Price (Forecast Color)",
                    mode='markers',
                    marker=dict(
                        color=df['forecast'],
                        colorscale='RdYlGn', # Red(Low/Short) -> Green(High/Long)
                        cmin=-20, cmax=20,
                        size=3,
                        showscale=True,
                        colorbar=dict(title="Forecast", x=1.02, thickness=10, len=0.3, y=0.6)
                    )
                ), row=2, col=1)
                # Add a thin line underneath to ensure connectivity visually
                fig.add_trace(go.Scatter(
                    x=df['date'], y=df['close'],
                    showlegend=False,
                    mode='lines',
                    line=dict(color='rgba(255,255,255,0.1)', width=1),
                    hoverinfo='skip'
                ), row=2, col=1)

                # 3. Drawdown
                # Calculate DD series for plotting
                strat_dd = (df['strategy_equity'] / df['strategy_equity'].cummax()) - 1
                asset_dd = (df['asset_equity'] / df['asset_equity'].cummax()) - 1
                
                fig.add_trace(go.Scatter(
                    x=df['date'], y=strat_dd, 
                    name="Strategy DD", 
                    fill='tozeroy', 
                    line=dict(color='#ef4444', width=1),
                    fillcolor='rgba(239, 68, 68, 0.1)'
                ), row=3, col=1)

                fig.add_trace(go.Scatter(
                    x=df['date'], y=asset_dd, 
                    name="Asset DD", 
                    fill='tozeroy', 
                    line=dict(color='#71717a', width=1, dash='dot'),
                    fillcolor='rgba(113, 113, 122, 0.1)'
                ), row=3, col=1)
                
                 # 4. Forecast / Position
                fig.add_trace(go.Scatter(
                    x=df['date'], y=df['forecast'], 
                    name="Forecast", 
                    line=dict(color='#10b981', width=1)
                ), row=4, col=1)
                
                # Zero line for forecast
                fig.add_hline(y=0, line_dash="dot", line_color="gray", row=4, col=1)

                # Layout Updates
                # Theme-aware colors
                chart_font_color = '#0f172a' if theme == 'light' else '#fafafa'
                grid_color = 'rgba(0,0,0,0.15)' if theme == 'light' else 'rgba(255,255,255,0.1)'
                axis_color = '#334155' if theme == 'light' else '#d1d5db'
                
                fig.update_layout(
                    height=1000,
                    margin=dict(l=20, r=20, t=40, b=20),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color=chart_font_color, size=12),
                    hovermode="x unified",
                    showlegend=True,
                    legend=dict(
                        orientation="h", 
                        yanchor="bottom", 
                        y=1.02, 
                        xanchor="right", 
                        x=1,
                        font=dict(color=chart_font_color, size=11)
                    )
                )
                
                fig.update_yaxes(
                    gridcolor=grid_color, 
                    showgrid=True,
                    title_font=dict(color=axis_color, size=12),
                    tickfont=dict(color=axis_color, size=10)
                )
                fig.update_xaxes(
                    gridcolor=grid_color, 
                    showgrid=False,
                    title_font=dict(color=axis_color, size=12),
                    tickfont=dict(color=axis_color, size=10)
                )

                st.plotly_chart(fig, use_container_width=True)
                
                # --- Detailed Stats Table ---
                st.markdown("### 📋 Detailed Metrics")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### Period Statistics (Risk/Return)")
                    
                    # Formatting Helper for Period Stats
                    def fmt_period_metric(val, name):
                        if "Ratio" in name:
                            return f"{val:.2f}"
                        else:
                            return f"{val:.2%}"
                            
                    metrics_data = []
                    for k in strat_metrics.keys():
                        metrics_data.append({
                            "Metric": k,
                            "Strategy": fmt_period_metric(strat_metrics[k], k),
                            "Asset": fmt_period_metric(asset_metrics[k], k)
                        })
                        
                    metrics_df = pd.DataFrame(metrics_data)
                    
                    st.dataframe(
                        metrics_df, 
                        use_container_width=True,
                        hide_index=True
                    )

                with col2:
                    st.markdown("#### Trade Analysis (Strategy Only)")
                    if not trades_df.empty:
                        # Helper to format metrics
                        def fmt_trade_metric(key, val):
                            if key == "Total Trades" or key == "Avg Duration":
                                return f"{val:.0f}"
                            elif key == "Profit Factor":
                                return f"{val:.2f}"
                            else: # Win Rate, Avg Trade, Avg Win, Avg Loss
                                return f"{val:.2%}"

                        trade_stats_df = pd.DataFrame([
                            {"Metric": k, "Value": fmt_trade_metric(k, v)}
                            for k, v in trade_metrics.items()
                        ])
                        
                        # Right Align Value Column
                        st.dataframe(
                            trade_stats_df.style.set_properties(subset=['Value'], **{'text-align': 'right'}),
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        st.markdown("#### Trade Log")
                        # Sort by date descending
                        all_trades = trades_df[['start_date', 'type', 'pnl', 'duration']].sort_values('start_date', ascending=False)
                        
                        st.dataframe(
                            all_trades.style.format({
                                'pnl': '{:.2%}',
                                'start_date': '{:%Y-%m-%d %H:%M}'
                            }),
                            use_container_width=True,
                            height=400
                        )
                    else:
                        st.warning("No trades detected.")
                
                # --- Monthly Returns Heatmap ---
                st.markdown("---")
                st.markdown("### 📅 Monthly Returns Heatmap")
                
                # Helper function to calculate monthly returns
                def calculate_monthly_returns(df, return_col):
                    """Calculate monthly returns from daily/intraday returns"""
                    df_copy = df.copy()
                    df_copy['year'] = df_copy['date'].dt.year
                    df_copy['month'] = df_copy['date'].dt.month
                    
                    # Group by year and month, calculate cumulative return for each month
                    monthly = df_copy.groupby(['year', 'month']).apply(
                        lambda x: (1 + x[return_col]).prod() - 1
                    ).reset_index(name='return')
                    
                    # Pivot to create heatmap format
                    heatmap_data = monthly.pivot(index='year', columns='month', values='return')
                    return heatmap_data
                
                # Calculate monthly returns
                strategy_monthly = calculate_monthly_returns(df, 'strategy_return')
                asset_monthly = calculate_monthly_returns(df, 'asset_return')
                
                # Create heatmaps side by side
                col1, col2 = st.columns(2)
                
                month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                
                with col1:
                    st.markdown("#### Strategy Monthly Returns")
                    fig_strat = go.Figure(data=go.Heatmap(
                        z=strategy_monthly.values,
                        x=[month_names[i-1] for i in strategy_monthly.columns],
                        y=strategy_monthly.index,
                        colorscale='RdYlGn',
                        zmid=0,
                        text=strategy_monthly.values,
                        texttemplate='%{text:.1%}',
                        textfont={"size": 10},
                        colorbar=dict(title="Return", tickformat=".0%")
                    ))
                    fig_strat.update_layout(
                        height=400,
                        margin=dict(l=20, r=20, t=20, b=20),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color=chart_font_color, size=11),
                        xaxis=dict(side='top', tickfont=dict(color=axis_color))
                    )
                    st.plotly_chart(fig_strat, use_container_width=True)
                
                with col2:
                    st.markdown("#### Asset Monthly Returns")
                    fig_asset = go.Figure(data=go.Heatmap(
                        z=asset_monthly.values,
                        x=[month_names[i-1] for i in asset_monthly.columns],
                        y=asset_monthly.index,
                        colorscale='RdYlGn',
                        zmid=0,
                        text=asset_monthly.values,
                        texttemplate='%{text:.1%}',
                        textfont={"size": 10},
                        colorbar=dict(title="Return", tickformat=".0%")
                    ))
                    fig_asset.update_layout(
                        height=400,
                        margin=dict(l=20, r=20, t=20, b=20),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color=chart_font_color, size=11),
                        xaxis=dict(side='top', tickfont=dict(color=axis_color))
                    )
                    st.plotly_chart(fig_asset, use_container_width=True)
                
                # --- Regime Analysis ---
                st.markdown("---")
                st.markdown("### 🎯 Performance by Market Regime")
                
                # Classify regimes based on asset returns
                # Using rolling window to smooth regime classification
                df_regime = df.copy()
                rolling_window = 21  # ~1 week for 8h bars
                df_regime['rolling_return'] = df_regime['asset_return'].rolling(window=rolling_window).mean()
                
                # Define regime thresholds (annualized)
                def classify_regime(ret):
                    """Classify market regime based on rolling return"""
                    annualized = ret * 756  # 8h bars
                    # Adjusted thresholds for more even distribution
                    if annualized > 0.30:
                        return 'Strong Bull'
                    elif annualized > 0.10:
                        return 'Bull'
                    elif annualized > -0.10:
                        return 'Sideways'
                    elif annualized > -0.30:
                        return 'Bear'
                    else:
                        return 'Strong Bear'
                
                df_regime['regime'] = df_regime['rolling_return'].apply(classify_regime)
                
                # Calculate cumulative returns by regime
                regime_performance = []
                for regime in ['Strong Bull', 'Bull', 'Sideways', 'Bear', 'Strong Bear']:
                    regime_data = df_regime[df_regime['regime'] == regime]
                    if len(regime_data) > 0:
                        strat_ret = (1 + regime_data['strategy_return']).prod() - 1
                        asset_ret = (1 + regime_data['asset_return']).prod() - 1
                        regime_performance.append({
                            'Regime': regime,
                            'Strategy': strat_ret,
                            'Asset': asset_ret,
                            'Periods': len(regime_data)
                        })
                
                regime_df = pd.DataFrame(regime_performance)
                
                # Add collapsible explanatory note
                with st.expander("ℹ️ Regime Definitions"):
                    st.markdown("""
                    **Regime Classification** (based on annualized rolling returns):
                    - 🟢 **Strong Bull**: > +30% annualized
                    - 🔵 **Bull**: +10% to +30% annualized
                    - ⚪ **Sideways**: -10% to +10% annualized
                    - 🟠 **Bear**: -30% to -10% annualized
                    - 🔴 **Strong Bear**: < -30% annualized
                    
                    *Regimes are calculated using a 21-period rolling window of returns.*
                    """)
                
                # Create regime comparison chart
                fig_regime = go.Figure()
                fig_regime.add_trace(go.Bar(
                    name='Strategy',
                    x=regime_df['Regime'],
                    y=regime_df['Strategy'],
                    marker_color='#8b5cf6',
                    text=regime_df['Strategy'],
                    texttemplate='%{text:.1%}',
                    textposition='outside',
                    customdata=regime_df['Periods'],
                    hovertemplate='<b>%{x}</b><br>Return: %{y:.2%}<br>Periods: %{customdata}<extra></extra>'
                ))
                fig_regime.add_trace(go.Bar(
                    name='Asset',
                    x=regime_df['Regime'],
                    y=regime_df['Asset'],
                    marker_color='#71717a',
                    text=regime_df['Asset'],
                    texttemplate='%{text:.1%}',
                    textposition='outside',
                    customdata=regime_df['Periods'],
                    hovertemplate='<b>%{x}</b><br>Return: %{y:.2%}<br>Periods: %{customdata}<extra></extra>'
                ))
                
                fig_regime.update_layout(
                    barmode='group',
                    height=400,
                    margin=dict(l=20, r=20, t=40, b=20),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color=chart_font_color, size=12),
                    yaxis=dict(title="Cumulative Return", tickformat=".0%", gridcolor=grid_color, title_font=dict(color=axis_color), tickfont=dict(color=axis_color)),
                    xaxis=dict(title="Market Regime", title_font=dict(color=axis_color), tickfont=dict(color=axis_color)),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color=chart_font_color))
                )
                
                st.plotly_chart(fig_regime, use_container_width=True)
                
                # --- Quarterly and Yearly Performance ---
                st.markdown("---")
                st.markdown("### 📊 Quarterly & Yearly Performance")
                
                # Calculate quarterly returns
                df_period = df.copy()
                df_period['year'] = df_period['date'].dt.year
                df_period['quarter'] = df_period['date'].dt.quarter
                
                quarterly = df_period.groupby(['year', 'quarter']).apply(
                    lambda x: pd.Series({
                        'strategy_return': (1 + x['strategy_return']).prod() - 1,
                        'asset_return': (1 + x['asset_return']).prod() - 1
                    })
                ).reset_index()
                quarterly['period'] = quarterly['year'].astype(str) + ' Q' + quarterly['quarter'].astype(str)
                
                # Calculate yearly returns
                yearly = df_period.groupby('year').apply(
                    lambda x: pd.Series({
                        'strategy_return': (1 + x['strategy_return']).prod() - 1,
                        'asset_return': (1 + x['asset_return']).prod() - 1
                    })
                ).reset_index()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### Quarterly Returns")
                    fig_q = go.Figure()
                    fig_q.add_trace(go.Bar(
                        name='Strategy',
                        x=quarterly['period'],
                        y=quarterly['strategy_return'],
                        marker_color='#8b5cf6'
                    ))
                    fig_q.add_trace(go.Bar(
                        name='Asset',
                        x=quarterly['period'],
                        y=quarterly['asset_return'],
                        marker_color='#71717a'
                    ))
                    fig_q.update_layout(
                        barmode='group',
                        height=400,
                        margin=dict(l=20, r=20, t=20, b=20),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color=chart_font_color, size=11),
                        yaxis=dict(title="Return", tickformat=".0%", gridcolor=grid_color, title_font=dict(color=axis_color), tickfont=dict(color=axis_color)),
                        xaxis=dict(tickangle=-45, tickfont=dict(color=axis_color)),
                        showlegend=True,
                        legend=dict(font=dict(color=chart_font_color))
                    )
                    st.plotly_chart(fig_q, use_container_width=True)
                
                with col2:
                    st.markdown("#### Yearly Returns")
                    fig_y = go.Figure()
                    fig_y.add_trace(go.Bar(
                        name='Strategy',
                        x=yearly['year'].astype(str),
                        y=yearly['strategy_return'],
                        marker_color='#8b5cf6',
                        text=yearly['strategy_return'],
                        texttemplate='%{text:.1%}',
                        textposition='outside'
                    ))
                    fig_y.add_trace(go.Bar(
                        name='Asset',
                        x=yearly['year'].astype(str),
                        y=yearly['asset_return'],
                        marker_color='#71717a',
                        text=yearly['asset_return'],
                        texttemplate='%{text:.1%}',
                        textposition='outside'
                    ))
                    fig_y.update_layout(
                        barmode='group',
                        height=400,
                        margin=dict(l=20, r=20, t=20, b=20),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color=chart_font_color, size=11),
                        yaxis=dict(title="Return", tickformat=".0%", gridcolor=grid_color, title_font=dict(color=axis_color), tickfont=dict(color=axis_color)),
                        xaxis=dict(title="Year", title_font=dict(color=axis_color), tickfont=dict(color=axis_color)),
                        showlegend=True,
                        legend=dict(font=dict(color=chart_font_color))
                    )
                    st.plotly_chart(fig_y, use_container_width=True)

            except Exception as e:
                st.error(f"Error running backtest: {e}")
                st.exception(e)
        else:
            st.error("Could not parse file. Please check format.")
else:
    # Landing State
    st.markdown("""
    <div style="text-align: center; padding: 50px;">
        <h2>👋 Welcome to ProTrade</h2>
        <p style="color: #a1a1aa;">Upload a CSV file containing <code>date</code>, <code>close</code>, and <code>forecast</code> columns to begin.</p>
    </div>
    """, unsafe_allow_html=True)
