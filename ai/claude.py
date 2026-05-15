"""
All Claude API calls. Uses prompt caching where possible to reduce costs.
"""
import time
import anthropic
from config import Config


def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)


def _ask(system: str, user: str, max_tokens: int = 1024) -> str:
    """Call Claude with automatic retry on overload (529) errors."""
    last_error = None
    for attempt, wait in enumerate([0, 5, 15]):
        if wait:
            time.sleep(wait)
        try:
            msg = _client().messages.create(
                model=Config.CLAUDE_MODEL,
                max_tokens=max_tokens,
                system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
                messages=[{"role": "user", "content": user}],
            )
            return msg.content[0].text
        except anthropic.APIStatusError as e:
            last_error = e
            if e.status_code == 529 and attempt < 2:
                continue  # retry on overload
            raise
    raise last_error


# ─── Morning Brief ────────────────────────────────────────────────────────────

MORNING_BRIEF_SYSTEM = """You are my personal futures trading analyst for ES and NQ.

My trading strategy (Smart Money Concepts):
1. Identify the Day High and Day Low — these are the key liquidity levels I track
2. Identify the current trend — Bullish (price making higher highs/lows) or Bearish (lower highs/lows)
3. Identify Inducement and POIs (Points of Interest) — areas where price may sweep liquidity (equal highs/lows, previous session highs/lows) before reversing
4. Entry trigger — if price breaks the Day High or Low, I wait for a Change of Character (CHOCH), then enter on a retracement into a Fair Value Gap (FVG) or Order Block

Definitions to apply:
- Inducement: a liquidity sweep designed to trap retail traders before the real move
- POI (Point of Interest): price levels with high institutional interest — previous highs/lows, supply/demand zones
- CHOCH (Change of Character): first sign of trend reversal — price breaks the most recent swing high in a downtrend (or swing low in an uptrend)
- FVG (Fair Value Gap): a 3-candle imbalance where the first candle's high and third candle's low don't overlap (bullish FVG), or first low and third high don't overlap (bearish FVG)
- Order Block: the last bullish/bearish candle before a significant move in the opposite direction — where institutional orders are likely resting

Be concise and direct. Use bullet points. Give specific price levels where possible."""


def generate_morning_brief_ict(futures_data: list, economic_events: list, market_news: list, config: dict) -> str:
    rules = _build_ict_rules(config)

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

    system = f"""You are my personal ICT (Inner Circle Trader) analyst for ES and NQ futures.
Apply only the rules I provide — do not add rules that are not listed.
Be specific with price levels. Use ICT terminology precisely.
Format output with clear sections and bullet points.

MY ACTIVE ICT RULES:
{rules}"""

    user_msg = f"""PRE-MARKET DATA:
{futures_block}

TODAY'S ECONOMIC EVENTS:
{events_block}

LATEST MARKET NEWS:
{news_block}

Apply my ICT strategy and provide the morning brief covering:
1. Market Structure — current HH/HL or LH/LL structure for ES and NQ
2. Dealing Range — identify today's range; is price in Premium or Discount?
3. Killzone — which killzone is active or upcoming? What phase of PO3?
4. Judas Swing — was there a false open move? Direction?
5. Liquidity — key resting stops to watch (equal highs/lows, swing points)
6. Setup — FVG or Order Block entry zone, OTE Fibonacci level if applicable
7. Economic event risk — events that could act as catalysts or invalidate setups
8. Session bias for ES and NQ — Bullish / Bearish / No Setup + one actionable insight"""

    return _ask(system, user_msg, max_tokens=1500)


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

    user_msg = f"""PRE-MARKET DATA:
{futures_block}

TODAY'S ECONOMIC EVENTS:
{events_block}

LATEST MARKET NEWS:
{news_block}

Apply my SMC strategy and provide the morning brief covering:
1. Overall trend — Bullish or Bearish for ES and NQ, with reasoning
2. Key levels — Day High, Day Low, and any major POIs to watch
3. Inducement zones — where liquidity may be swept before the real move
4. Potential trade setup — if a High/Low breaks, what CHOCH + FVG/Order Block entry would look like
5. Economic event risk — any scheduled events that could act as catalysts or invalidate setups
6. Session bias and one actionable insight for today"""

    return _ask(MORNING_BRIEF_SYSTEM, user_msg, max_tokens=1500)


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


# ─── My Strategy (SMC) Analysis ──────────────────────────────────────────────

