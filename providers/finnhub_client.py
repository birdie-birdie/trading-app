"""
Finnhub provider — real-time stock quotes, company info, economic calendar, news.
Free API key: https://finnhub.io/register  (60 req/min free tier)
"""
from datetime import date, timedelta, datetime
import finnhub


def _client(api_key: str) -> finnhub.Client:
    return finnhub.Client(api_key=api_key)


# ── Real-time stock quotes ─────────────────────────────────────────────────────

def get_stock_quote(symbol: str, api_key: str) -> dict:
    """Real-time stock quote. Returns normalized dict matching yahoo.get_quote() format."""
    if not api_key:
        return {"symbol": symbol, "error": "Finnhub API key not configured"}
    try:
        c = _client(api_key)
        q = c.quote(symbol)
        # q keys: c=current, h=high, l=low, o=open, pc=prev_close, d=change, dp=chg_pct
        if not q or q.get("c", 0) == 0:
            return {"symbol": symbol, "error": "No data returned"}
        return {
            "symbol":     symbol,
            "price":      round(q["c"], 2),
            "change":     round(q.get("d", 0), 2),
            "change_pct": round(q.get("dp", 0), 2),
            "high":       q.get("h"),
            "low":        q.get("l"),
            "open":       q.get("o"),
            "prev_close": q.get("pc"),
            "volume":     None,  # Finnhub /quote does not return volume
        }
    except Exception as e:
        return {"symbol": symbol, "error": str(e)}


def get_multiple_stock_quotes(symbols: list, api_key: str) -> list:
    return [get_stock_quote(s, api_key) for s in symbols]


def get_stock_info(symbol: str, api_key: str) -> dict:
    """
    Company profile + basic financials merged into a normalized dict
    that matches the field names used from yahoo.get_info().
    """
    if not api_key:
        return {}
    try:
        c = _client(api_key)
        profile = c.company_profile2(symbol=symbol)
        basics  = c.company_basic_financials(symbol, "all").get("metric", {})
        q       = c.quote(symbol)

        # Finnhub marketCapitalization is in USD millions — convert to units
        mktcap_m = profile.get("marketCapitalization", 0) or 0
        mktcap   = mktcap_m * 1_000_000 if mktcap_m else None

        return {
            # Identity
            "symbol":            symbol,
            "longName":          profile.get("name", symbol),
            "shortName":         profile.get("name", symbol),
            "sector":            profile.get("finnhubIndustry", "—"),
            "industry":          profile.get("finnhubIndustry", "—"),
            # Pricing
            "currentPrice":      q.get("c"),
            "regularMarketPrice": q.get("c"),
            "fiftyTwoWeekHigh":  basics.get("52WeekHigh"),
            "fiftyTwoWeekLow":   basics.get("52WeekLow"),
            # Valuation
            "marketCap":         mktcap,
            "trailingPE":        basics.get("peNormalizedAnnual"),
            "trailingEps":       basics.get("epsNormalizedAnnual"),
            "revenueGrowth":     basics.get("revenueGrowthTTMYoy"),
            "dividendYield":     basics.get("dividendYieldIndicatedAnnual"),
            # Extra Finnhub metrics passed through for AI context
            "roeTTM":            basics.get("roeTTM"),
            "netMarginTTM":      basics.get("netMarginTTM"),
            "debtEquityAnnual":  basics.get("totalDebt/totalEquityAnnual"),
        }
    except Exception:
        return {}


def get_stock_earnings(symbol: str, api_key: str) -> dict:
    """Recent earnings surprises and upcoming calendar from Finnhub."""
    if not api_key:
        return {}
    try:
        c = _client(api_key)
        surprises = c.company_earnings(symbol, limit=4)
        cal = c.earnings_calendar(
            _from=date.today().isoformat(),
            to=date(date.today().year, 12, 31).isoformat(),
            symbol=symbol,
            international=False,
        )
        return {
            "surprises": surprises,
            "calendar":  cal.get("earningsCalendar", []),
        }
    except Exception:
        return {}


def get_economic_calendar(api_key: str, days_ahead: int = 1) -> list:
    """Return economic events for today and the next `days_ahead` days."""
    if not api_key:
        return []
    try:
        raw = _client(api_key).economic_calendar()
        events = raw.get("economicCalendar", [])
        today = date.today()
        cutoff = today + timedelta(days=days_ahead)
        filtered = []
        for e in events:
            t = e.get("time", "")
            try:
                ev_date = date.fromisoformat(t[:10])
                if today <= ev_date <= cutoff:
                    filtered.append(e)
            except (ValueError, TypeError):
                pass
        return sorted(filtered, key=lambda x: x.get("time", ""))
    except Exception:
        return []


def get_market_news(api_key: str, category: str = "general", count: int = 8) -> list:
    """Return recent market news headlines."""
    if not api_key:
        return []
    try:
        news = _client(api_key).general_news(category, min_id=0)
        return news[:count]
    except Exception:
        return []


def format_event(event: dict) -> str:
    impact_map = {"1": "Low", "2": "Medium", "3": "High"}
    impact = impact_map.get(str(event.get("impact", "")), "—")
    return (
        f"{event.get('time', '')[:16]}  "
        f"[{impact}]  "
        f"{event.get('event', 'Unknown event')}  "
        f"(Actual: {event.get('actual', '—')} | Est: {event.get('estimate', '—')} | Prev: {event.get('prev', '—')})"
    )
