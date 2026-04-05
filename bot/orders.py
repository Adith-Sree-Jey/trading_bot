"""High-level futures order placement with validation and response parsing."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

_MARKET_FILL_MAX_WAIT_S = 8.0
_MARKET_FILL_POLL_INTERVAL_S = 0.2
_MARKET_FAILED_STATUSES = frozenset({"CANCELED", "REJECTED", "EXPIRED"})

from bot.client import BinanceClient, TradingBotError
from bot.validators import (
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_stop_price,
    validate_symbol,
)

logger = logging.getLogger(__name__)


@dataclass
class OrderResult:
    order_id: int
    symbol: str
    side: str
    order_type: str
    status: str
    quantity: float
    executed_qty: float
    avg_price: float
    price: float
    client_order_id: str
    raw_response: dict


def _to_float(val: Any, default: float = 0.0) -> float:
    if val is None or val == "":
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _to_int(val: Any, default: int = 0) -> int:
    if val is None or val == "":
        return default
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def _parse_response(response: dict) -> OrderResult:
    """Build OrderResult from Binance futures or algo order JSON."""
    rid = response.get("orderId")
    if rid is None:
        rid = response.get("algoId")
    order_id = _to_int(rid, 0)
    symbol = str(response.get("symbol") or "")
    side = str(response.get("side") or "")
    order_type = str(response.get("type") or response.get("orderType") or "")
    status = str(response.get("status") or "")
    quantity = _to_float(response.get("origQty") or response.get("quantity"))
    executed_qty = _to_float(response.get("executedQty"))
    avg_price = _to_float(response.get("avgPrice"))
    price = _to_float(response.get("price"))
    cid = response.get("clientOrderId") or response.get("clientAlgoId") or ""
    client_order_id = str(cid) if cid is not None else ""

    return OrderResult(
        order_id=order_id,
        symbol=symbol,
        side=side,
        order_type=order_type,
        status=status,
        quantity=quantity,
        executed_qty=executed_qty,
        avg_price=avg_price,
        price=price,
        client_order_id=client_order_id,
        raw_response=response,
    )


def _wait_for_market_filled(
    client: BinanceClient, symbol: str, order_id: int, initial: dict
) -> dict:
    """Poll until MARKET order is FILLED so CLI shows correct final status."""
    status = str(initial.get("status") or "").upper()
    if status == "FILLED":
        return initial
    if status in _MARKET_FAILED_STATUSES:
        raise TradingBotError(
            f"Market order ended in non-fill status: {initial.get('status')}"
        )
    if order_id <= 0:
        raise TradingBotError(
            "Market order response missing orderId; cannot confirm FILLED status."
        )

    deadline = time.monotonic() + _MARKET_FILL_MAX_WAIT_S
    last = initial
    while time.monotonic() < deadline:
        time.sleep(_MARKET_FILL_POLL_INTERVAL_S)
        last = client.get_futures_order(symbol=symbol, orderId=order_id)
        st = str(last.get("status") or "").upper()
        if st == "FILLED":
            logger.info(
                "Market order confirmed FILLED via poll: orderId=%s symbol=%s",
                order_id,
                symbol,
            )
            return last
        if st in _MARKET_FAILED_STATUSES:
            raise TradingBotError(
                f"Market order ended in status {last.get('status')!r} (expected FILLED)."
            )

    raise TradingBotError(
        "Market order did not reach FILLED status within "
        f"{_MARKET_FILL_MAX_WAIT_S:.0f}s (last status={last.get('status')!r})."
    )


def place_market_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    quantity: float,
) -> OrderResult:
    sym = validate_symbol(symbol)
    sd = validate_side(side)
    qty = validate_quantity(quantity)
    validate_order_type("MARKET")
    validate_price(None, "MARKET")
    validate_stop_price(None, "MARKET")

    params = {
        "symbol": sym,
        "side": sd,
        "type": "MARKET",
        "quantity": qty,
    }
    raw = client.place_futures_order(**params)
    raw = _wait_for_market_filled(client, sym, _to_int(raw.get("orderId"), 0), raw)
    result = _parse_response(raw)
    if result.status.upper() != "FILLED":
        raise TradingBotError(
            f"Market order must be FILLED for display; got status={result.status!r}."
        )
    logger.info(
        "Market order completed: id=%s status=%s symbol=%s",
        result.order_id,
        result.status,
        result.symbol,
    )
    return result


def place_limit_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    quantity: float,
    price: float,
) -> OrderResult:
    sym = validate_symbol(symbol)
    sd = validate_side(side)
    qty = validate_quantity(quantity)
    validate_order_type("LIMIT")
    px = validate_price(price, "LIMIT")
    validate_stop_price(None, "LIMIT")
    assert px is not None

    params = {
        "symbol": sym,
        "side": sd,
        "type": "LIMIT",
        "timeInForce": "GTC",
        "quantity": qty,
        "price": px,
    }
    raw = client.place_futures_order(**params)
    result = _parse_response(raw)
    logger.info(
        "Limit order completed: id=%s status=%s symbol=%s",
        result.order_id,
        result.status,
        result.symbol,
    )
    return result


def place_stop_limit_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    quantity: float,
    price: float,
    stop_price: float,
) -> OrderResult:
    sym = validate_symbol(symbol)
    sd = validate_side(side)
    qty = validate_quantity(quantity)
    validate_order_type("STOP_LIMIT")
    px = validate_price(price, "STOP_LIMIT")
    sp = validate_stop_price(stop_price, "STOP_LIMIT")
    assert px is not None and sp is not None

    params = {
        "symbol": sym,
        "side": sd,
        "type": "STOP",
        "timeInForce": "GTC",
        "quantity": qty,
        "price": px,
        "stopPrice": sp,
    }
    raw = client.place_futures_order(**params)
    result = _parse_response(raw)
    logger.info(
        "Stop-limit order completed: id=%s status=%s symbol=%s",
        result.order_id,
        result.status,
        result.symbol,
    )
    return result


# Re-export for tests that patch exception type
__all__ = [
    "OrderResult",
    "place_limit_order",
    "place_market_order",
    "place_stop_limit_order",
    "TradingBotError",
    "_parse_response",
]
