# Trading Intelligence Dashboard

An AI-powered trading assistant for **index futures day trading** (MES / MNQ) and **U.S. stock analysis** (swing to long-term). Built with Streamlit and Claude AI.

---

## Features

| Page | What it does |
|---|---|
| **Morning Brief** | Pre-market futures snapshot, today's economic events, market news, and an AI-generated session outlook |
| **Watchlist** | Manage your U.S. stock watchlist; get AI trading suggestions ranked by timeframe |
| **Stock Analysis** | On-demand technical + fundamental analysis, or earnings report interpretation, for any ticker |
| **Settings** | Configure all API keys and provider preferences through the UI |

---

## Architecture

```
Trading Intelligence Dashboard
│
├── app.py                     Streamlit entry point & sidebar navigation
├── config.py                  Central config — reads from .env
│
├── providers/                 Pluggable data adapters
│   ├── yahoo.py               Yahoo Finance  (stocks + futures, free default)
│   ├── projectx.py            ProjectX / TopstepX  (real-time futures)
│   └── finnhub_client.py      Finnhub  (economic calendar + news)
│
├── ai/
│   └── claude.py              All Claude API calls (prompt-cached)
│
└── views/                     Streamlit page renderers
    ├── morning_brief.py       Morning Brief page
    ├── watchlist.py           Watchlist page
    ├── stock_analysis.py      Stock Analysis page
    └── settings.py            Settings page
```

### Data Flow

```
Morning Brief  →  futures quotes  +  economic events  +  news  →  Claude AI brief
Watchlist      →  quotes + company info  →  Claude AI ranked suggestions
Stock Analysis →  price history + financials  →  Claude AI analysis / earnings
```

### Provider Matrix

| Data | Default (free) | Real-time (free) | Real-time (paid) |
|---|---|---|---|
| Futures quotes | Yahoo Finance — ~15 min delay | — | ProjectX / TopstepX API |
| Stock quotes | Yahoo Finance — ~15 min delay | **Finnhub** (same free key) | Questrade *(planned)* |
| Stock charts | Yahoo Finance (historical OHLCV) | Yahoo Finance | Yahoo Finance |
| Economic calendar | Finnhub free tier | — | — |
| Market news | Finnhub free tier | — | — |
| AI analysis | Claude (Anthropic) | — | — |

Switching providers is a one-line change in `.env` — no code edits required. Charts always use Yahoo Finance regardless of quote provider (best free historical data source).

---

## Requirements

- Python **3.11+**
- At minimum: an **Anthropic API key** (all other data sources have free tiers)

---

## Quick Start

```powershell
# 1. Navigate to project folder
cd "D:\dev\ai trading\Decision n Strategy"

# 2. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up your API keys
copy .env.example .env
notepad .env          # add your keys (see Configuration section below)

# 5. Run the app
streamlit run app.py
```

The app opens in your browser at **http://localhost:8501**.

---

## Configuration

All settings live in the `.env` file. You can also edit them from the **Settings** page inside the app — changes are written back to `.env` automatically.

### `.env` File Reference

```env
# ── AI (required) ──────────────────────────────────────────────────────────
ANTHROPIC_API_KEY=sk-ant-...

# Claude model to use
# Options: claude-sonnet-4-6 | claude-opus-4-7 | claude-haiku-4-5-20251001
CLAUDE_MODEL=claude-sonnet-4-6

# ── Economic Calendar & News (recommended, free) ───────────────────────────
FINNHUB_API_KEY=your_finnhub_key

# ── Futures: ProjectX / TopstepX (optional, real-time) ────────────────────
PROJECTX_USERNAME=your_topstepx_email@example.com
PROJECTX_API_KEY=your_projectx_api_key

# ── Stocks: Questrade (optional, planned) ─────────────────────────────────
QUESTRADE_ACCESS_TOKEN=

# ── Provider selection ─────────────────────────────────────────────────────
# "yahoo"    → free, ~15 min delayed
# "projectx" → real-time (requires ProjectX credentials above)
FUTURES_PROVIDER=yahoo

# "yahoo"    → free, ~15 min delay
# "finnhub"  → real-time, free (reuses FINNHUB_API_KEY — charts still use yfinance)
# "questrade"→ real-time (planned)
STOCKS_PROVIDER=yahoo

# ── App ────────────────────────────────────────────────────────────────────
REFRESH_INTERVAL=60
```

### API Keys — Where to Get Them

