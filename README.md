# Trading Intelligence Dashboard

An AI-powered trading assistant for **ES / NQ index futures day trading** and **U.S. stock analysis** (swing to long-term). Built with Streamlit and Claude AI, tuned to both ICT (Inner Circle Trader) and Smart Money Concepts (SMC) trading strategies.

---

## Table of Contents

- [Features](#features)
- [My ICT Strategy](#my-ict-strategy-inner-circle-trader)
- [My SMC Strategy](#my-smc-strategy-smart-money-concepts)
- [Architecture](#architecture)
- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Running the App](#running-the-app)
- [Feature Guide](#feature-guide)
  - [Morning Brief](#morning-brief)
  - [Watchlist](#watchlist)
  - [Stock Analysis](#stock-analysis)
  - [Settings](#settings)
- [Enabling Real-Time Futures (ProjectX)](#enabling-real-time-futures-projectx)
- [Futures Symbols Reference](#futures-symbols-reference)
- [Managing Your Watchlist](#managing-your-watchlist)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Cost Estimate](#cost-estimate)
- [Roadmap](#roadmap)

---

## Features

| Page | What it does |
|---|---|
| **Morning Brief** | Pre-market ES/NQ snapshot, today's economic events, market news, and an AI session outlook — choose **My ICT** or **My SMC** strategy before generating. Active futures provider shown in caption. |
| **Watchlist** | Manage your U.S. stock watchlist; get AI trading suggestions ranked by timeframe |
| **Stock Analysis** | Analyze **Stocks** or **Futures** (ES=F, NQ=F, MES=F…) — choose instrument type, then run **My ICT** *(default)*, My SMC, technical/fundamental, or earnings analysis with VWAP chart and visual entry map. Active quotes provider shown in caption; futures quotes note delay unless ProjectX is configured. |
| **Settings** | Configure all API keys and provider preferences through the UI |

---

## My ICT Strategy (Inner Circle Trader)

**My ICT** is the default analysis strategy across the app. It applies ICT methodology with fully configurable rules stored in `ict_config.json`. Each rule can be toggled on/off and fine-tuned without touching code — from the **ICT Rules** expander inside the Stock Analysis page.

### Configurable ICT Rules

| Rule | Default | Parameters |
|---|---|---|
| **Market Structure** | On | — |
| **Killzones** | On | London Open 02:00–05:00, NY Open 07:00–09:00, London Close (off) |
| **Power of Three (PO3)** | On | — |
| **Premium / Discount** | On | — |
| **Optimal Trade Entry (OTE)** | On | Fib 0.62–0.79 |
| **Fair Value Gap (FVG)** | On | Min size: 2.0 pts |
| **Order Block** | On | — |
| **Breaker Block** | Off | — |
| **Liquidity** | On | Equal highs, equal lows, swing points |
| **Judas Swing** | On | — |
| **Risk Management** | On | Min R:R 2.0, risk per trade 1% |

Rules are saved to `ict_config.json` and persist across sessions. Only enabled rules are included in the AI prompt, so you can incrementally adopt ICT concepts as you test them.

### ICT Morning Brief Sections

When **My ICT** is selected on the Morning Brief page, Claude delivers:

1. **Market Structure** — current HH/HL or LH/LL for ES and NQ
2. **Dealing Range** — today's range high/low; is price in Premium or Discount?
3. **Killzone** — which killzone is active or upcoming; current PO3 phase
4. **Judas Swing** — false open move direction, if any
5. **Liquidity** — key resting stops (equal highs/lows, swing points)
6. **Setup** — FVG or Order Block entry zone, OTE Fibonacci level if applicable
7. **Economic event risk** — catalysts or setup invalidators
8. **Session bias** — Bullish / Bearish / No Setup for ES and NQ + one actionable insight

---

## My SMC Strategy (Smart Money Concepts)

The **My SMC** strategy is available as an alternative in both the Morning Brief and Stock Analysis pages.

1. **Identify Day High / Day Low** — key liquidity levels to track each session
2. **Identify current trend** — Bullish (higher highs and higher lows) or Bearish (lower highs and lower lows)
3. **Identify Inducement and POIs (Points of Interest)** — areas where price may sweep liquidity before reversing
4. **Entry trigger** — if price breaks the Day High or Low, wait for a **Change of Character (CHOCH)**, then enter on a retracement into a **Fair Value Gap (FVG)** or **Order Block**

### Key Concepts

| Term | Definition |
|---|---|
| **Inducement** | A liquidity sweep designed to trap retail traders before the real move |
| **POI (Point of Interest)** | Key price levels with institutional interest — previous highs/lows, supply/demand zones |
| **CHOCH (Change of Character)** | First sign of trend reversal — price breaks the most recent swing high in a downtrend (or swing low in an uptrend) |
| **FVG (Fair Value Gap)** | A 3-candle price imbalance where the first candle's high and third candle's low don't overlap (bullish), or vice versa (bearish) |
| **Order Block** | The last bullish/bearish candle before a significant opposing move — where institutional orders are likely resting |

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
│   ├── finnhub_client.py      Finnhub  (real-time stocks, economic calendar, news)
│   └── stocks.py              Provider router — dispatches to yahoo or finnhub
│
├── ai/
│   └── claude.py              All Claude API calls (prompt-cached)
│                              • generate_morning_brief_ict()   — ICT-tuned ES/NQ brief
│                              • generate_morning_brief()       — SMC-tuned ES/NQ brief
│                              • analyze_ict()                  — My ICT analysis (dynamic rules)
│                              • get_ict_entry_levels()         — ICT structured JSON entry levels
│                              • analyze_stock_my_strategy()    — My SMC stock analysis
│                              • get_smc_entry_levels()         — SMC structured JSON entry levels
│                              • analyze_stock()                — technical/fundamental analysis
│                              • analyze_earnings()             — earnings report interpretation
│                              • generate_watchlist_suggestions()
│
├── ict_config.json            Configurable ICT rule settings (persisted between sessions)
│
└── views/                     Streamlit page renderers
    ├── morning_brief.py       Morning Brief page (strategy selector: My ICT / My SMC)
    ├── watchlist.py           Watchlist page
    ├── stock_analysis.py      Stock Analysis page (VWAP + ICT/SMC entry map)
    └── settings.py            Settings page
```

### Data Flow

```
Morning Brief  →  ES/NQ quotes  +  economic events  +  news
               →  strategy selector (My ICT / My SMC)
               →  ICT-tuned or SMC-tuned Claude brief

Watchlist      →  quotes + company info  →  Claude ranked suggestions

Stock Analysis →  price history  →  VWAP chart
               →  analysis type (My ICT default / My SMC / Technical / Earnings)
               →  ict_config.json (enabled rules)  →  dynamic ICT prompt
               →  Claude analysis  →  entry map chart
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

Switching providers is a one-line change in `.env` — no code edits required. Charts always use Yahoo Finance regardless of quote provider.

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

# ── Economic Calendar, News & Stock Quotes (recommended, free) ─────────────
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
STOCKS_PROVIDER=finnhub

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
STOCKS_PROVIDER=finnhub
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

- Active **futures provider** shown in caption — reflects which provider *actually served* the quotes (ProjectX or Yahoo Finance fallback)
- Tracks **ES and NQ only** (focused on the contracts you trade)
- Futures table with live prices, change %, high/low — **↺ Refresh** button re-fetches quotes on demand (quotes always refresh on every page interaction too)
- Economic events for today — color-coded by impact (High / Medium / Low)
- Latest market news headlines with source links
- Choose **Analysis strategy** — **My ICT** *(default)* or **My SMC** — before generating
- Click **Generate Morning Brief** → Claude applies your chosen strategy and delivers a session outlook tailored to that framework
- ICT brief includes the actual prior RTH session High/Low/EQ fetched from Yahoo history — no estimated dealing ranges

### Watchlist

- Add any U.S. ticker via the **Manage Watchlist** expander
- Choose timeframe: **Day Trade / Swing / Mid-Term / Long-Term**
- Snapshot table: price, change %, 52-week range, P/E, sector
- Click **Get AI Suggestions** → Claude ranks each stock by opportunity with bias, key level, and a one-line trade idea

### Stock Analysis

- Active **quotes provider** (Yahoo Finance, Finnhub, or Questrade) shown in the page caption

1. Choose **Instrument** — **Stock** or **Futures**
   - **Stock** — enter any U.S. ticker (e.g. `NVDA`, `AAPL`, `TSLA`); quotes via configured stock provider
   - **Futures** — enter a futures symbol (e.g. `ES=F`, `NQ=F`, `MES=F`, `MNQ=F`); quotes via configured futures provider (Yahoo Finance or ProjectX). Shows price, change %, day high/low.
2. Choose analysis type:
   - **My ICT** *(default)* — applies your configurable ICT ruleset. Expand **ICT Rules** to toggle/tune any of the 11 rule categories, then click **Save Rules** to persist them to `ict_config.json`. Only enabled rules are sent to Claude. Generates an **Entry Map chart** showing:
     - Order Block zone (shaded green/red)
     - FVG zone (shaded yellow)
     - CHOCH level (purple line)
     - Entry, Stop Loss, and Target (horizontal lines)
     - Risk/Reward ratio (e.g. `R:R 2.5R`)
   - **My SMC** — applies your Smart Money Concepts strategy: trend, High/Low, POIs, inducement zones, CHOCH + FVG/Order Block entry, invalidation level. Generates the same Entry Map chart as My ICT.
   - **Technical & Fundamental** — general trend analysis, support/resistance, valuation, entry/target/stop *(stocks only)*
   - **Earnings Report** — interprets the most recent earnings: beat/miss, guidance, price reaction expectation, trading recommendation *(stocks only)*
3. Choose timeframe to tailor the AI output

**Charts include:**
- Candlesticks with volume bars
- SMA 20 (orange) and SMA 50 (blue)
- **VWAP** (magenta dotted line) — resets per trading day on intraday charts; anchored from period start on daily/weekly charts

### Settings

- Enter/update API keys (stored in `.env`, never logged)
- Switch futures or stock data provider
- Change Claude model
- Service Status panel shows which integrations are active

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
| `ES=F` | E-mini S&P 500 | CME |
| `NQ=F` | E-mini Nasdaq-100 | CME |
| `MES=F` | Micro E-mini S&P 500 | CME |
| `MNQ=F` | Micro E-mini Nasdaq-100 | CME |
| `YM=F` | E-mini Dow Jones | CBOT |
| `RTY=F` | E-mini Russell 2000 | CME |

> The morning brief tracks **ES and NQ** by default. Edit `FUTURES_WATCHLIST` in `config.py` to add more contracts.

---

## Managing Your Watchlist

Stocks persist in `watchlist.json`. Manage them via the UI or edit the file directly:

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

1. Push project to a **private** GitHub repo (`.env` is already in `.gitignore`)
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app → connect your repo
3. In **Advanced settings → Secrets**, paste your keys in TOML format:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   FINNHUB_API_KEY = "your_key"
   FUTURES_PROVIDER = "yahoo"
   STOCKS_PROVIDER = "finnhub"
   CLAUDE_MODEL = "claude-sonnet-4-6"
   ```
4. Deploy — the app auto-redeploys on every `git push`

> Note: Streamlit Community Cloud has an ephemeral filesystem. Watchlist changes and ICT rule edits made via the UI will reset on restart. Commit your preferred `ict_config.json` and `watchlist.json` to the repo before deploying so they survive redeploys. For fully persistent UI edits, use a cloud database (e.g. Firebase Firestore).

### Option 3 — Docker / Google Cloud Run

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

Deploy to Google Cloud Run to use a custom domain (e.g. `trade.alleasier.ca`).

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` with venv active |
| Futures data shows errors | Yahoo Finance can be flaky; wait a moment and refresh |
| AI buttons do nothing | Verify `ANTHROPIC_API_KEY` is set and valid |
| Economic calendar is empty | Check `FINNHUB_API_KEY` at finnhub.io |
| Entry map not showing | Requires Anthropic API key; Claude generates the levels |
| ProjectX connection fails | Confirm your API subscription is active and credentials are correct |
| Port 8501 already in use | `streamlit run app.py --server.port 8502` |
| Settings changes not applied | Restart the app after saving new API keys |
| Analysis disappears on interact | Fixed via session_state — analysis persists per ticker |

---

## Cost Estimate

| Service | Cost |
|---|---|
| Yahoo Finance | Free |
| Finnhub | Free |
| Claude Sonnet 4.6 | ~$0.003 per morning brief, ~$0.004 per My ICT or My SMC analysis (includes entry map) |
| ProjectX API | $14.50–$29/mo |

**Typical daily AI cost:** < $0.03 (one morning brief + a few stock analyses with entry maps)

---

## Roadmap

- [ ] Questrade real-time stock quotes
- [ ] Auto-refresh on a configurable timer
- [ ] Price alerts (desktop notifications)
- [ ] Trade journal — log and review your trades with ICT/SMC annotations
- [ ] Options chain analysis
- [ ] Simple backtesting panel for ICT/SMC setups
- [ ] Persistent watchlist via Firebase Firestore
