# Trading Intelligence Dashboard — Documentation

## Overview

A Streamlit-based AI trading assistant designed for a day trader who trades **MES/MNQ index futures** and **U.S. stocks** (swing to long-term). Powered by Claude AI (Anthropic), it delivers three core capabilities:

| Feature | Description |
|---|---|
| **Morning Brief** | Pre-market futures snapshot, economic calendar, market news, and AI-generated trading outlook |
| **Watchlist** | Manage a U.S. stock watchlist; get AI trading suggestions by timeframe |
| **Stock Analysis** | On-demand technical/fundamental analysis or earnings report interpretation for any stock |

---

## Architecture

```
trading-app/
├── app.py                     # Streamlit entry point & navigation
├── config.py                  # Central config — reads from .env
├── .env                       # Your API keys (never commit this)
├── .env.example               # Template — safe to commit
├── requirements.txt           # Python dependencies
├── watchlist.json             # Persisted watchlist (auto-managed)
│
├── providers/                 # Data source adapters
│   ├── yahoo.py               # Yahoo Finance (stocks + futures, default)
│   ├── projectx.py            # ProjectX/TopstepX (real-time futures)
│   └── finnhub_client.py      # Finnhub (economic calendar + news)
│
├── ai/
│   └── claude.py              # All Claude API calls (prompt-cached)
│
└── views/                     # Streamlit page renderers
    ├── morning_brief.py       # Morning Brief page
    ├── watchlist.py           # Watchlist page
    ├── stock_analysis.py      # Stock Analysis page
    └── settings.py            # Settings page (UI for .env)
```

### Data Flow

```
User opens app
    │
    ├── Morning Brief
    │       ├── providers/yahoo.py  OR  providers/projectx.py  →  futures quotes
    │       ├── providers/finnhub_client.py  →  economic events + news
    │       └── ai/claude.py  →  AI morning brief text
    │
    ├── Watchlist
    │       ├── watchlist.json  →  persisted ticker list
    │       ├── providers/yahoo.py  →  quotes + company info
    │       └── ai/claude.py  →  AI trading suggestions
    │
    └── Stock Analysis
            ├── providers/yahoo.py  →  price history + company info + earnings
            └── ai/claude.py  →  AI stock / earnings analysis
```

### Provider Architecture (pluggable)

| Data Type | Default (free) | Premium (real-time) |
|---|---|---|
| Futures quotes | Yahoo Finance (yfinance) | ProjectX / TopstepX API |
| Stock quotes | Yahoo Finance (yfinance) | Questrade API *(coming soon)* |
| Economic calendar | Finnhub (free tier) | — |
| Market news | Finnhub (free tier) | — |
| AI analysis | Claude (Anthropic) | — |

Switching providers requires a single environment variable change — no code edits.

---

## Prerequisites

- Python 3.11 or higher
- API keys (see Configuration section below)

---

## Installation

**1. Clone / navigate to the project folder**

```powershell
cd "D:\dev\ai trading\Decision n Strategy"
```

**2. Create a virtual environment**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**3. Install dependencies**

```powershell
pip install -r requirements.txt
```

**4. Set up your API keys**

```powershell
copy .env.example .env
# Then open .env in any text editor and fill in your keys
```

---

## Configuration

All settings live in the `.env` file in the project root. You can also edit them through the app's **Settings** page (sidebar → Settings), which writes back to `.env`.

### API Keys

