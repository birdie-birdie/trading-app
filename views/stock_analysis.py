import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import anthropic
from providers import stocks as stock_provider
from ai.claude import analyze_stock, analyze_stock_my_strategy, analyze_earnings, get_smc_entry_levels
from config import Config


def _claude_error(e: Exception) -> None:
    """Show a user-friendly error for Claude API failures."""
    if isinstance(e, anthropic.APIStatusError) and e.status_code == 529:
        st.warning("Claude is temporarily overloaded. Please try again in a moment.")
    elif isinstance(e, anthropic.AuthenticationError):
        st.error("Invalid Anthropic API key. Check your key in Settings.")
    else:
        st.error(f"Claude API error: {e}")


def _md(text: str) -> None:
    """Render Claude output safely — escapes $ to prevent Streamlit LaTeX rendering."""
    st.markdown(text.replace("$", r"\$"))


# ─── VWAP ─────────────────────────────────────────────────────────────────────

def _compute_vwap(df: pd.DataFrame, interval: str) -> pd.Series:
    tp  = (df["High"] + df["Low"] + df["Close"]) / 3
    tpv = tp * df["Volume"]
    intraday = interval in ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h"]

    if intraday:
        dates = df.index.normalize()
        vwap  = pd.Series(index=df.index, dtype=float)
        for d in dates.unique():
            mask        = dates == d
            cum_vol     = df["Volume"][mask].cumsum().replace(0, np.nan)
            vwap[mask]  = tpv[mask].cumsum() / cum_vol
    else:
        cum_vol = df["Volume"].cumsum().replace(0, np.nan)
        vwap    = tpv.cumsum() / cum_vol

    return vwap


# ─── Main candlestick chart ────────────────────────────────────────────────────

def _candlestick_chart(ticker: str, period: str, interval: str, timeframe: str = "", prepost: bool = False):
    df = stock_provider.get_history(ticker, period=period, interval=interval, prepost=prepost)
    if df is None or df.empty:
        st.warning("No price history available.")
        return None

    fig = go.Figure()

    # Candlesticks
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"],
        low=df["Low"],   close=df["Close"],
        name=ticker,
    ))

    # Volume bars
    fig.add_trace(go.Bar(
        x=df.index, y=df["Volume"],
        name="Volume", yaxis="y2",
        marker_color="rgba(100,100,200,0.25)",
    ))

    # SMA 20 & 50
    df["SMA20"] = df["Close"].rolling(20).mean()
    df["SMA50"] = df["Close"].rolling(50).mean()
    fig.add_trace(go.Scatter(x=df.index, y=df["SMA20"], name="SMA 20",
                             line=dict(color="orange", width=1)))
    fig.add_trace(go.Scatter(x=df.index, y=df["SMA50"], name="SMA 50",
                             line=dict(color="royalblue", width=1)))

    # VWAP
    df["VWAP"] = _compute_vwap(df, interval)
    fig.add_trace(go.Scatter(x=df.index, y=df["VWAP"], name="VWAP",
                             line=dict(color="magenta", width=1.5, dash="dot")))

    interval_label = {"1m": "1m", "2m": "2m", "5m": "5m", "15m": "15m",
                      "30m": "30m", "1h": "1h", "1d": "Daily", "1wk": "Weekly"}
    bar_label = interval_label.get(interval, interval)
    title = f"{ticker}  |  {timeframe}  ({bar_label} bars)"

    # Skip non-trading periods to remove blank gaps
    intraday = interval in ["1m", "2m", "5m", "15m", "30m", "60m", "1h"]
    rangebreaks = [dict(bounds=["sat", "mon"])]  # always skip weekends
    if intraday and not prepost:
        rangebreaks.append(dict(bounds=[16, 9.5], pattern="hour"))  # skip after-hours

    fig.update_layout(
        title=title,
        xaxis_rangeslider_visible=False,
        xaxis=dict(rangebreaks=rangebreaks),
        yaxis2=dict(overlaying="y", side="right", showgrid=False),
        height=520,
        legend=dict(orientation="h"),
    )
    st.plotly_chart(fig, use_container_width=True)
    return df


# ─── SMC entry map chart ───────────────────────────────────────────────────────

