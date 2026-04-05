"""Application configuration loaded from environment."""

import os

from dotenv import load_dotenv

load_dotenv()

TESTNET_BASE_URL = "https://testnet.binancefuture.com"
LOG_FILE = "logs/trading_bot.log"
LOG_LEVEL_FILE = "DEBUG"
LOG_LEVEL_CONSOLE = "INFO"

API_KEY = (os.getenv("BINANCE_API_KEY") or "").strip()
API_SECRET = (os.getenv("BINANCE_API_SECRET") or "").strip()


def require_credentials() -> None:
    """Ensure API credentials are present. Call before live trading (not dry-run).

    Raises:
        EnvironmentError: If either key is missing or empty.
    """
    missing = []
    if not API_KEY:
        missing.append("BINANCE_API_KEY")
    if not API_SECRET:
        missing.append("BINANCE_API_SECRET")
    if missing:
        raise EnvironmentError(
            "Missing or empty Binance API credentials: "
            + ", ".join(missing)
            + ". Copy .env.example to .env and set your Binance Futures Testnet "
            "API key and secret. Never commit .env to version control."
        )
