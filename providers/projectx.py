"""
ProjectX / TopstepX real-time futures data provider.
Requires: pip install project-x-py --no-deps
API docs:  https://gateway.docs.projectx.com/
"""
import asyncio
import threading

# Yahoo Finance ticker → ProjectX contract name
SYMBOL_MAP = {
    "MES=F": "MES",
    "MNQ=F": "MNQ",
    "ES=F":  "ES",
    "NQ=F":  "NQ",
    "YM=F":  "YM",
    "RTY=F": "RTY",
}


def _run_async(coro):
    """Run an async coroutine in a fresh thread/event-loop (avoids Streamlit's running loop)."""
    result = [None]
    error  = [None]

    def _target():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result[0] = loop.run_until_complete(coro)
        except Exception as exc:
            error[0] = exc
        finally:
            loop.close()

    t = threading.Thread(target=_target, daemon=True)
    t.start()
    t.join(timeout=20)
    if error[0] is not None:
        raise error[0]
    return result[0]


async def _fetch_quotes_async(contracts: list[str], username: str, api_key: str) -> list[dict]:
    """Fetch today's OHLCV for each contract using 1-minute bars."""
    from project_x_py.client import ProjectX

    async with ProjectX(username=username, api_key=api_key) as client:
        await client.authenticate()
        results = []
        for contract in contracts:
            try:
                bars = await client.get_bars(contract, days=1, interval=1)
                if bars is None or len(bars) == 0:
                    results.append({"contract": contract, "error": "no data"})
                    continue
                last   = bars.row(-1, named=True)
                first  = bars.row(0,  named=True)
                close  = float(last["close"])
                open_  = float(first["open"])
                high   = float(bars["high"].max())
                low    = float(bars["low"].min())
                volume = int(bars["volume"].sum())
                results.append({
                    "contract": contract,
                    "close":    close,
                    "open":     open_,
                    "high":     high,
                    "low":      low,
                    "volume":   volume,
                })
            except Exception as exc:
                results.append({"contract": contract, "error": str(exc)})
        return results


def get_multiple_quotes(tickers: list, username: str, api_key: str) -> list:
    """Fetch real-time quotes for a list of tickers. Returns list of quote dicts."""
    contracts = [SYMBOL_MAP.get(t, t.replace("=F", "")) for t in tickers]
    ticker_map = dict(zip(contracts, tickers))

    try:
        raw = _run_async(_fetch_quotes_async(contracts, username, api_key))
    except Exception as exc:
        return [{"symbol": t, "error": str(exc)} for t in tickers]

    quotes = []
    for item in raw:
        contract = item["contract"]
        ticker   = ticker_map.get(contract, contract)
        if "error" in item:
            quotes.append({"symbol": ticker, "error": item["error"]})
            continue
        close  = item["close"]
        open_  = item["open"]
        change = round(close - open_, 2)
        change_pct = round((change / open_) * 100, 4) if open_ else 0.0
        quotes.append({
            "symbol":     ticker,
            "price":      close,
            "change":     change,
            "change_pct": change_pct,
            "high":       item["high"],
            "low":        item["low"],
            "open":       open_,
            "volume":     item["volume"],
        })
    return quotes


def get_quote(ticker: str, username: str, api_key: str) -> dict:
    """Fetch a single real-time quote from ProjectX."""
    results = get_multiple_quotes([ticker], username, api_key)
    return results[0] if results else {"symbol": ticker, "error": "no result"}