def _smc_entry_chart(df: pd.DataFrame, levels: dict, ticker: str):
    if not levels or df is None or df.empty:
        return

    bias    = levels.get("bias", "Bullish")
    ob      = levels.get("order_block", {})
    fvg     = levels.get("fvg", {})
    entry   = levels.get("entry")
    sl      = levels.get("stop_loss")
    target  = levels.get("target")
    choch   = levels.get("choch_level")

    # Show last 40 candles for clarity
    recent = df.tail(40)
    x_start = recent.index[0]
    x_end   = recent.index[-1]

    ob_color  = "rgba(0,180,100,0.15)"  if bias == "Bullish" else "rgba(220,50,50,0.15)"
    fvg_color = "rgba(255,200,0,0.15)"
    ob_border = "rgba(0,180,100,0.6)"   if bias == "Bullish" else "rgba(220,50,50,0.6)"

    fig = go.Figure()

    # Candlesticks
    fig.add_trace(go.Candlestick(
        x=recent.index,
        open=recent["Open"], high=recent["High"],
        low=recent["Low"],   close=recent["Close"],
        name=ticker, showlegend=False,
    ))

    # VWAP on entry map too
    if "VWAP" in df.columns:
        fig.add_trace(go.Scatter(
            x=recent.index, y=df["VWAP"].reindex(recent.index),
            name="VWAP", line=dict(color="magenta", width=1, dash="dot"),
        ))

    shapes = []
    annotations = []

    def hline(y, color, dash, label, side="right"):
        if y is None:
            return
        shapes.append(dict(
            type="line", x0=x_start, x1=x_end, y0=y, y1=y,
            line=dict(color=color, width=1.5, dash=dash),
        ))
        annotations.append(dict(
            x=x_end, y=y, xanchor="left", yanchor="middle",
            text=f"  {label}: {y:.2f}", showarrow=False,
            font=dict(color=color, size=11),
        ))

    def zone(y_low, y_high, fill, border, label):
        if not y_low or not y_high:
            return
        shapes.append(dict(
            type="rect", x0=x_start, x1=x_end, y0=y_low, y1=y_high,
            fillcolor=fill, line=dict(color=border, width=1),
        ))
        annotations.append(dict(
            x=x_start, y=(y_low + y_high) / 2,
            xanchor="right", yanchor="middle",
            text=f"{label}  ", showarrow=False,
            font=dict(size=10, color=border),
        ))

    # Order Block zone
    zone(ob.get("low"), ob.get("high"), ob_color, ob_border, "Order Block")

    # FVG zone
    zone(fvg.get("low"), fvg.get("high"), fvg_color, "rgba(200,160,0,0.8)", "FVG")

    # Key levels
    hline(choch,  "purple",  "dashdot", "CHOCH")
    hline(entry,  "lime",    "solid",   "Entry")
    hline(sl,     "red",     "dash",    "Stop Loss")
    hline(target, "dodgerblue", "dash", "Target")

    # R:R annotation
    if entry and sl and target:
        risk   = abs(entry - sl)
        reward = abs(target - entry)
        rr     = f"{reward/risk:.1f}R" if risk > 0 else "—"
        annotations.append(dict(
            x=x_end, y=target, xanchor="left", yanchor="bottom",
            text=f"  R:R {rr}", showarrow=False,
            font=dict(color="dodgerblue", size=12, family="Arial Black"),
        ))

    fig.update_layout(
        title=f"{ticker} — SMC Entry Map  ({bias})",
        shapes=shapes,
        annotations=annotations,
        xaxis_rangeslider_visible=False,
        height=480,
        legend=dict(orientation="h"),
    )
    st.plotly_chart(fig, use_container_width=True)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _key_metrics(info: dict):
    cols = st.columns(4)
    metrics = [
        ("Price",      f"${info.get('currentPrice') or info.get('regularMarketPrice', '—')}"),
        ("52w High",   f"${info.get('fiftyTwoWeekHigh', '—')}"),
        ("52w Low",    f"${info.get('fiftyTwoWeekLow', '—')}"),
        ("Market Cap", _fmt_large(info.get("marketCap"))),
        ("P/E (TTM)",  info.get("trailingPE", "—")),
        ("EPS (TTM)",  info.get("trailingEps", "—")),
        ("Rev Growth", _pct(info.get("revenueGrowth"))),
        ("Dividend",   _pct(info.get("dividendYield"))),
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


# ─── Page ─────────────────────────────────────────────────────────────────────

def render():
    from providers.stocks import active_provider
    st.title("Stock Analysis")
    st.caption(f"Data: {active_provider()}  |  Charts: Yahoo Finance (historical)")
    services = Config.validate()

    # ── Inputs ────────────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns([2, 2, 2])
    with col1:
        ticker = st.text_input("Ticker symbol", placeholder="e.g. AAPL").upper().strip()
    with col2:
        analysis_type = st.selectbox(
            "Analysis type",
            ["My Strategy", "Technical & Fundamental", "Earnings Report"],
        )
    with col3:
        timeframe = st.selectbox("Timeframe", ["Day Trade", "Swing", "Mid-Term", "Long-Term"])

    if not ticker:
        st.info("Enter a ticker symbol above to get started.")
        return

    period_map = {
        "Day Trade": ("5d",  "5m"),
        "Swing":     ("3mo", "1h"),
        "Mid-Term":  ("6mo", "1d"),
        "Long-Term": ("2y",  "1wk"),
    }
    period, interval = period_map.get(timeframe, ("3mo", "1d"))

    intraday = interval in ["1m", "2m", "5m", "15m", "30m", "60m", "1h"]
    prepost  = False
    if intraday:
        prepost = st.checkbox("Show pre-market & after-hours", value=False)

    # ── Load & chart ──────────────────────────────────────────────────────────
    with st.spinner(f"Loading {ticker}…"):
        info = stock_provider.get_info(ticker)
        df   = _candlestick_chart(ticker, period, interval, timeframe, prepost)

    if not info:
        st.error(f"Could not load data for {ticker}. Check the ticker symbol.")
        return

    st.caption(f"{info.get('longName', ticker)}  |  {info.get('sector', '')}")

    st.subheader("Key Metrics")
    _key_metrics(info)

    # ── AI Analysis ───────────────────────────────────────────────────────────
    st.divider()
    if not services["claude"]:
        st.warning("Add your Anthropic API key in Settings to enable AI analysis.")
        return

    tf_key = timeframe.split()[0].lower()

    if analysis_type == "My Strategy":
        st.subheader("My Strategy (SMC) Analysis")
        if st.button("Analyze", type="primary"):
            summary = _history_summary(df)
            try:
                with st.spinner(f"Applying your strategy to {ticker}…"):
                    result = analyze_stock_my_strategy(ticker, info, summary, tf_key)
                st.session_state[f"smc_result_{ticker}"] = result

                with st.spinner("Building entry map…"):
                    levels = get_smc_entry_levels(ticker, info, summary, tf_key)
                st.session_state[f"smc_levels_{ticker}"] = levels
            except Exception as e:
                _claude_error(e)

        # Persist analysis across reruns
        result = st.session_state.get(f"smc_result_{ticker}")
        levels = st.session_state.get(f"smc_levels_{ticker}")

        if result:
            _md(result)
        if levels:
            st.subheader("Entry Map")
            _smc_entry_chart(df, levels, ticker)

    elif analysis_type == "Technical & Fundamental":
        st.subheader("AI Analysis")
        if st.button("Analyze", type="primary"):
            summary = _history_summary(df)
            try:
                with st.spinner(f"Claude is analyzing {ticker}…"):
                    result = analyze_stock(ticker, info, summary, tf_key)
                st.session_state[f"ta_result_{ticker}"] = result
            except Exception as e:
                _claude_error(e)

        result = st.session_state.get(f"ta_result_{ticker}")
        if result:
            _md(result)

    else:  # Earnings Report
        st.subheader("Earnings Report Analysis")
        if st.button("Analyze Earnings", type="primary"):
            try:
                with st.spinner(f"Fetching earnings data for {ticker}…"):
                    earnings = stock_provider.get_earnings(ticker)
                with st.spinner("Claude is analyzing the earnings…"):
                    result = analyze_earnings(ticker, earnings, info)
                st.session_state[f"earn_result_{ticker}"] = result
            except Exception as e:
                _claude_error(e)

        result = st.session_state.get(f"earn_result_{ticker}")
        if result:
            _md(result)
            qe = st.session_state.get(f"earn_qe_{ticker}", {})
            if qe:
                st.subheader("Quarterly Earnings History")
                try:
                    st.dataframe(pd.DataFrame(qe), use_container_width=True)
                except Exception:
                    pass