MY_STRATEGY_SYSTEM = """You are my personal trading analyst. Apply my SMC-based strategy to stock analysis.

My strategy:
1. Identify the High and Low — key liquidity levels for the relevant timeframe
2. Identify the current trend — Bullish (higher highs/lows) or Bearish (lower highs/lows)
3. Identify Inducement and POIs (Points of Interest) — areas where price may sweep liquidity before reversing
4. Entry trigger — if price breaks the High or Low, wait for a Change of Character (CHOCH), then enter on a retracement into a Fair Value Gap (FVG) or Order Block

Definitions:
- Inducement: liquidity sweep designed to trap retail traders before the real move
- POI (Point of Interest): key price levels with institutional interest — previous highs/lows, supply/demand zones
- CHOCH (Change of Character): first sign of reversal — price breaks the most recent swing high in a downtrend (or swing low in uptrend)
- FVG (Fair Value Gap): 3-candle imbalance where first candle's high and third candle's low don't overlap (bullish), or vice versa (bearish)
- Order Block: last bullish/bearish candle before a significant opposing move — where institutional orders rest

Be specific with price levels. Be concise and direct."""


def analyze_stock_my_strategy(ticker: str, info: dict, history_summary: str, timeframe: str = "swing") -> str:
    price  = info.get("currentPrice") or info.get("regularMarketPrice", "N/A")
    high52 = info.get("fiftyTwoWeekHigh", "N/A")
    low52  = info.get("fiftyTwoWeekLow", "N/A")
    name   = info.get("longName", ticker)

    user_msg = f"""Apply my SMC strategy to analyze {name} ({ticker}) for a {timeframe} trade.

SNAPSHOT:
  Current Price: ${price} | 52w Range: ${low52} – ${high52}

RECENT PRICE ACTION:
  {history_summary}

Provide:
1. Trend — Bullish or Bearish with reasoning based on recent price structure
2. Key levels — High, Low, and major POIs (with approximate prices)
3. Inducement zones — where liquidity may be swept before the real move
4. Potential setup — if a key level breaks, describe the CHOCH to watch for and the FVG/Order Block entry zone
5. Invalidation — what price action would invalidate the setup
6. Bias: Bullish / Bearish / Neutral + one-line trade idea"""

    return _ask(MY_STRATEGY_SYSTEM, user_msg, max_tokens=1200)


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


# ─── My ICT Analysis ─────────────────────────────────────────────────────────

ICT_SYSTEM = """You are my personal ICT (Inner Circle Trader) analyst.
Apply only the rules I provide — do not add rules that are not listed.
Be specific with price levels. Use ICT terminology precisely.
Format output with clear sections and bullet points."""


def _build_ict_rules(config: dict) -> str:
    rules = []

    if config.get("market_structure", {}).get("enabled"):
        rules.append("• Market Structure: Identify HH/HL (bullish) or LH/LL (bearish) — note most recent shift")

    kz = config.get("killzones", {})
    if kz.get("enabled"):
        active = []
        if kz.get("london_open",   {}).get("enabled"):
            t = kz["london_open"];   active.append(f"London Open ({t['start']}–{t['end']} ET)")
        if kz.get("new_york_open", {}).get("enabled"):
            t = kz["new_york_open"]; active.append(f"NY Open ({t['start']}–{t['end']} ET)")
        if kz.get("london_close",  {}).get("enabled"):
            t = kz["london_close"];  active.append(f"London Close ({t['start']}–{t['end']} ET)")
        if active:
            rules.append(f"• Killzones: Prefer entries during — {', '.join(active)}")

    if config.get("power_of_three", {}).get("enabled"):
        rules.append("• Power of Three (PO3): Identify which phase is active — Accumulation / Manipulation / Distribution")

    if config.get("premium_discount", {}).get("enabled"):
        rules.append("• Premium/Discount: Buy only in discount (<50% of dealing range), sell only in premium (>50%)")

    if config.get("optimal_trade_entry", {}).get("enabled"):
        ote = config["optimal_trade_entry"]
        rules.append(f"• OTE: Enter on {int(ote['fib_low']*100)}%–{int(ote['fib_high']*100)}% Fibonacci retracement after displacement")

    if config.get("fair_value_gap", {}).get("enabled"):
        fvg = config["fair_value_gap"]
        rules.append(f"• FVG: Look for 3-candle imbalances ≥{fvg['min_size_points']} points. Enter on retracement into gap")

    if config.get("order_block", {}).get("enabled"):
        rules.append("• Order Block: Last opposing candle before significant displacement — enter on retest")

    if config.get("breaker_block", {}).get("enabled"):
        rules.append("• Breaker Block: Failed order block that flips — previous support becomes resistance and vice versa")

    liq = config.get("liquidity", {})
    if liq.get("enabled"):
        targets = []
        if liq.get("watch_equal_highs"):  targets.append("equal highs")
        if liq.get("watch_equal_lows"):   targets.append("equal lows")
        if liq.get("watch_swing_points"): targets.append("swing highs/lows")
        if targets:
            rules.append(f"• Liquidity: Watch for stop hunts at {', '.join(targets)} before real move")

    if config.get("judas_swing", {}).get("enabled"):
        rules.append("• Judas Swing: False move at session open to trap retail before real directional move")

    rm = config.get("risk_management", {})
    if rm.get("enabled"):
        rules.append(f"• Risk Management: Minimum R:R {rm['min_rr_ratio']}:1 | Risk {rm['risk_per_trade_pct']}% per trade")

    return "\n".join(rules) if rules else "No rules enabled."


