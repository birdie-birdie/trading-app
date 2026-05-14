"""
ProjectX / TopstepX real-time futures data provider.
Requires: pip install project-x-py
API docs:  https://gateway.docs.projectx.com/
"""
import asyncio
from typing import Optional

# Symbol mapping: our internal symbol -> ProjectX contract name
SYMBOL_MAP = {
    "MES=F": "MES",
    "MNQ=F": "MNQ",
    "ES=F":  "ES",
    "NQ=F":  "NQ",
    "YM=F":  "YM",
    "RTY=F": "RTY",
}

_client = None


def _get_client(username: str, api_key: str):
    global _client
    if _client is not None:
        return _client
    try:
        from projectx.client import ProjectXClient  # project-x-py
        _client = ProjectXClient(username=username, api_key=api_key)
        return _client
    except ImportError:
        raise ImportError(
            "project-x-py is not installed. Run: pip install project-x-py"
        )


def get_quote(ticker: str, username: str, api_key: str) -> dict:
    """Fetch a single real-time quote from ProjectX."""
    contract = SYMBOL_MAP.get(ticker, ticker.replace("=F", ""))
    try:
        client = _get_client(username, api_key)
        # project-x-py exposes async methods; run them synchronously here
        quote = asyncio.run(_fetch_quote(client, contract))
        return {
            "symbol":     ticker,
            "price":      quote.get("last", 0.0),
            "change":     quote.get("change", 0.0),
            "change_pct": quote.get("changePct", 0.0),
            "volume":     quote.get("volume", 0),
            "high":       quote.get("high", 0.0),
            "low":        quote.get("low", 0.0),
            "open":       quote.get("open", 0.0),
            "bid":        quote.get("bid", 0.0),
            "ask":        quote.get("ask", 0.0),
        }
    except Exception as e:
        return {"symbol": ticker, "error": str(e)}


async def _fetch_quote(client, contract: str) -> dict:
    """Internal async quote fetch."""
    # Adjust method names to match actual project-x-py SDK
    data = await client.get_quote(contract)
    return data if isinstance(data, dict) else {}


def get_multiple_quotes(tickers: list, username: str, api_key: str) -> list:
    return [get_quote(t, username, api_key) for t in tickers]
