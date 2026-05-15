import os
import streamlit as st
from pathlib import Path
from config import Config

ENV_FILE = Path(__file__).parent.parent / ".env"


def _read_env() -> dict:
    """Read .env file. Falls back to current Config values (e.g. on Streamlit Cloud
    where .env doesn't exist and secrets come from the dashboard)."""
    result = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                result[k.strip()] = v.strip()
    # Fill any missing keys from the live Config (covers Streamlit Cloud secrets)
    defaults = {
        "ANTHROPIC_API_KEY":      Config.ANTHROPIC_API_KEY,
        "CLAUDE_MODEL":           Config.CLAUDE_MODEL,
        "FINNHUB_API_KEY":        Config.FINNHUB_API_KEY,
        "PROJECTX_USERNAME":      Config.PROJECTX_USERNAME,
        "PROJECTX_API_KEY":       Config.PROJECTX_API_KEY,
        "FUTURES_PROVIDER":       Config.FUTURES_PROVIDER,
        "STOCKS_PROVIDER":        Config.STOCKS_PROVIDER,
        "QUESTRADE_ACCESS_TOKEN": Config.QUESTRADE_ACCESS_TOKEN,
        "REFRESH_INTERVAL":       str(Config.REFRESH_INTERVAL),
    }
    for k, v in defaults.items():
        result.setdefault(k, v)
    return result


def _write_env(values: dict):
    """Write values to .env (local persistence). No-op if path isn't writable."""
    try:
        lines = [f"{k}={v}" for k, v in values.items()]
        ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except Exception:
        pass  # Streamlit Cloud has a read-only filesystem in some configs


def render():
    st.title("Settings")

    on_cloud = not ENV_FILE.exists()
    if on_cloud:
        st.info(
            "Running on Streamlit Cloud — changes apply to this session immediately. "
            "For permanent changes, update your app secrets in the Streamlit Cloud dashboard."
        )
    else:
        st.info("Changes apply immediately — no restart required.")

    env = _read_env()

    st.subheader("AI — Anthropic")
    anthropic_key = st.text_input(
        "Anthropic API Key",
        value=env.get("ANTHROPIC_API_KEY", ""),
        type="password",
        help="Get one at https://console.anthropic.com",
    )
    claude_model = st.selectbox(
        "Claude Model",
        ["claude-sonnet-4-6", "claude-opus-4-7", "claude-haiku-4-5-20251001"],
        index=["claude-sonnet-4-6", "claude-opus-4-7", "claude-haiku-4-5-20251001"].index(
            env.get("CLAUDE_MODEL", "claude-sonnet-4-6")
        ),
    )

    st.subheader("Economic Calendar & News — Finnhub")
    finnhub_key = st.text_input(
        "Finnhub API Key",
        value=env.get("FINNHUB_API_KEY", ""),
        type="password",
        help="Free key at https://finnhub.io/register",
    )

    st.subheader("Futures — ProjectX / TopstepX")
    projectx_user = st.text_input("ProjectX Username", value=env.get("PROJECTX_USERNAME", ""))
    projectx_key  = st.text_input("ProjectX API Key", value=env.get("PROJECTX_API_KEY", ""),
                                   type="password",
                                   help="API docs: https://gateway.docs.projectx.com/")
    futures_provider = st.radio(
        "Futures data provider",
        ["yahoo", "projectx"],
        index=0 if env.get("FUTURES_PROVIDER", "yahoo") == "yahoo" else 1,
        horizontal=True,
    )

    st.subheader("Stocks — Provider")
    st.caption("Finnhub provides free real-time quotes. Charts always use Yahoo Finance for historical data.")
    stocks_provider_options = ["yahoo", "finnhub", "questrade"]
    current_sp = env.get("STOCKS_PROVIDER", "yahoo")
    stocks_provider = st.radio(
        "Stock data provider",
        stocks_provider_options,
        index=stocks_provider_options.index(current_sp) if current_sp in stocks_provider_options else 0,
        horizontal=True,
        captions=["Free, ~15 min delay", "Free, real-time (uses Finnhub key above)", "Real-time (planned)"],
    )

    st.subheader("Stocks — Questrade (planned)")
    questrade_token = st.text_input(
        "Questrade Access Token",
        value=env.get("QUESTRADE_ACCESS_TOKEN", ""),
        type="password",
    )

    st.subheader("App")
    refresh = st.number_input(
        "Auto-refresh interval (seconds)",
        min_value=10, max_value=300,
        value=int(env.get("REFRESH_INTERVAL", "60")),
    )

    if st.button("Save Settings", type="primary"):
        new_values = {
            "ANTHROPIC_API_KEY":      anthropic_key,
            "CLAUDE_MODEL":           claude_model,
            "FINNHUB_API_KEY":        finnhub_key,
            "PROJECTX_USERNAME":      projectx_user,
            "PROJECTX_API_KEY":       projectx_key,
            "FUTURES_PROVIDER":       futures_provider,
            "STOCKS_PROVIDER":        stocks_provider,
            "QUESTRADE_ACCESS_TOKEN": questrade_token,
            "REFRESH_INTERVAL":       str(refresh),
        }
        # 1. Persist to .env for local use
        _write_env(new_values)
        # 2. Push into os.environ immediately (no restart needed)
        for k, v in new_values.items():
            os.environ[k] = v
        # 3. Reload Config class attributes from the updated os.environ
        Config.reload()
        st.success("Settings saved and applied.")

    # ── Status ────────────────────────────────────────────────────────────────
    st.divider()
    st.subheader("Service Status")
    services = Config.validate()
    col1, col2 = st.columns(2)
    checks = [
        ("Claude AI",        services["claude"]),
        ("Finnhub Calendar", services["finnhub"]),
        ("ProjectX Futures", services["projectx"]),
        ("Questrade Stocks", services["questrade"]),
    ]
    for i, (name, ok) in enumerate(checks):
        col = col1 if i % 2 == 0 else col2
        icon = "✅" if ok else "❌ Not configured"
        col.markdown(f"**{name}**: {icon}")
