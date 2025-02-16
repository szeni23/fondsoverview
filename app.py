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
    st.title("💰 SBOG42 Funds overview")

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

    col1, col2 = st.columns(2)
    col1.metric("Cash Balance", f"CHF {savings_balance:,.2f}")

    if initial_price_usd and latest_price_usd:
        total_performance = ((latest_price_usd / initial_price_usd) - 1) * 100
        delta_str = f"{etf_profit_chf:+,.2f} CHF ({total_performance:+.2f}%)"
    else:
        delta_str = f"{etf_profit_chf:+,.2f} CHF"

    col2.metric("Total ETF Value", f"CHF {total_etf_value_chf:,.2f}", delta=delta_str)
    if latest_price_usd:
        col2.caption(f"Depot Composition: {NUM_SHARES} shares of {ISIN} (Latest Price: {latest_price_usd:.2f} USD)")
    else:
        col2.caption("Depot Composition: Data not available")

    total_portfolio_value = savings_balance + total_etf_value_chf
    st.markdown(
        f'<div style="text-align: center; margin: 20px 0; padding: 15px; background-color: #e8f5e9; border-radius: 8px;">'
        f'<h2 style="margin: 0; color: #2e7d32;">Total Portfolio Value: CHF {total_portfolio_value:,.2f}</h2></div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    if not df.empty:
        import seaborn as sns
        import matplotlib.pyplot as plt

        plt.figure(figsize=(10, 4))
        sns.lineplot(data=df, x="Date", y="Close")
        plt.title(f"ETF Price Trend Since Purchase ({START_DATE}) | {ISIN}")
        plt.tight_layout()
        st.pyplot(plt.gcf())
    else:
        st.warning("No ETF price data available.")

    df["Daily Return"] = df["Close"].pct_change()
    volatility = df["Daily Return"].std() * 100
    risk_free_rate = 0.01
    sharpe_ratio = (df["Daily Return"].mean() - risk_free_rate / 252) / df["Daily Return"].std()

    col6, col7 = st.columns(2)
    col6.metric("Historical Volatility", f"{volatility:.2f}%")
    col7.metric("Sharpe Ratio", f"{sharpe_ratio:.2f}")

    st.link_button("Go to iShares ETF",
                   "https://www.ishares.com/de/privatanleger/de/produkte/251882/ishares-msci-world-ucits-etf-acc-fund")

    st.markdown("---")
    st.subheader("Alternative Investment Comparison")

    comparison_assets = {
        "Credit Suisse": "CS",
        "UBS": "SWX",
        "Tesla": "TSLA",
        "Microsoft": "MSFT",
        "Apple": "AAPL",
        "Nvidia": "NVDA",
        "S&P 500": "^GSPC",
        "SMI": "SMI",
        "Bitcoin ETF": "IBIT"

    }
    options = list(comparison_assets.keys()) + ["Other"]
    selected_asset = st.selectbox("Compare with:", options)

    if selected_asset == "Other":
        asset_ticker = st.text_input("Enter a ticker symbol for comparison:").strip().upper()
        if not asset_ticker:
            st.warning("Please enter a valid ticker symbol.")
            st.stop()
    else:
        asset_ticker = comparison_assets[selected_asset]

    if asset_ticker.upper() == "CS":
        st.warning("No available data. Idiots drove the company into the wall")
        st.stop()

    asset_data = yf.Ticker(asset_ticker).history(start=START_DATE)
    if asset_data.empty:
        st.warning(f"No data available for {selected_asset}.")
    else:
        asset_initial_price = asset_data["Close"].iloc[0]
        asset_latest_price = asset_data["Close"].iloc[-1]
        asset_performance = (asset_latest_price / asset_initial_price - 1) * 100

        initial_investment = NUM_SHARES * initial_price_usd
        alternative_shares = initial_investment / asset_initial_price
        asset_value_if_invested_usd = alternative_shares * asset_latest_price
        asset_profit_usd = asset_value_if_invested_usd - initial_investment
        asset_value_if_invested = asset_value_if_invested_usd * latest_fx_rate
        asset_profit_chf = asset_profit_usd * latest_fx_rate

        col1, col2 = st.columns(2)
        col1.metric(f"{selected_asset} Portfolio Value", f"CHF {asset_value_if_invested:,.2f}",
                    delta=f"{asset_performance:+.2f}%")
        col2.metric("Profit Difference", f"CHF {(asset_profit_chf - etf_profit_chf):,.2f}")

        df["Performance"] = df["Close"] / df["Close"].iloc[0] * 100
        asset_data["Performance"] = asset_data["Close"] / asset_data["Close"].iloc[0] * 100


        plt.figure(figsize=(10, 4))
        sns.lineplot(data=df, x="Date", y="Performance", label="ETF")
        asset_data_reset = asset_data.reset_index()
        sns.lineplot(data=asset_data_reset, x="Date", y="Performance", label=selected_asset)
        plt.title(f"ETF vs. {selected_asset} Performance Comparison")
        plt.tight_layout()

        st.pyplot(plt.gcf())