| Variable | Required | Where to get it |
|---|---|---|
| `ANTHROPIC_API_KEY` | **Yes** — AI features need this | [console.anthropic.com](https://console.anthropic.com) |
| `FINNHUB_API_KEY` | Recommended — economic calendar & news | [finnhub.io/register](https://finnhub.io/register) (free) |
| `PROJECTX_USERNAME` | Optional — real-time futures | Your TopstepX login email |
| `PROJECTX_API_KEY` | Optional — real-time futures | [gateway.docs.projectx.com](https://gateway.docs.projectx.com) ($29/mo, 50% off for Topstep Traders) |
| `QUESTRADE_ACCESS_TOKEN` | Optional — future integration | Questrade API portal |

### Provider Selection

```env
# Futures quotes: "yahoo" (free, ~15min delay) or "projectx" (real-time)
FUTURES_PROVIDER=yahoo

# Stock quotes: "yahoo" (free) or "questrade" (real-time, future)
STOCKS_PROVIDER=yahoo
```

### App Settings

```env
# Claude model to use for AI analysis
# Options: claude-sonnet-4-6 | claude-opus-4-7 | claude-haiku-4-5-20251001
CLAUDE_MODEL=claude-sonnet-4-6

# Page auto-refresh interval in seconds (not currently auto-refreshed — manual)
REFRESH_INTERVAL=60
```

### Minimum `.env` to get started (free, no paid APIs)

```env
ANTHROPIC_API_KEY=sk-ant-...
FINNHUB_API_KEY=your_finnhub_key
FUTURES_PROVIDER=yahoo
STOCKS_PROVIDER=yahoo
CLAUDE_MODEL=claude-sonnet-4-6
```

---

## Running the App

```powershell
# Make sure your virtual environment is active
.venv\Scripts\Activate.ps1

# Launch
streamlit run app.py
```

The app opens automatically in your browser at `http://localhost:8501`.

---

## Feature Guide

### Morning Brief

Navigate to **Morning Brief** in the sidebar.

- The futures table loads automatically — color-coded green/red
- Economic events show today's scheduled releases (requires Finnhub key)
- Click **Generate Morning Brief** for the AI analysis
- The brief covers: market sentiment, key levels for MES/MNQ, session risks, trading bias, and one actionable insight

### Watchlist

Navigate to **Watchlist** in the sidebar.

- Click **Manage Watchlist** to add or remove tickers
- Select a **trading timeframe** (Day Trade / Swing / Mid-Term / Long-Term)
- The snapshot table shows price, change, 52-week range, P/E, and sector
- Click **Get AI Suggestions** to have Claude rank and assess each stock for your timeframe

### Stock Analysis

Navigate to **Stock Analysis** in the sidebar.

- Enter any U.S. stock ticker (e.g. `AAPL`, `NVDA`, `TSLA`)
- Choose **Technical & Fundamental** for price action + valuation analysis
- Choose **Earnings Report** for Claude to interpret the most recent earnings data
- A candlestick chart with SMA 20/50 and volume renders automatically
- Key metrics (P/E, EPS, 52-week range, market cap, revenue growth) are shown above the AI analysis

### Settings

Navigate to **Settings** in the sidebar.

- Enter API keys (stored securely in `.env`, never displayed in logs)
- Switch futures/stock providers
- Change Claude model
- The **Service Status** section shows which services are active

---

## Futures Symbols Reference

| Symbol | Contract |
|---|---|
| `MES=F` | Micro E-mini S&P 500 |
| `MNQ=F` | Micro E-mini Nasdaq-100 |
| `ES=F` | E-mini S&P 500 |
| `NQ=F` | E-mini Nasdaq-100 |
| `YM=F` | E-mini Dow Jones |
| `RTY=F` | E-mini Russell 2000 |

These are the Yahoo Finance symbols. ProjectX uses the shorter names (MES, MNQ, ES, NQ, YM, RTY) — the mapping is handled automatically in `providers/projectx.py`.

---

## Switching to ProjectX (Real-Time Futures)

1. Subscribe to API Access on the ProjectX platform ($29/mo — check for your Topstep 50% discount)
2. Get your API key from [gateway.docs.projectx.com](https://gateway.docs.projectx.com)
3. Open Settings in the app (or edit `.env`):
   ```env
   PROJECTX_USERNAME=your@email.com
   PROJECTX_API_KEY=your_key_here
   FUTURES_PROVIDER=projectx
   ```
4. Restart the app

---

## Adding Stocks to Your Watchlist

Stocks are saved to `watchlist.json` in the project root. You can:
- Add them via the **Watchlist → Manage Watchlist** UI
- Edit `watchlist.json` directly:
  ```json
  {
    "stocks": ["AAPL", "NVDA", "MSFT", "TSLA", "AMZN"]
  }
  ```

---

## Deployment (Optional)

### Run on Windows startup (background)

Create a `.bat` file:

```bat
@echo off
cd /d "D:\dev\ai trading\Decision n Strategy"
call .venv\Scripts\activate.bat
streamlit run app.py --server.port 8501 --server.headless true
```

Pin it to Task Scheduler to auto-start each morning.

### Streamlit Community Cloud (free hosting)

1. Push the project to a private GitHub repo (ensure `.env` is in `.gitignore`)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo and set environment variables in the Streamlit Secrets panel

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```powershell
docker build -t trading-app .
docker run -p 8501:8501 --env-file .env trading-app
```

---

## Troubleshooting

| Issue | Fix |
|---|---|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` with the venv active |
| Futures show `—` or errors | Yahoo Finance data can be delayed; try refreshing |
| AI button does nothing | Check `ANTHROPIC_API_KEY` is set correctly in `.env` |
| Economic calendar empty | Verify `FINNHUB_API_KEY` is valid at finnhub.io |
| ProjectX connection fails | Confirm credentials and that your API subscription is active |
| Port 8501 already in use | Run `streamlit run app.py --server.port 8502` |

---

## Cost Estimates

| Service | Cost |
|---|---|
| Yahoo Finance | Free |
| Finnhub | Free (60 calls/min) |
| Anthropic Claude Sonnet 4.6 | ~$0.003 per morning brief, ~$0.002 per stock analysis |
| ProjectX API | $29/mo (or ~$14.50 with Topstep 50% discount) |

Daily AI usage for one morning brief + 5 stock analyses ≈ **< $0.02/day**.

---

## Roadmap (Future Enhancements)

- [ ] Questrade real-time stock quotes integration
- [ ] Auto-refresh on a timer (st.rerun with interval)
- [ ] Price alerts (email/desktop notification)
- [ ] Trade journal — log and review your trades
- [ ] Backtesting panel for simple strategies
- [ ] Options chain analysis
