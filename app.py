import streamlit as st
import vectorbt as vbt
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from datetime import datetime
import pytz  # Make sure pytz is installed

# Convert date to datetime with timezone
def convert_to_timezone_aware(date_obj):
    return datetime.combine(date_obj, datetime.min.time()).replace(tzinfo=pytz.UTC)

# Streamlit interface

st.set_page_config(page_title='VectorBT Backtesting', layout='wide')
st.title("VectorBT Backtesting - www.marketcalls.in")

# Sidebar for inputs
with st.sidebar:
    # Inputs for the symbol, start and end dates
    st.header("Strategy Controls")
    
    # Inputs for the symbol, start and end dates
    symbol = st.text_input("Enter the symbol (e.g., 'AAPL')", value="HDFCBANK.NS")
    start_date = st.date_input("Start Date", value=pd.to_datetime("2010-01-01"))
    end_date = st.date_input("End Date", value=pd.to_datetime("2023-01-01"))

    # EMA controls
    short_ema_period = st.number_input("Short EMA Period", value=10, min_value=1)
    long_ema_period = st.number_input("Long EMA Period", value=20, min_value=1)
    
    st.header("Backtesting Controls")

    # Backtesting controls
    initial_equity = st.number_input("Initial Equity", value=100000)
    size = st.text_input("Position Size", value='50')  # Text input for size
    size_type = st.selectbox("Size Type", ["amount", "value", "percent"], index=2)  # Dropdown for size type
    fees = st.number_input("Fees (as %)", value=0.12, format="%.4f")
    direction = st.selectbox("Direction", ["longonly", "shortonly", "both"], index=0)

    # Button to perform backtesting
    backtest_clicked = st.button("Backtest")

# Main area for results
if backtest_clicked:
    start_date_tz = convert_to_timezone_aware(start_date)
    end_date_tz = convert_to_timezone_aware(end_date)

    # Fetch data
    data = vbt.YFData.download(symbol, start=start_date_tz, end=end_date_tz).get('Close')

    # Calculate EMAs and signals
    short_ema = vbt.MA.run(data, short_ema_period, short_name='fast', ewm=True)
    long_ema = vbt.MA.run(data, long_ema_period, short_name='slow', ewm=True)
    entries = short_ema.ma_crossed_above(long_ema)
    exits = short_ema.ma_crossed_below(long_ema)

    # Convert size to appropriate type
    if size_type == 'percent':
        size_value = float(size) / 100.0
    else:
        size_value = float(size)

    # Run portfolio
    portfolio = vbt.Portfolio.from_signals(
        data, entries, exits,
        direction=direction,
        size=size_value,
        size_type=size_type,
        fees=fees/100,
        init_cash=initial_equity,
        freq='1D',
        min_size =1,
        size_granularity = 1
    )

    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Backtesting Stats", "List of Trades", 
                                          "Equity Curve", "Drawdown", "Portfolio Plot"])


    with tab1:
        # Display results
        st.markdown("**Backtesting Stats:**")
        stats_df = pd.DataFrame(portfolio.stats(), columns=['Value'])
        stats_df.index.name = 'Metric'  # Set the index name to 'Metric' to serve as the header
        st.dataframe(stats_df, height=800)  # Adjust the height as needed to remove the scrollbar

    with tab2:
        st.markdown("**List of Trades:**")
        trades_df = portfolio.trades.records_readable
        trades_df = trades_df.round(2)  # Rounding the values for better readability
        trades_df.index.name = 'Trade No'  # Set the index name to 'Trade Name' to serve as the header
        trades_df.drop(trades_df.columns[[0,1]], axis=1, inplace=True)
        st.dataframe(trades_df, width=800,height=600)  # Set index to False and use full width


    # Plotting
    equity_data = portfolio.value()
    drawdown_data = portfolio.drawdown() * 100

    with tab3:
    # Equity Curve
        equity_trace = go.Scatter(x=equity_data.index, y=equity_data, mode='lines', name='Equity',line=dict(color='green') )
        equity_fig = go.Figure(data=[equity_trace])
        equity_fig.update_layout(title='Equity Curve', xaxis_title='Date', yaxis_title='Equity',
                                 width=800,height=600)
        st.plotly_chart(equity_fig)

    with tab4:
        # Drawdown Curve
        drawdown_trace = go.Scatter(
            x=drawdown_data.index,
            y=drawdown_data,
            mode='lines',
            name='Drawdown',
            fill='tozeroy',
            line=dict(color='red')  # Set the line color to red
        )
        drawdown_fig = go.Figure(data=[drawdown_trace])
        drawdown_fig.update_layout(
            title='Drawdown Curve',
            xaxis_title='Date',
            yaxis_title='% Drawdown',
            template='plotly_white',
            width = 800,
            height = 600
        )
        st.plotly_chart(drawdown_fig)

    with tab5:
        # Portfolio Plot
        st.markdown("**Portfolio Plot:**")
        st.plotly_chart(portfolio.plot())
