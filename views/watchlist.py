import json
import streamlit as st
import pandas as pd
from pathlib import Path
from providers import stocks as stock_provider
from ai import claude
from config import Config

WATCHLIST_FILE = Path(__file__).parent.parent / "watchlist.json"


def _load() -> list:
    try:
        return json.loads(WATCHLIST_FILE.read_text(encoding="utf-8"))["stocks"]
    except Exception:
        return []


def _save(stocks: list):
    WATCHLIST_FILE.write_text(json.dumps({"stocks": stocks}, indent=2), encoding="utf-8")


def _enrich(symbols: list) -> list:
    rows = []
    for sym in symbols:
        q = stock_provider.get_quote(sym)
        if "error" in q:
            rows.append({"symbol": sym, "error": q["error"]})
            continue
        info = stock_provider.get_info(sym)
        rows.append({
            "symbol":     sym,
            "name":       info.get("shortName", sym),
            "price":      q["price"],
            "change":     q["change"],
            "change_pct": q["change_pct"],
            "volume":     q.get("volume", 0),
            "high52":     info.get("fiftyTwoWeekHigh", "—"),
            "low52":      info.get("fiftyTwoWeekLow", "—"),
            "pe":         info.get("trailingPE", "—"),
            "mktcap":     info.get("marketCap", "—"),
            "sector":     info.get("sector", "—"),
        })
    return rows


def render():
    st.title("Watchlist")
    services = Config.validate()

    stocks = _load()

    # ── Add / Remove ──────────────────────────────────────────────────────────
    with st.expander("Manage Watchlist", expanded=not stocks):
        col1, col2 = st.columns([3, 1])
        with col1:
            new_ticker = st.text_input("Add ticker (e.g. AAPL, TSLA, NVDA)", key="new_ticker").upper().strip()
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Add") and new_ticker:
                if new_ticker not in stocks:
                    stocks.append(new_ticker)
                    _save(stocks)
                    st.success(f"Added {new_ticker}")
                    st.rerun()
                else:
                    st.info(f"{new_ticker} already in watchlist.")

        if stocks:
            to_remove = st.multiselect("Remove stocks", options=stocks)
            if st.button("Remove selected") and to_remove:
                stocks = [s for s in stocks if s not in to_remove]
                _save(stocks)
                st.rerun()

    if not stocks:
        st.info("Your watchlist is empty. Add some tickers above.")
        return

    # ── Timeframe selector ────────────────────────────────────────────────────
    timeframe = st.radio(
        "Trading timeframe",
        ["Day Trade", "Swing (2–10 days)", "Mid-Term (1–3 months)", "Long-Term (6+ months)"],
        horizontal=True,
        index=1,
    )
    tf_key = timeframe.split()[0].lower()

    # ── Quotes table ──────────────────────────────────────────────────────────
    st.subheader(f"Watchlist Snapshot  ·  {stock_provider.active_provider()}")
    with st.spinner("Loading quotes…"):
        data = _enrich(stocks)

    display_rows = []
    for d in data:
        if "error" in d:
            display_rows.append({"Symbol": d["symbol"], "Name": "Error", "Price": "—",
                                  "Chg %": "—", "52w Low": "—", "52w High": "—",
                                  "P/E": "—", "Sector": "—"})
        else:
            display_rows.append({
                "Symbol":   d["symbol"],
                "Name":     d.get("name", "—"),
                "Price":    f"${d['price']:.2f}",
                "Chg %":    f"{d['change_pct']:+.2f}%",
                "52w Low":  d.get("low52", "—"),
                "52w High": d.get("high52", "—"),
                "P/E":      d.get("pe", "—"),
                "Sector":   d.get("sector", "—"),
            })

    st.dataframe(pd.DataFrame(display_rows), use_container_width=True, hide_index=True)

    # ── AI Suggestions ────────────────────────────────────────────────────────
    st.divider()
    st.subheader("AI Trading Suggestions")
    if not services["claude"]:
        st.warning("Add your Anthropic API key in Settings to enable AI suggestions.")
        return

    if st.button("Get AI Suggestions", type="primary"):
        valid_data = [d for d in data if "error" not in d]
        with st.spinner(f"Claude is analyzing your watchlist ({tf_key} timeframe)…"):
            suggestions = claude.generate_watchlist_suggestions(valid_data, tf_key)
        st.markdown(suggestions)
