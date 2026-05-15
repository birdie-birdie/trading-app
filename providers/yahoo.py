import yfinance as yf
import pandas as pd
from datetime import datetime


def get_quote(ticker: str) -> dict:
    t = yf.Ticker(ticker)
    try:
        fi = t.fast_info
        price = fi.last_price or 0.0
        prev = fi.previous_close or price
        change = price - prev
        change_pct = (change / prev * 100) if prev else 0.0
        return {
            "symbol":     ticker,
            "price":      round(price, 2),
            "change":     round(change, 2),
            "change_pct": round(change_pct, 2),
            "volume":     fi.last_volume,
            "high":       fi.day_high,
            "low":        fi.day_low,
            "open":       fi.open,
            "prev_close": round(prev, 2),
        }
    except Exception as e:
        return {"symbol": ticker, "error": str(e)}


def get_multiple_quotes(tickers: list) -> list:
    return [get_quote(t) for t in tickers]


def get_history(ticker: str, period: str = "3mo", interval: str = "1d", prepost: bool = False) -> pd.DataFrame:
    return yf.Ticker(ticker).history(period=period, interval=interval, prepost=prepost)


def get_info(ticker: str) -> dict:
    try:
        return yf.Ticker(ticker).info
    except Exception:
        return {}


def get_earnings(ticker: str) -> dict:
    t = yf.Ticker(ticker)
    result = {}
    try:
        result["calendar"] = t.calendar
    except Exception:
        result["calendar"] = {}
    try:
        qe = t.quarterly_earnings
        result["quarterly_earnings"] = qe.to_dict() if qe is not None else {}
    except Exception:
        result["quarterly_earnings"] = {}
    try:
        qf = t.quarterly_financials
        result["quarterly_financials"] = qf.to_dict() if qf is not None else {}
    except Exception:
        result["quarterly_financials"] = {}
    return result


def build_history_summary(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return "No history available."
    latest = df.iloc[-1]
    oldest = df.iloc[0]
    period_chg = ((latest["Close"] - oldest["Close"]) / oldest["Close"] * 100)
    high = df["High"].max()
    low = df["Low"].low() if hasattr(df["Low"], "low") else df["Low"].min()
    return (
        f"Period: {oldest.name.date()} to {latest.name.date()} | "
        f"Change: {period_chg:+.2f}% | "
        f"High: {high:.2f} | Low: {low:.2f} | "
        f"Last close: {latest['Close']:.2f}"
    )
