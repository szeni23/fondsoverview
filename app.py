import os
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv

MY_PASSWORD = st.secrets["auth"]["APP_PASSWORD"]
NUM_SHARES = int(st.secrets["portfolio"]["NUM_SHARES"])
ISIN = st.secrets["portfolio"]["ISIN"]
TICKER = st.secrets["portfolio"]["TICKER"]
START_DATE = st.secrets["portfolio"]["START_DATE"]
INITIAL_SAVINGS = float(st.secrets["portfolio"]["INITIAL_SAVINGS"])

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.title("Please Log In")
    pass_input = st.text_input("Password", type="password")
    if st.button("Login"):
        if pass_input == MY_PASSWORD:
            st.session_state["logged_in"] = True
            st.rerun()
        else:
            st.error("Invalid password")
    st.stop()
else:
    st.title("💰 Friends Investment Dashboard")
    st.write("Tracking our shared investment and savings.")

    deposits_url = "https://raw.githubusercontent.com/szeni23/fondsoverview/main/deposit.csv"

    try:
        df_deposits = pd.read_csv(deposits_url, parse_dates=["date"], dayfirst=True)
        df_deposits = df_deposits[df_deposits["date"] <= pd.Timestamp.today()]
        if df_deposits.empty:
            deposit_sum = 0.0
        else:
            deposit_sum = df_deposits["amount"].sum()
        savings_balance = INITIAL_SAVINGS + deposit_sum
    except Exception as e:
        st.error(f"Could not load deposits CSV. Error: {e}")
        savings_balance = INITIAL_SAVINGS

    etf = yf.Ticker(TICKER)
    df = etf.history(start="2023-07-30")
    df.reset_index(inplace=True)

    initial_data = df.loc[df["Date"] == START_DATE]
    if not initial_data.empty:
        initial_price_usd = initial_data["Close"].iloc[0]
    else:
        fallback_data = df.loc[df["Date"] > START_DATE].head(1)
        if not fallback_data.empty:
            initial_price_usd = fallback_data["Close"].iloc[0]
        else:
            initial_price_usd = None

    latest_price_usd = df["Close"].iloc[-1] if not df.empty else None

    fx = yf.Ticker("CHF=X")
    fx_data = fx.history(period="1d")
    latest_fx_rate = fx_data["Close"].iloc[-1] if not fx_data.empty else 1.0

    if latest_price_usd:
        total_etf_value_chf = NUM_SHARES * latest_price_usd * latest_fx_rate
    else:
        total_etf_value_chf = 0.0

    if initial_price_usd and latest_price_usd:
        profit_usd = (latest_price_usd - initial_price_usd) * NUM_SHARES
        etf_profit_chf = profit_usd * latest_fx_rate
    else:
        etf_profit_chf = 0.0

    st.subheader("📊 Portfolio Overview")
    st.write(f"**Cash Balance:** CHF {savings_balance:,.2f}")

    if latest_price_usd:
        st.write(f"**ETF Holdings:** {NUM_SHARES} shares of {ISIN} (Latest Price: {latest_price_usd:.2f} USD)")
    else:
        st.write("**ETF Holdings:** Could not fetch latest price.")

    st.write(f"**Total ETF Value (Converted to CHF):** CHF {total_etf_value_chf:,.2f}")
    st.write(f"**ETF Profit Since Purchase (in CHF):** CHF {etf_profit_chf:,.2f}")
    st.write(f"**Total Portfolio Value:** CHF {(savings_balance + total_etf_value_chf):,.2f}")

    if not df.empty:
        fig = px.line(df, x="Date", y="Close", title=f"ETF Price Trend Since Purchase {START_DATE} | {ISIN}")
        st.plotly_chart(fig)
    else:
        st.warning("No ETF price data available.")
