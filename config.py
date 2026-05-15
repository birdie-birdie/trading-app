import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Claude AI
    ANTHROPIC_API_KEY:       str  = os.getenv("ANTHROPIC_API_KEY", "")

    # Finnhub (economic calendar & news)
    FINNHUB_API_KEY:         str  = os.getenv("FINNHUB_API_KEY", "")

    # ProjectX / TopstepX (futures)
    PROJECTX_USERNAME:       str  = os.getenv("PROJECTX_USERNAME", "")
    PROJECTX_API_KEY:        str  = os.getenv("PROJECTX_API_KEY", "")

    # Questrade (stocks, future integration)
    QUESTRADE_ACCESS_TOKEN:  str  = os.getenv("QUESTRADE_ACCESS_TOKEN", "")

    # Provider selection
    FUTURES_PROVIDER:        str  = os.getenv("FUTURES_PROVIDER", "projectx")
    STOCKS_PROVIDER:         str  = os.getenv("STOCKS_PROVIDER",  "finnhub")

    # Default futures contracts to track
    FUTURES_WATCHLIST:       list = ["ES=F", "NQ=F"]

    # Claude model
    CLAUDE_MODEL:            str  = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

    # Auth
    APP_USERNAME:            str  = os.getenv("APP_USERNAME", "")
    APP_PASSWORD:            str  = os.getenv("APP_PASSWORD", "")

    # App
    APP_TITLE:               str  = "Trading Intelligence Dashboard"
    REFRESH_INTERVAL:        int  = int(os.getenv("REFRESH_INTERVAL", "60"))

    @classmethod
    def reload(cls):
        """Re-read all values from os.environ. Call after updating os.environ so
        changes from the Settings page take effect without restarting the server."""
        cls.ANTHROPIC_API_KEY      = os.getenv("ANTHROPIC_API_KEY", "")
        cls.FINNHUB_API_KEY        = os.getenv("FINNHUB_API_KEY", "")
        cls.PROJECTX_USERNAME      = os.getenv("PROJECTX_USERNAME", "")
        cls.PROJECTX_API_KEY       = os.getenv("PROJECTX_API_KEY", "")
        cls.QUESTRADE_ACCESS_TOKEN = os.getenv("QUESTRADE_ACCESS_TOKEN", "")
        cls.FUTURES_PROVIDER       = os.getenv("FUTURES_PROVIDER", "projectx")
        cls.STOCKS_PROVIDER        = os.getenv("STOCKS_PROVIDER",  "finnhub")
        cls.CLAUDE_MODEL           = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
        cls.APP_USERNAME           = os.getenv("APP_USERNAME", "")
        cls.APP_PASSWORD           = os.getenv("APP_PASSWORD", "")
        cls.REFRESH_INTERVAL       = int(os.getenv("REFRESH_INTERVAL", "60"))

    @classmethod
    def validate(cls) -> dict:
        """Return which services are configured."""
        return {
            "claude":    bool(cls.ANTHROPIC_API_KEY),
            "finnhub":   bool(cls.FINNHUB_API_KEY),
            "projectx":  bool(cls.PROJECTX_USERNAME and cls.PROJECTX_API_KEY),
            "questrade": bool(cls.QUESTRADE_ACCESS_TOKEN),
        }