def analyze_ict(instrument: str, info: dict, history_summary: str, timeframe: str, config: dict) -> str:
    price = info.get("currentPrice") or info.get("regularMarketPrice", "N/A")
    name  = info.get("longName", instrument)
    rules = _build_ict_rules(config)

    user_msg = f"""Apply my ICT strategy to analyze {name} ({instrument}) for a {timeframe} trade.

Current Price: ${price}
Recent Price Action: {history_summary}

MY ACTIVE ICT RULES:
{rules}

Provide analysis in these sections:
1. Market Structure — current structure, most recent swing points with prices
2. Dealing Range — identify the range high/low; is price in Premium or Discount?
3. Killzone — is current time inside an active killzone? Which phase of PO3?
4. Judas Swing — was there a false move? In which direction?
5. Liquidity — where are the resting stops (equal highs/lows, swing points)?
6. Setup — describe the ICT entry setup:
   - Which liquidity is being targeted?
   - FVG zone (prices) or Order Block zone (prices) for entry
   - OTE Fibonacci zone if applicable
7. Trade Plan — Entry zone, Stop Loss, Target 1, Target 2, R:R
8. Bias: Bullish / Bearish / No Setup — one line reason"""

    return _ask(ICT_SYSTEM, user_msg, max_tokens=1500)


def get_ict_entry_levels(instrument: str, info: dict, history_summary: str, config: dict) -> dict:
    """Returns structured ICT entry levels as JSON for chart plotting."""
    price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
    rules = _build_ict_rules(config)

    user_msg = f"""ICT analysis of {instrument} at ${price}.
Recent price action: {history_summary}
Active rules: {rules}

Return ONLY valid JSON, no other text:
{{
  "bias": "Bullish",
  "order_block": {{"high": 0.0, "low": 0.0, "type": "Bullish"}},
  "fvg": {{"high": 0.0, "low": 0.0, "type": "Bullish"}},
  "choch_level": 0.0,
  "entry": 0.0,
  "stop_loss": 0.0,
  "target": 0.0
}}
All prices must be realistic relative to current price ${price}."""

    import json, re
    raw = _ask(ICT_SYSTEM, user_msg, max_tokens=400)
    try:
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            return json.loads(match.group())
    except (json.JSONDecodeError, AttributeError):
        pass
    return {}


# ─── SMC Structured Entry Levels ─────────────────────────────────────────────

def get_smc_entry_levels(ticker: str, info: dict, history_summary: str, timeframe: str) -> dict:
    """
    Returns SMC entry levels as a structured dict for chart plotting.
    Asks Claude to return JSON only — parsed and returned as a Python dict.
    """
    price = info.get("currentPrice") or info.get("regularMarketPrice", 0)

    user_msg = f"""Based on SMC analysis of {ticker} at current price ${price}.

Recent price action: {history_summary}

Return ONLY valid JSON, no other text, in this exact format:
{{
  "bias": "Bullish",
  "order_block": {{"high": 0.0, "low": 0.0, "type": "Bullish"}},
  "fvg": {{"high": 0.0, "low": 0.0, "type": "Bullish"}},
  "choch_level": 0.0,
  "entry": 0.0,
  "stop_loss": 0.0,
  "target": 0.0
}}

Rules:
- bias must be "Bullish" or "Bearish"
- order_block and fvg type must match bias
- All prices must be realistic relative to current price ${price}
- entry should be inside or near the order_block or fvg zone
- stop_loss below order_block low (bullish) or above order_block high (bearish)
- target is the next significant liquidity level"""

    raw = _ask(MY_STRATEGY_SYSTEM, user_msg, max_tokens=400)

    import json, re
    try:
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            return json.loads(match.group())
    except (json.JSONDecodeError, AttributeError):
        pass
    return {}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _impact(event: dict) -> str:
    return {"1": "Low", "2": "Med", "3": "High"}.get(str(event.get("impact", "")), "—")
