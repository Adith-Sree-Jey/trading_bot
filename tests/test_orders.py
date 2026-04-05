"""Unit tests for bot.orders with mocked Binance client."""

from unittest.mock import MagicMock

import pytest

from bot.client import BinanceClient, TradingBotError
from bot.orders import (
    OrderResult,
    place_limit_order,
    place_market_order,
    place_stop_limit_order,
)


def _make_client() -> BinanceClient:
    c = MagicMock(spec=BinanceClient)
    c.place_futures_order = MagicMock()
    c.get_futures_order = MagicMock()
    return c  # type: ignore[return-value]


def test_place_market_order_returns_order_result() -> None:
    client = _make_client()
    client.place_futures_order.return_value = {
        "orderId": 123456789,
        "symbol": "BTCUSDT",
        "side": "BUY",
        "type": "MARKET",
        "status": "FILLED",
        "origQty": "0.001",
        "executedQty": "0.001",
        "avgPrice": "43250.50",
        "price": "0",
        "clientOrderId": "abc123",
    }

    result = place_market_order(client, "btcusdt", "buy", 0.001)  # type: ignore[arg-type]

    assert isinstance(result, OrderResult)
    assert result.order_id == 123456789
    assert result.symbol == "BTCUSDT"
    assert result.side == "BUY"
    assert result.status == "FILLED"
    assert result.executed_qty == 0.001
    assert result.avg_price == 43250.50
    client.place_futures_order.assert_called_once()
    call_kw = client.place_futures_order.call_args[1]
    assert call_kw["type"] == "MARKET"
    assert call_kw["symbol"] == "BTCUSDT"
    client.get_futures_order.assert_not_called()


def test_place_market_order_polls_until_filled() -> None:
    client = _make_client()
    client.place_futures_order.return_value = {
        "orderId": 9001,
        "symbol": "BTCUSDT",
        "side": "BUY",
        "type": "MARKET",
        "status": "NEW",
        "origQty": "0.002",
        "executedQty": "0",
        "avgPrice": "0",
        "price": "0",
        "clientOrderId": "p1",
    }
    client.get_futures_order.return_value = {
        "orderId": 9001,
        "symbol": "BTCUSDT",
        "side": "BUY",
        "type": "MARKET",
        "status": "FILLED",
        "origQty": "0.002",
        "executedQty": "0.002",
        "avgPrice": "95000.00",
        "price": "0",
        "clientOrderId": "p1",
    }

    result = place_market_order(client, "BTCUSDT", "BUY", 0.002)  # type: ignore[arg-type]

    assert result.status == "FILLED"
    assert result.avg_price == 95000.00
    client.get_futures_order.assert_called()
    client.get_futures_order.assert_called_with(symbol="BTCUSDT", orderId=9001)


def test_place_limit_order_returns_order_result() -> None:
    client = _make_client()
    client.place_futures_order.return_value = {
        "orderId": 99,
        "symbol": "ETHUSDT",
        "side": "SELL",
        "type": "LIMIT",
        "status": "NEW",
        "origQty": "0.01",
        "executedQty": "0",
        "avgPrice": "0",
        "price": "3200",
        "clientOrderId": "cid-limit",
    }

    result = place_limit_order(client, "ethusdt", "sell", 0.01, 3200.0)  # type: ignore[arg-type]

    assert result.order_id == 99
    assert result.price == 3200.0
    call_kw = client.place_futures_order.call_args[1]
    assert call_kw["type"] == "LIMIT"
    assert call_kw["timeInForce"] == "GTC"
    assert call_kw["price"] == 3200.0


def test_place_stop_limit_order_returns_order_result() -> None:
    client = _make_client()
    client.place_futures_order.return_value = {
        "algoId": 555,
        "symbol": "BTCUSDT",
        "side": "BUY",
        "type": "STOP",
        "status": "NEW",
        "quantity": "0.001",
        "executedQty": "0",
        "avgPrice": "0",
        "price": "44000",
        "clientAlgoId": "algo-cid",
    }

    result = place_stop_limit_order(
        client, "BTCUSDT", "BUY", 0.001, 44000.0, 43500.0
    )  # type: ignore[arg-type]

    assert result.order_id == 555
    assert result.client_order_id == "algo-cid"
    call_kw = client.place_futures_order.call_args[1]
    assert call_kw["type"] == "STOP"
    assert call_kw["stopPrice"] == 43500.0


def test_trading_bot_error_propagates_from_client() -> None:
    client = _make_client()
    client.place_futures_order.side_effect = TradingBotError("API failure")

    with pytest.raises(TradingBotError, match="API failure"):
        place_market_order(client, "BTCUSDT", "BUY", 0.001)  # type: ignore[arg-type]
