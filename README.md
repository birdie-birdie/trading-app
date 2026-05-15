# Trading Intelligence Dashboard

An AI-powered trading assistant for **ES / NQ index futures day trading** and **U.S. stock analysis** (swing to long-term). Built with Streamlit and Claude AI, and tuned to a Smart Money Concepts (SMC) trading strategy.

---

## Features

| Page | What it does |
|---|---|
| **Morning Brief** | Pre-market ES/NQ snapshot, today's economic events, market news, and an SMC-based AI session outlook |
| **Watchlist** | Manage your U.S. stock watchlist; get AI trading suggestions ranked by timeframe |
| **Stock Analysis** | On-demand My SMC, My ICT, technical/fundamental, or earnings analysis for any ticker — with VWAP chart and visual entry map |
| **Settings** | Configure all API keys and provider preferences through the UI |

---

## My SMC Strategy (Smart Money Concepts)

The AI analysis throughout this app is tuned to the following strategy for **ES and NQ futures** and **U.S. stocks**:

1. **Identify Day High / Day Low** — these are the key liquidity levels to track each session
2. **Identify current trend** — Bullish (higher highs and higher lows) or Bearish (lower highs and lower lows)
3. **Identify Inducement and POIs (Points of Interest)** — areas where price may sweep liquidity (equal highs/lows, previous session highs/lows) before reversing
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

## My ICT Strategy (Inner Circle Trader)

The **My ICT** analysis type applies ICT methodology with fully configurable rules stored in `ict_config.json`. Each rule can be toggled on/off and fine-tuned without touching code — from the **ICT Rules** expander inside the Stock Analysis page.

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
│                              • generate_morning_brief()       — SMC-tuned ES/NQ brief
│                              • analyze_stock_my_strategy()    — My SMC stock analysis
│                              • get_smc_entry_levels()         — structured JSON entry levels
│                              • analyze_ict()                  — My ICT analysis (dynamic rules)
│                              • get_ict_entry_levels()         — ICT structured JSON entry levels
│                              • analyze_stock()                — technical/fundamental analysis
│                              • analyze_earnings()             — earnings report interpretation
│                              • generate_watchlist_suggestions()
│
├── ict_config.json            Configurable ICT rule settings (persisted between sessions)
│
└── views/                     Streamlit page renderers
    ├── morning_brief.py       Morning Brief page
    ├── watchlist.py           Watchlist page
    ├── stock_analysis.py      Stock Analysis page (VWAP + SMC/ICT entry map)
    └── settings.py            Settings page
```

### Data Flow

```
Morning Brief  →  ES/NQ quotes  +  economic events  +  news  →  SMC-tuned Claude brief
Watchlist      →  quotes + company info  →  Claude ranked suggestions
Stock Analysis →  price history  →  VWAP chart  →  Claude SMC/ICT analysis  →  entry map chart
               →  ict_config.json (enabled rules)  →  dynamic ICT prompt  →  ICT entry map
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

- Tracks **ES and NQ only** (focused on the contracts you trade)
- Futures table with live prices, change %, high/low
- Economic events for today — color-coded by impact (High / Medium / Low)
- Latest market news headlines with source links
- Click **Generate Morning Brief** → Claude applies your SMC strategy and delivers:
  - Trend direction (Bullish / Bearish) for ES and NQ
  - Day High / Day Low and major POIs with approximate price levels
  - Inducement zones — where liquidity may be swept before the real move
  - Potential CHOCH + FVG / Order Block entry setup
  - Economic event risks that could invalidate setups
  - Session bias and one actionable insight

### Watchlist

- Add any U.S. ticker via the **Manage Watchlist** expander
- Choose timeframe: **Day Trade / Swing / Mid-Term / Long-Term**
- Snapshot table: price, change %, 52-week range, P/E, sector
- Click **Get AI Suggestions** → Claude ranks each stock by opportunity with bias, key level, and a one-line trade idea

### Stock Analysis

1. Enter any U.S. ticker (e.g. `NVDA`, `AAPL`, `TSLA`)
2. Choose analysis type:
   - **My SMC** *(default)* — applies your Smart Money Concepts strategy: trend, High/Low, POIs, inducement zones, CHOCH + FVG/Order Block entry, invalidation level. Generates an **Entry Map chart** showing:
     - Order Block zone (shaded green/red)
     - FVG zone (shaded yellow)
     - CHOCH level (purple line)
     - Entry, Stop Loss, and Target (horizontal lines)
     - Risk/Reward ratio (e.g. `R:R 2.5R`)
   - **My ICT** — applies your configurable ICT ruleset. Expand **ICT Rules** to toggle/tune any of the 11 rule categories, then click **Save Rules** to persist them to `ict_config.json`. Only enabled rules are sent to Claude. Generates the same Entry Map chart as My SMC.
   - **Technical & Fundamental** — general trend analysis, support/resistance, valuation, entry/target/stop
   - **Earnings Report** — interprets the most recent earnings: beat/miss, guidance, price reaction expectation, trading recommendation
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
| Claude Sonnet 4.6 | ~$0.003 per morning brief, ~$0.004 per My SMC or My ICT analysis (includes entry map) |
| ProjectX API | $14.50–$29/mo |

**Typical daily AI cost:** < $0.03 (one morning brief + a few stock analyses with entry maps)

---

## Roadmap

- [ ] Questrade real-time stock quotes
- [ ] Auto-refresh on a configurable timer
- [ ] Price alerts (desktop notifications)
- [ ] Trade journal — log and review your trades with SMC annotations
- [ ] Options chain analysis
- [ ] Simple backtesting panel for SMC setups
- [ ] Persistent watchlist via Firebase Firestore
