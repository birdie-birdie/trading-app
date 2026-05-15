import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Claude AI
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # Finnhub (economic calendar & news)
    FINNHUB_API_KEY: str = os.getenv("FINNHUB_API_KEY", "")

    # ProjectX / TopstepX (futures)
    PROJECTX_USERNAME: str = os.getenv("PROJECTX_USERNAME", "")
    PROJECTX_API_KEY: str = os.getenv("PROJECTX_API_KEY", "")

    # Questrade (stocks, future integration)
    QUESTRADE_ACCESS_TOKEN: str = os.getenv("QUESTRADE_ACCESS_TOKEN", "")

    # Provider selection
    FUTURES_PROVIDER: str = os.getenv("FUTURES_PROVIDER", "yahoo")   # "yahoo" | "projectx"
    STOCKS_PROVIDER: str = os.getenv("STOCKS_PROVIDER", "yahoo")     # "yahoo" | "finnhub" | "questrade"

    # Default futures contracts to track
    FUTURES_WATCHLIST: list = ["ES=F", "NQ=F"]

    # Claude model
    CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

    # App
    APP_TITLE: str = "Trading Intelligence Dashboard"
    REFRESH_INTERVAL: int = int(os.getenv("REFRESH_INTERVAL", "60"))

    @classmethod
    def validate(cls) -> dict:
        """Return which services are configured."""
        return {
            "claude":    bool(cls.ANTHROPIC_API_KEY),
            "finnhub":   bool(cls.FINNHUB_API_KEY),
            "projectx":  bool(cls.PROJECTX_USERNAME and cls.PROJECTX_API_KEY),
            "questrade": bool(cls.QUESTRADE_ACCESS_TOKEN),
        }
