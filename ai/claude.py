"""
All Claude API calls. Uses prompt caching where possible to reduce costs.
"""
import anthropic
from config import Config


def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)


def _ask(system: str, user: str, max_tokens: int = 1024) -> str:
    msg = _client().messages.create(
        model=Config.CLAUDE_MODEL,
        max_tokens=max_tokens,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user}],
    )
    return msg.content[0].text


# ─── Morning Brief ────────────────────────────────────────────────────────────

MORNING_BRIEF_SYSTEM = """You are a professional futures trading analyst specializing in U.S. index futures (MES, MNQ, ES, NQ, YM, RTY).
Your role is to deliver concise, actionable morning briefings to day traders.
Focus on: market sentiment, key price levels, catalysts, and session trading bias.
Be direct. No fluff. Use bullet points where helpful."""


def generate_morning_brief(futures_data: list, economic_events: list, market_news: list) -> str:
    futures_block = "\n".join(
        f"  {f['symbol']}: {f['price']} ({f['change_pct']:+.2f}%)"
        for f in futures_data if "error" not in f
    ) or "  No futures data available."

    events_block = "\n".join(
        f"  {e.get('time','')[:16]}  [{_impact(e)}]  {e.get('event','')}"
        for e in economic_events[:6]
    ) or "  No major economic events scheduled."

    news_block = "\n".join(
        f"  - {n.get('headline', '')}"
        for n in market_news[:5]
    ) or "  No news available."

    user_msg = f"""PRE-MARKET FUTURES:
{futures_block}

TODAY'S ECONOMIC EVENTS:
{events_block}

LATEST MARKET NEWS:
{news_block}

Provide a morning brief covering:
1. Overall market sentiment (Bullish / Bearish / Neutral) with 1-line reasoning
2. Key levels to watch for MES and MNQ (support, resistance)
3. Major catalysts or risks for the session
4. Session trading bias with context
5. One actionable insight for today's session"""

    return _ask(MORNING_BRIEF_SYSTEM, user_msg, max_tokens=1200)


# ─── Watchlist Suggestions ────────────────────────────────────────────────────

WATCHLIST_SYSTEM = """You are an expert stock trader and technical analyst.
Provide clear, scannable trading suggestions for a watchlist.
Format output as a ranked list. Include bias, key level, and setup quality for each stock."""


def generate_watchlist_suggestions(watchlist_data: list, timeframe: str = "swing") -> str:
    if not watchlist_data:
        return "Watchlist is empty. Add stocks to get suggestions."

    stocks_block = "\n".join(
        f"  {s['symbol']}: ${s.get('price', 0):.2f} ({s.get('change_pct', 0):+.2f}%) | "
        f"52w: ${s.get('low52', '?')} – ${s.get('high52', '?')} | Vol: {s.get('volume', '?')}"
        for s in watchlist_data if "error" not in s
    )

    user_msg = f"""WATCHLIST ({timeframe.upper()} TIMEFRAME):
{stocks_block}

For each stock provide:
- Bias: Bullish / Bearish / Neutral
- Key level to watch (price)
- Setup quality: A / B / C
- One-line trade idea

Then rank top 3 opportunities for today."""

    return _ask(WATCHLIST_SYSTEM, user_msg, max_tokens=1500)


# ─── Stock Analysis ───────────────────────────────────────────────────────────

STOCK_ANALYSIS_SYSTEM = """You are a seasoned stock analyst covering both technical and fundamental analysis.
Deliver structured analysis that helps traders make decisions.
Include specific price levels, not vague guidance."""


def analyze_stock(ticker: str, info: dict, history_summary: str, timeframe: str = "swing") -> str:
    price    = info.get("currentPrice") or info.get("regularMarketPrice", "N/A")
    high52   = info.get("fiftyTwoWeekHigh", "N/A")
    low52    = info.get("fiftyTwoWeekLow", "N/A")
    mktcap   = info.get("marketCap", "N/A")
    pe       = info.get("trailingPE", "N/A")
    eps      = info.get("trailingEps", "N/A")
    rev_grow = info.get("revenueGrowth", "N/A")
    sector   = info.get("sector", "N/A")
    name     = info.get("longName", ticker)

    user_msg = f"""Analyze {name} ({ticker}) for a {timeframe} trade.

SNAPSHOT:
  Price: ${price} | 52w: ${low52} – ${high52}
  Market Cap: {mktcap} | P/E: {pe} | EPS: {eps}
  Revenue Growth: {rev_grow} | Sector: {sector}

RECENT PRICE ACTION:
  {history_summary}

Provide:
1. Technical outlook — trend, key support & resistance levels
2. Fundamental snapshot — is valuation reasonable?
3. {timeframe.title()} trade setup — entry zone, target, stop loss
4. Risk/reward ratio
5. Recommendation: Strong Buy / Buy / Hold / Sell / Strong Sell + brief reason"""

    return _ask(STOCK_ANALYSIS_SYSTEM, user_msg, max_tokens=1200)


# ─── Earnings Analysis ────────────────────────────────────────────────────────

EARNINGS_SYSTEM = """You are a buy-side earnings analyst. Interpret earnings reports and translate them into
trading implications. Be precise about what beats/misses mean for the stock price."""


def analyze_earnings(ticker: str, earnings_data: dict, info: dict) -> str:
    price  = info.get("currentPrice") or info.get("regularMarketPrice", "N/A")
    name   = info.get("longName", ticker)
    sector = info.get("sector", "N/A")

    cal = earnings_data.get("calendar", {})
    qe  = earnings_data.get("quarterly_earnings", {})

    user_msg = f"""Analyze the earnings situation for {name} ({ticker}).

COMPANY: {sector} sector | Current price: ${price}

EARNINGS CALENDAR:
  {cal}

RECENT QUARTERLY EARNINGS:
  {qe}

Provide:
1. Earnings trend — are results improving or declining?
2. EPS and Revenue beat/miss assessment
3. What the market likely already priced in
4. Post-earnings price reaction expectation (up / down / flat) with reasoning
5. Trading recommendation: Hold through earnings / Buy before / Wait for reaction / Avoid
6. Key things to watch in the next report"""

    return _ask(EARNINGS_SYSTEM, user_msg, max_tokens=1200)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _impact(event: dict) -> str:
    return {"1": "Low", "2": "Med", "3": "High"}.get(str(event.get("impact", "")), "—")
