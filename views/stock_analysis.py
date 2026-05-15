import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from providers import stocks as stock_provider
from ai.claude import analyze_stock, analyze_stock_my_strategy, analyze_earnings
from config import Config


def _candlestick_chart(ticker: str, period: str, interval: str):
    df = stock_provider.get_history(ticker, period=period, interval=interval)
    if df is None or df.empty:
        st.warning("No price history available.")
        return

    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"],
        low=df["Low"],  close=df["Close"],
        name=ticker,
    ))
    fig.add_trace(go.Bar(
        x=df.index, y=df["Volume"],
        name="Volume", yaxis="y2",
        marker_color="rgba(100,100,200,0.3)",
    ))

    # 20 & 50 SMA
    df["SMA20"] = df["Close"].rolling(20).mean()
    df["SMA50"] = df["Close"].rolling(50).mean()
    fig.add_trace(go.Scatter(x=df.index, y=df["SMA20"], name="SMA 20",
                             line=dict(color="orange", width=1)))
    fig.add_trace(go.Scatter(x=df.index, y=df["SMA50"], name="SMA 50",
                             line=dict(color="blue", width=1)))

    fig.update_layout(
        title=f"{ticker} — {period}",
        xaxis_rangeslider_visible=False,
        yaxis2=dict(overlaying="y", side="right", showgrid=False),
        height=500,
        legend=dict(orientation="h"),
    )
    st.plotly_chart(fig, use_container_width=True)

    return df


def _key_metrics(info: dict):
    cols = st.columns(4)
    metrics = [
        ("Price",       f"${info.get('currentPrice') or info.get('regularMarketPrice', '—')}"),
        ("52w High",    f"${info.get('fiftyTwoWeekHigh', '—')}"),
        ("52w Low",     f"${info.get('fiftyTwoWeekLow', '—')}"),
        ("Market Cap",  _fmt_large(info.get("marketCap"))),
        ("P/E (TTM)",   info.get("trailingPE", "—")),
        ("EPS (TTM)",   info.get("trailingEps", "—")),
        ("Rev Growth",  _pct(info.get("revenueGrowth"))),
        ("Dividend",    _pct(info.get("dividendYield"))),
    ]
    for i, (label, val) in enumerate(metrics):
        cols[i % 4].metric(label, val)


def _fmt_large(n) -> str:
    if n is None:
        return "—"
    if n >= 1e12:
        return f"${n/1e12:.2f}T"
    if n >= 1e9:
        return f"${n/1e9:.2f}B"
    if n >= 1e6:
        return f"${n/1e6:.2f}M"
    return str(n)


def _pct(v) -> str:
    try:
        return f"{float(v)*100:.2f}%"
    except (TypeError, ValueError):
        return "—"


def _history_summary(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return "No history available."
    latest = df.iloc[-1]
    oldest = df.iloc[0]
    chg = (latest["Close"] - oldest["Close"]) / oldest["Close"] * 100
    return (
        f"{oldest.name.date()} to {latest.name.date()} | "
        f"Change: {chg:+.2f}% | "
        f"High: {df['High'].max():.2f} | Low: {df['Low'].min():.2f} | "
        f"Last close: {latest['Close']:.2f}"
    )


def render():
    from providers.stocks import active_provider
    st.title("Stock Analysis")
    st.caption(f"Data: {active_provider()}  |  Charts: Yahoo Finance (historical)")
    services = Config.validate()

    # ── Ticker input ──────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns([2, 2, 2])
    with col1:
        ticker = st.text_input("Ticker symbol", placeholder="e.g. AAPL").upper().strip()
    with col2:
        analysis_type = st.selectbox("Analysis type", ["My Strategy", "Technical & Fundamental", "Earnings Report"])
    with col3:
        timeframe = st.selectbox("Timeframe", ["Day Trade", "Swing", "Mid-Term", "Long-Term"])

    if not ticker:
        st.info("Enter a ticker symbol above to get started.")
        return

    # ── Chart period based on timeframe ───────────────────────────────────────
    period_map = {
        "Day Trade": ("5d",  "15m"),
        "Swing":     ("3mo", "1d"),
        "Mid-Term":  ("6mo", "1d"),
        "Long-Term": ("2y",  "1wk"),
    }
    period, interval = period_map.get(timeframe, ("3mo", "1d"))

    # ── Load data ─────────────────────────────────────────────────────────────
    with st.spinner(f"Loading {ticker}…"):
        info    = stock_provider.get_info(ticker)
        df      = _candlestick_chart(ticker, period, interval)

    if not info:
        st.error(f"Could not load data for {ticker}. Check the ticker symbol.")
        return

    name = info.get("longName", ticker)
    sector = info.get("sector", "")
    st.caption(f"{name}  |  {sector}")

    # ── Key metrics ───────────────────────────────────────────────────────────
    st.subheader("Key Metrics")
    _key_metrics(info)

    # ── AI Analysis ───────────────────────────────────────────────────────────
    st.divider()
    if not services["claude"]:
        st.warning("Add your Anthropic API key in Settings to enable AI analysis.")
        return

    if analysis_type == "My Strategy":
        st.subheader("My Strategy (SMC) Analysis")
        if st.button("Analyze", type="primary"):
            summary = _history_summary(df)
            tf_key  = timeframe.split()[0].lower()
            with st.spinner(f"Applying your strategy to {ticker}…"):
                result = analyze_stock_my_strategy(ticker, info, summary, tf_key)
            st.markdown(result)

    elif analysis_type == "Technical & Fundamental":
        st.subheader("AI Analysis")
        if st.button("Analyze", type="primary"):
            summary = _history_summary(df)
            tf_key  = timeframe.split()[0].lower()
            with st.spinner(f"Claude is analyzing {ticker}…"):
                result = analyze_stock(ticker, info, summary, tf_key)
            st.markdown(result)

    else:  # Earnings Report
        st.subheader("Earnings Report Analysis")
        if st.button("Analyze Earnings", type="primary"):
            with st.spinner(f"Fetching earnings data for {ticker}…"):
                earnings = stock_provider.get_earnings(ticker)
            with st.spinner("Claude is analyzing the earnings…"):
                result = analyze_earnings(ticker, earnings, info)
            st.markdown(result)

            # Show raw earnings table if available
            qe = earnings.get("quarterly_earnings", {})
            if qe:
                st.subheader("Quarterly Earnings History")
                try:
                    st.dataframe(pd.DataFrame(qe), use_container_width=True)
                except Exception:
                    pass
