import json
import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
from config import Config
from providers import yahoo, finnhub_client
from ai import claude

ICT_CONFIG_FILE = Path(__file__).parent.parent / "ict_config.json"


def _load_ict_config() -> dict:
    try:
        return json.loads(ICT_CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _futures_quotes() -> tuple[list, str]:
    """Returns (quotes, provider_name). Falls back to Yahoo if ProjectX fails."""
    if Config.FUTURES_PROVIDER == "projectx" and Config.validate()["projectx"]:
        from providers import projectx
        quotes = projectx.get_multiple_quotes(
            Config.FUTURES_WATCHLIST, Config.PROJECTX_USERNAME, Config.PROJECTX_API_KEY
        )
        if any("error" not in q for q in quotes):
            return quotes, "ProjectX (real-time)"
    quotes = yahoo.get_multiple_quotes(Config.FUTURES_WATCHLIST)
    return quotes, "Yahoo Finance"


def render():
    st.title("Morning Brief")
    services = Config.validate()

    # ── Futures Overview ──────────────────────────────────────────────────────
    col_hdr, col_refresh = st.columns([6, 1])
    with col_hdr:
        st.subheader("Index Futures")
    with col_refresh:
        st.button("↺ Refresh", help="Click to fetch latest quotes")

    with st.spinner("Fetching futures data…"):
        futures_data, futures_provider = _futures_quotes()

    try:
        from zoneinfo import ZoneInfo
        et = datetime.now(ZoneInfo("America/New_York"))
    except Exception:
        et = datetime.now(timezone.utc)
    st.caption(
        f"As of {et.strftime('%A, %B %d %Y  %H:%M ET')}"
        f"  |  Futures: {futures_provider}"
    )

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

    strategy = st.selectbox(
        "Analysis strategy",
        ["My ICT", "My SMC"],
        help="Which strategy framework Claude should apply to the brief",
    )

    if st.button("Generate Morning Brief", type="primary"):
        events  = finnhub_client.get_economic_calendar(Config.FINNHUB_API_KEY) if services["finnhub"] else []
        news    = finnhub_client.get_market_news(Config.FINNHUB_API_KEY) if services["finnhub"] else []
        with st.spinner("Claude is analyzing the markets…"):
            if strategy == "My ICT":
                cfg = _load_ict_config()
                prior = {
                    sym: yahoo.get_prior_session(sym)
                    for sym in Config.FUTURES_WATCHLIST
                }
                brief = claude.generate_morning_brief_ict(futures_data, events, news, cfg, prior)
            else:
                brief = claude.generate_morning_brief(futures_data, events, news)
        st.markdown(brief.replace("$", r"\$"))
