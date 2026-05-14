import os
import streamlit as st
from pathlib import Path
from config import Config

ENV_FILE = Path(__file__).parent.parent / ".env"


def _read_env() -> dict:
    result = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                result[k.strip()] = v.strip()
    return result


def _write_env(values: dict):
    lines = []
    for k, v in values.items():
        lines.append(f"{k}={v}")
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def render():
    st.title("Settings")
    st.info("Changes are saved to your `.env` file. Restart the app for new API keys to take effect.")

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
    projectx_user = st.text_input("ProjectX Username (email)", value=env.get("PROJECTX_USERNAME", ""))
    projectx_key  = st.text_input("ProjectX API Key", value=env.get("PROJECTX_API_KEY", ""), type="password",
                                   help="API docs: https://gateway.docs.projectx.com/")
    futures_provider = st.radio(
        "Futures data provider",
        ["yahoo", "projectx"],
        index=0 if env.get("FUTURES_PROVIDER", "yahoo") == "yahoo" else 1,
        horizontal=True,
    )

    st.subheader("Stocks — Provider")
    st.caption("Finnhub provides free real-time quotes (uses same key as Economic Calendar). Charts always use Yahoo Finance for historical data.")
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
        new_env = {
            "ANTHROPIC_API_KEY":     anthropic_key,
            "CLAUDE_MODEL":          claude_model,
            "FINNHUB_API_KEY":       finnhub_key,
            "PROJECTX_USERNAME":     projectx_user,
            "PROJECTX_API_KEY":      projectx_key,
            "FUTURES_PROVIDER":      futures_provider,
            "QUESTRADE_ACCESS_TOKEN": questrade_token,
            "STOCKS_PROVIDER":       stocks_provider,
            "REFRESH_INTERVAL":      str(refresh),
        }
        _write_env(new_env)
        st.success("Settings saved! Restart the app for API key changes to take effect.")

    # ── Status ────────────────────────────────────────────────────────────────
    st.divider()
    st.subheader("Service Status")
    services = Config.validate()
    col1, col2 = st.columns(2)
    checks = [
        ("Claude AI",          services["claude"]),
        ("Finnhub Calendar",   services["finnhub"]),
        ("ProjectX Futures",   services["projectx"]),
        ("Questrade Stocks",   services["questrade"]),
    ]
    for i, (name, ok) in enumerate(checks):
        col = col1 if i % 2 == 0 else col2
        icon = "✅" if ok else "❌ Not configured"
        col.markdown(f"**{name}**: {icon}")
