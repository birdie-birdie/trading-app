"""
ProjectX / TopstepX real-time futures data provider.
Requires: pip install project-x-py --no-deps
API docs:  https://gateway.docs.projectx.com/
"""
import asyncio
import datetime
import threading

import httpx
import pandas as pd

# Yahoo Finance ticker → ProjectX contract name
SYMBOL_MAP = {
    "MES=F": "MES",
    "MNQ=F": "MNQ",
    "ES=F":  "ES",
    "NQ=F":  "NQ",
    "YM=F":  "YM",
    "RTY=F": "RTY",
    "GC=F":  "GC",
    "SI=F":  "SI",
    "CL=F":  "CL",
}

_BASE_URL = "https://api.topstepx.com/api"

# Cached session token (valid 24h — we refresh after 23h to be safe)
_token: str | None = None
_token_expires: datetime.datetime | None = None

# Cached contract IDs so we don't re-search on every chart render
_contract_ids: dict[str, str] = {}

# Yahoo interval string → (TopstepX unit, unitNumber)
# unit: 2=minute  4=day  5=week
_INTERVAL_MAP: dict[str, tuple[int, int]] = {
    "1m":  (2, 1),
    "2m":  (2, 2),
    "5m":  (2, 5),
    "15m": (2, 15),
    "30m": (2, 30),
    "60m": (2, 60),
    "1h":  (2, 60),
    "1d":  (4, 1),
    "1wk": (5, 1),
}

# Yahoo period string → calendar days to look back
# Slightly padded to account for weekends / holidays
_PERIOD_DAYS: dict[str, int] = {
    "1d":  2,
    "5d":  8,
    "1mo": 35,
    "3mo": 100,
    "6mo": 190,
    "1y":  370,
    "2y":  740,
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
    """Fetch today's OHLCV for each contract via direct HTTP (no SDK dependency)."""
    now   = datetime.datetime.now(datetime.timezone.utc)
    # 26h covers the current futures session (23h/day) with buffer.
    # 26h × 60 min = 1560 bars — safely under the 2000-bar limit so we
    # never truncate and miss the most recent bars.
    start = now - datetime.timedelta(hours=26)

    async with httpx.AsyncClient(base_url=_BASE_URL, timeout=15) as http:
        # Authenticate
        resp = await http.post("/Auth/loginKey", json={"userName": username, "apiKey": api_key})
        body = resp.json()
        if not body.get("success"):
            raise Exception(f"TopstepX auth failed (errorCode={body.get('errorCode')})")
        token   = body["token"]
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        results = []
        for contract in contracts:
            try:
                # Resolve contract ID
                cr = await http.post(
                    "/Contract/search",
                    json={"searchText": contract, "live": False},
                    headers=headers,
                )
                found = cr.json().get("contracts", [])
                if not found:
                    results.append({"contract": contract, "error": "contract not found"})
                    continue
                contract_id = found[0]["id"]

                # Fetch 1-min bars for today
                br = await http.post("/History/retrieveBars", json={
                    "contractId":        contract_id,
                    "live":              False,
                    "startTime":         start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "endTime":           now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "unit":              2,
                    "unitNumber":        1,
                    "limit":             2000,
                    "includePartialBar": True,
                }, headers=headers)

                bars = br.json().get("bars", [])
                if not bars:
                    results.append({"contract": contract, "error": "no data"})
                    continue

                # Sort ascending by timestamp — API order is not guaranteed
                bars.sort(key=lambda b: b["t"])
                close  = float(bars[-1]["c"])
                open_  = float(bars[0]["o"])
                high   = max(float(b["h"]) for b in bars)
                low    = min(float(b["l"]) for b in bars)
                volume = sum(int(b["v"]) for b in bars)
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


# ─── History (for charts) ──────────────────────────────────────────────────────

async def _fetch_history_async(symbol: str, period: str, interval: str) -> pd.DataFrame:
    global _token, _token_expires, _contract_ids

    from config import Config

    unit, unit_number = _INTERVAL_MAP.get(interval, (4, 1))
    days_back = _PERIOD_DAYS.get(period, 90)
    contract_name = SYMBOL_MAP.get(symbol, symbol.replace("=F", ""))
    now = datetime.datetime.now(datetime.timezone.utc)

    async with httpx.AsyncClient(base_url=_BASE_URL, timeout=15) as http:
        # Authenticate — reuse cached token if still valid
        if not _token or not _token_expires or now >= _token_expires:
            resp = await http.post("/Auth/loginKey", json={
                "userName": Config.PROJECTX_USERNAME,
                "apiKey":   Config.PROJECTX_API_KEY,
            })
            body = resp.json()
            if not body.get("success"):
                raise Exception(f"TopstepX auth failed (errorCode={body.get('errorCode')})")
            _token = body["token"]
            _token_expires = now + datetime.timedelta(hours=23)

        headers = {"Authorization": f"Bearer {_token}", "Content-Type": "application/json"}

        # Resolve contract ID (cached per symbol)
        if contract_name not in _contract_ids:
            cr = await http.post(
                "/Contract/search",
                json={"searchText": contract_name, "live": False},
                headers=headers,
            )
            contracts = cr.json().get("contracts", [])
            if not contracts:
                raise Exception(f"No TopstepX contract found for {contract_name}")
            _contract_ids[contract_name] = contracts[0]["id"]

        contract_id = _contract_ids[contract_name]

        # Fetch bars
        start = now - datetime.timedelta(days=days_back)
        br = await http.post("/History/retrieveBars", json={
            "contractId":       contract_id,
            "live":             False,
            "startTime":        start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "endTime":          now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "unit":             unit,
            "unitNumber":       unit_number,
            "limit":            2000,
            "includePartialBar": False,
        }, headers=headers)

        bars = br.json().get("bars", [])
        if not bars:
            return pd.DataFrame()

        df = pd.DataFrame(bars)
        df = df.rename(columns={"t": "Datetime", "o": "Open", "h": "High",
                                "l": "Low",  "c": "Close", "v": "Volume"})
        df["Datetime"] = pd.to_datetime(df["Datetime"], utc=True)
        df = df.set_index("Datetime").sort_index()
        return df


def get_history(symbol: str, period: str = "3mo", interval: str = "1d") -> pd.DataFrame:
    """Fetch OHLCV bar history from TopstepX for charting. Falls back to Yahoo on error."""
    try:
        return _run_async(_fetch_history_async(symbol, period, interval))
    except Exception:
        from providers import yahoo
        return yahoo.get_history(symbol, period=period, interval=interval)
