import streamlit as st
from config import Config

st.set_page_config(
    page_title=Config.APP_TITLE,
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Auth ──────────────────────────────────────────────────────────────────────

def _login_gate() -> bool:
    """
    Returns True if the user is authenticated.
    If APP_USERNAME / APP_PASSWORD are not set in .env, auth is skipped.
    """
    # Skip auth if no credentials configured
    if not Config.APP_USERNAME or not Config.APP_PASSWORD:
        return True

    if st.session_state.get("authenticated"):
        return True

    # Centre the login form
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("## Trading AI Dashboard")
        st.markdown("Please sign in to continue.")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In", use_container_width=True)

        if submitted:
            if username == Config.APP_USERNAME and password == Config.APP_PASSWORD:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Incorrect username or password.")

    return False


# ── Guard ─────────────────────────────────────────────────────────────────────

if not _login_gate():
    st.stop()


# ── Lazy page loader ──────────────────────────────────────────────────────────

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


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 📈 Trading AI")
    st.markdown("---")

    page = st.radio(
        "Navigation",
        ["Morning Brief", "Watchlist", "Stock Analysis", "Settings"],
        label_visibility="collapsed",
    )

    st.markdown("---")

    # Service status
    services = Config.validate()
    st.markdown("**Services**")
    for name, key in [("Claude AI", "claude"), ("Finnhub", "finnhub"),
                      ("ProjectX", "projectx"), ("Questrade", "questrade")]:
        icon = "🟢" if services[key] else "🔴"
        st.markdown(f"{icon} {name}")

    st.markdown("---")

    # Logout (only shown if auth is enabled)
    if Config.APP_USERNAME:
        if st.button("Sign Out", use_container_width=True):
            st.session_state["authenticated"] = False
            st.rerun()

    st.caption("v1.0  |  Claude Sonnet 4.6")


# ── Render page ───────────────────────────────────────────────────────────────

load_view(page)
