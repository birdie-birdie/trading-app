import streamlit as st
from config import Config

st.set_page_config(
    page_title=Config.APP_TITLE,
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Lazy imports so each page only loads what it needs
def load_view(name: str):
    if name == "Morning Brief":
        from views.morning_brief import render
    elif name == "Watchlist":
        from views.watchlist import render
    elif name == "Stock Analysis":
        from views.stock_analysis import render
    elif name == "Settings":
        from views.settings import render
    render()


# ── Sidebar navigation ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📈 Trading Intelligence")
    st.markdown("---")

    page = st.radio(
        "Navigation",
        ["Morning Brief", "Watchlist", "Stock Analysis", "Settings"],
        label_visibility="collapsed",
    )

    st.markdown("---")

    # Mini status panel
    services = Config.validate()
    st.markdown("**Services**")
    for name, key in [("Claude AI", "claude"), ("Finnhub", "finnhub"),
                      ("ProjectX", "projectx"), ("Questrade", "questrade")]:
        icon = "🟢" if services[key] else "🔴"
        st.markdown(f"{icon} {name}")

    st.markdown("---")
    st.caption("v1.0  |  Claude Sonnet 4.6")

# ── Render selected page ──────────────────────────────────────────────────────
load_view(page)
