"""
Stock data provider router.
Dispatches to the configured provider so views stay provider-agnostic.

STOCKS_PROVIDER options:
  "yahoo"   — Yahoo Finance (free, slightly delayed)
  "finnhub" — Finnhub (free, real-time quotes; yfinance still used for charts)
  "questrade" — Questrade (planned)
"""
from config import Config
from providers import yahoo, finnhub_client


def get_quote(symbol: str) -> dict:
    if Config.STOCKS_PROVIDER == "finnhub" and Config.FINNHUB_API_KEY:
        return finnhub_client.get_stock_quote(symbol, Config.FINNHUB_API_KEY)
    return yahoo.get_quote(symbol)


def get_multiple_quotes(symbols: list) -> list:
    if Config.STOCKS_PROVIDER == "finnhub" and Config.FINNHUB_API_KEY:
        return finnhub_client.get_multiple_stock_quotes(symbols, Config.FINNHUB_API_KEY)
    return yahoo.get_multiple_quotes(symbols)


def get_info(symbol: str) -> dict:
    if Config.STOCKS_PROVIDER == "finnhub" and Config.FINNHUB_API_KEY:
        return finnhub_client.get_stock_info(symbol, Config.FINNHUB_API_KEY)
    return yahoo.get_info(symbol)


def get_earnings(symbol: str) -> dict:
    if Config.STOCKS_PROVIDER == "finnhub" and Config.FINNHUB_API_KEY:
        return finnhub_client.get_stock_earnings(symbol, Config.FINNHUB_API_KEY)
    return yahoo.get_earnings(symbol)


def get_history(symbol: str, period: str = "3mo", interval: str = "1d", prepost: bool = False):
    """Historical OHLCV for charting — always uses yfinance (best free source)."""
    return yahoo.get_history(symbol, period=period, interval=interval, prepost=prepost)


def active_provider() -> str:
    if Config.STOCKS_PROVIDER == "finnhub" and Config.FINNHUB_API_KEY:
        return "Finnhub (real-time)"
    if Config.STOCKS_PROVIDER == "questrade" and Config.QUESTRADE_ACCESS_TOKEN:
        return "Questrade (real-time)"
    return "Yahoo Finance"