| Key | Required | Cost | Link |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | **Yes** | Pay-per-use (~$0.02/day typical) | [console.anthropic.com](https://console.anthropic.com) |
| `FINNHUB_API_KEY` | Recommended | Free (60 req/min) | [finnhub.io/register](https://finnhub.io/register) |
| `PROJECTX_API_KEY` | Optional | $29/mo (50% off for Topstep Traders) | [gateway.docs.projectx.com](https://gateway.docs.projectx.com) |
| `QUESTRADE_ACCESS_TOKEN` | Optional | Free with account | Questrade API portal |

### Minimum setup (free data, AI-only cost)

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
# Activate virtual environment first
.venv\Scripts\Activate.ps1

# Start app (default port 8501)
streamlit run app.py

# Custom port
streamlit run app.py --server.port 8502
```

---

## Feature Guide

### Morning Brief

- Futures table (MES, MNQ, ES, NQ, YM, RTY) with live prices, change %, high/low
- Economic events for today — color-coded by impact (High / Medium / Low)
- Latest market news headlines
- Click **Generate Morning Brief** → Claude delivers: market sentiment, key MES/MNQ levels, session risks, trading bias, and one actionable insight

### Watchlist

- Add any U.S. ticker via the **Manage Watchlist** expander
- Choose timeframe: **Day Trade / Swing / Mid-Term / Long-Term**
- Snapshot table: price, change %, 52-week range, P/E, sector
- Click **Get AI Suggestions** → Claude ranks each stock by opportunity and gives a one-line trade idea per name

### Stock Analysis

1. Enter a ticker symbol (e.g. `NVDA`, `AAPL`, `TSLA`)
2. Choose analysis type:
   - **Technical & Fundamental** — candlestick chart with SMA 20/50 + volume, key metrics, AI analysis with entry/target/stop
   - **Earnings Report** — Claude interprets the most recent earnings: beat/miss, guidance, price reaction expectation, trading recommendation
3. Choose timeframe to tailor the AI output

### Settings

- Enter/update API keys (stored in `.env`, never logged)
- Switch futures or stock data provider
- Change Claude model
- Service Status panel shows which integrations are active (green/red)

---

## Enabling Real-Time Futures (ProjectX)

1. Subscribe to **API Access** on the ProjectX platform
   - Go to your TopstepX account → ProjectX → Settings → API
   - Cost: $29/mo — Topstep Traders get 50% off → ~$14.50/mo
2. Get your API credentials from [gateway.docs.projectx.com](https://gateway.docs.projectx.com)
3. Update `.env`:
   ```env
   PROJECTX_USERNAME=your@email.com
   PROJECTX_API_KEY=your_key_here
   FUTURES_PROVIDER=projectx
   ```
4. Restart the app

---

## Futures Symbols Reference

| Symbol (Yahoo) | Contract | Exchange |
|---|---|---|
| `MES=F` | Micro E-mini S&P 500 | CME |
| `MNQ=F` | Micro E-mini Nasdaq-100 | CME |
| `ES=F` | E-mini S&P 500 | CME |
| `NQ=F` | E-mini Nasdaq-100 | CME |
| `YM=F` | E-mini Dow Jones | CBOT |
| `RTY=F` | E-mini Russell 2000 | CME |

> The ProjectX provider uses the short form (MES, MNQ, ES…) — the mapping is handled automatically.

---

## Managing Your Watchlist

Stocks persist in `watchlist.json`. You can manage them via the UI or edit the file directly:

```json
{
  "stocks": ["AAPL", "NVDA", "MSFT", "TSLA", "AMZN"]
}
```

---

## Deployment

### Option 1 — Windows Task Scheduler (run on startup)

Create `start_trading_app.bat`:

```bat
@echo off
cd /d "D:\dev\ai trading\Decision n Strategy"
call .venv\Scripts\activate.bat
streamlit run app.py --server.port 8501 --server.headless true
```

Add it to Task Scheduler → trigger on user logon.

### Option 2 — Streamlit Community Cloud (free, browser-accessible anywhere)

1. Push project to a **private** GitHub repo (add `.env` to `.gitignore`)
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app → connect your repo
3. In **Advanced settings → Secrets**, paste your `.env` contents in TOML format:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   FINNHUB_API_KEY = "your_key"
   FUTURES_PROVIDER = "yahoo"
   STOCKS_PROVIDER = "yahoo"
   CLAUDE_MODEL = "claude-sonnet-4-6"
   ```

### Option 3 — Docker

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

| Problem | Solution |
|---|---|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` with venv active |
| Futures data shows errors | Yahoo Finance can be flaky; wait a moment and refresh |
| AI buttons do nothing | Verify `ANTHROPIC_API_KEY` is set and valid |
| Economic calendar is empty | Check `FINNHUB_API_KEY` at finnhub.io |
| ProjectX connection fails | Confirm your API subscription is active and credentials are correct |
| Port 8501 already in use | `streamlit run app.py --server.port 8502` |
| Settings changes not applied | Restart the app after saving new API keys |

---

## Cost Estimate

| Service | Cost |
|---|---|
| Yahoo Finance | Free |
| Finnhub | Free |
| Claude Sonnet 4.6 | ~$0.003 per morning brief, ~$0.002 per stock analysis |
| ProjectX API | $14.50–$29/mo |

**Typical daily AI cost:** < $0.02 (one morning brief + a few stock analyses)

---

## Roadmap

- [ ] Questrade real-time stock quotes
- [ ] Auto-refresh on a configurable timer
- [ ] Price alerts (desktop notifications)
- [ ] Trade journal — log and review your trades
- [ ] Options chain analysis
- [ ] Simple backtesting panel
