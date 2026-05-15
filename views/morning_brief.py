import streamlit as st
import pandas as pd
from datetime import datetime
from config import Config
from providers import yahoo, finnhub_client
from ai import claude


def _futures_quotes() -> list:
    if Config.FUTURES_PROVIDER == "projectx" and Config.validate()["projectx"]:
        from providers import projectx
        return projectx.get_multiple_quotes(
            Config.FUTURES_WATCHLIST, Config.PROJECTX_USERNAME, Config.PROJECTX_API_KEY
        )
    return yahoo.get_multiple_quotes(Config.FUTURES_WATCHLIST)


def render():
    st.title("Morning Brief")
    st.caption(f"As of {datetime.now().strftime('%A, %B %d %Y  %H:%M')}")

    services = Config.validate()

    # ── Futures Overview ──────────────────────────────────────────────────────
    st.subheader("Index Futures")
    with st.spinner("Fetching futures data…"):
        futures_data = _futures_quotes()

    if futures_data:
        rows = []
        for f in futures_data:
            if "error" in f:
                rows.append({"Symbol": f["symbol"], "Price": "—", "Change": "—", "Chg %": "—",
                              "High": "—", "Low": "—", "Volume": "—"})
            else:
                rows.append({
                    "Symbol":  f["symbol"],
                    "Price":   f["price"],
                    "Change":  f["change"],
                    "Chg %":   f["change_pct"],
                    "High":    f.get("high", "—"),
                    "Low":     f.get("low", "—"),
                    "Volume":  f.get("volume", "—"),
                })
        df = pd.DataFrame(rows)

        def color_chg(val):
            try:
                v = float(val)
                color = "green" if v > 0 else ("red" if v < 0 else "gray")
                return f"color: {color}"
            except (TypeError, ValueError):
                return ""

        styled = df.style.map(color_chg, subset=["Change", "Chg %"])
        st.dataframe(styled, use_container_width=True, hide_index=True)
    else:
        st.warning("Could not fetch futures data.")

    # ── Economic Events ───────────────────────────────────────────────────────
    st.subheader("Today's Economic Events")
    if services["finnhub"]:
        with st.spinner("Fetching economic calendar…"):
            events = finnhub_client.get_economic_calendar(Config.FINNHUB_API_KEY)
        if events:
            impact_map = {"1": "Low", "2": "Medium", "3": "High"}
            ev_rows = [{
                "Time":   e.get("time", "")[:16],
                "Impact": impact_map.get(str(e.get("impact", "")), "—"),
                "Event":  e.get("event", ""),
                "Actual": e.get("actual", "—"),
                "Est.":   e.get("estimate", "—"),
                "Prev.":  e.get("prev", "—"),
            } for e in events]

            def color_impact(val):
                return {"High": "color: red", "Medium": "color: orange", "Low": "color: gray"}.get(val, "")

            ev_df = pd.DataFrame(ev_rows)
            st.dataframe(
                ev_df.style.map(color_impact, subset=["Impact"]),
                use_container_width=True, hide_index=True
            )
        else:
            st.info("No major economic events scheduled for today.")
    else:
        st.info("Add a Finnhub API key in Settings to see the economic calendar.")

    # ── Market News ───────────────────────────────────────────────────────────
    st.subheader("Market News")
    if services["finnhub"]:
        with st.spinner("Fetching news…"):
            news = finnhub_client.get_market_news(Config.FINNHUB_API_KEY)
        if news:
            for n in news:
                st.markdown(f"- **[{n.get('headline','')}]({n.get('url','#')})** — *{n.get('source','')}*")
        else:
            st.info("No news available.")
    else:
        st.info("Add a Finnhub API key in Settings to see market news.")

    # ── AI Morning Brief ──────────────────────────────────────────────────────
    st.divider()
    st.subheader("AI Morning Brief")
    if not services["claude"]:
        st.warning("Add your Anthropic API key in Settings to enable AI analysis.")
        return

    if st.button("Generate Morning Brief", type="primary"):
        events  = finnhub_client.get_economic_calendar(Config.FINNHUB_API_KEY) if services["finnhub"] else []
        news    = finnhub_client.get_market_news(Config.FINNHUB_API_KEY) if services["finnhub"] else []
        with st.spinner("Claude is analyzing the markets…"):
            brief = claude.generate_morning_brief(futures_data, events, news)
        st.markdown(brief.replace("$", r"\$"))
