"""Binance Futures (USDT-M) testnet client wrapper."""

from __future__ import annotations

import logging
from typing import Any

import requests
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException

logger = logging.getLogger(__name__)


class TradingBotError(Exception):
    """Raised when a trading operation fails after handling Binance or network errors."""


class BinanceClient:
    """Thin wrapper around python-binance Client for USDT-M futures on testnet."""

    def __init__(self, api_key: str, api_secret: str, testnet_url: str) -> None:
        self.client = Client(api_key, api_secret, testnet=True)
        normalized = f"{testnet_url.rstrip('/')}/fapi"
        self.client.FUTURES_TESTNET_URL = normalized
        logger.info(
            "BinanceClient initialized for futures testnet (base=%s)",
            normalized,
        )

    def place_futures_order(self, **params: Any) -> dict:
        logger.debug("place_futures_order params: %r", params)
        try:
            response = self.client.futures_create_order(**params)
        except BinanceAPIException as e:
            logger.error(
                "Binance API error: code=%s msg=%s",
                getattr(e, "code", None),
                getattr(e, "message", str(e)),
            )
            raise TradingBotError(str(e)) from e
        except BinanceRequestException as e:
            logger.error("Binance request error: %s", e)
            raise TradingBotError(str(e)) from e
        except requests.exceptions.ConnectionError as e:
            logger.error("Connection error: %s", e)
            raise TradingBotError(str(e)) from e

        logger.debug("place_futures_order response: %r", response)
        logger.info("Futures order placed successfully")
        return response

    def get_futures_order(self, **params: Any) -> dict:
        """Query a single futures order (used to confirm MARKET fills)."""
        logger.debug("get_futures_order params: %r", params)
        try:
            response = self.client.futures_get_order(**params)
        except BinanceAPIException as e:
            logger.error(
                "Binance API error (get order): code=%s msg=%s",
                getattr(e, "code", None),
                getattr(e, "message", str(e)),
            )
            raise TradingBotError(str(e)) from e
        except BinanceRequestException as e:
            logger.error("Binance request error (get order): %s", e)
            raise TradingBotError(str(e)) from e
        except requests.exceptions.ConnectionError as e:
            logger.error("Connection error (get order): %s", e)
            raise TradingBotError(str(e)) from e

        logger.debug("get_futures_order response: %r", response)
        return response
