"""Unit tests for bot.validators."""

import pytest
from click import BadParameter

from bot.validators import (
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_stop_price,
    validate_symbol,
)


def test_valid_symbol_uppercased() -> None:
    assert validate_symbol("btcusdt") == "BTCUSDT"


def test_invalid_symbol_too_short() -> None:
    with pytest.raises(BadParameter):
        validate_symbol("BT")


def test_invalid_symbol_wrong_suffix() -> None:
    with pytest.raises(BadParameter):
        validate_symbol("BTCXYZ")


def test_invalid_symbol_special_chars() -> None:
    with pytest.raises(BadParameter):
        validate_symbol("BTC-USDT")


def test_valid_quantity() -> None:
    assert validate_quantity(0.001) == 0.001


def test_quantity_zero_raises() -> None:
    with pytest.raises(BadParameter):
        validate_quantity(0.0)


def test_quantity_negative_raises() -> None:
    with pytest.raises(BadParameter):
        validate_quantity(-1.0)


def test_quantity_too_small_raises() -> None:
    with pytest.raises(BadParameter):
        validate_quantity(0.0001)


def test_quantity_too_large_raises() -> None:
    with pytest.raises(BadParameter):
        validate_quantity(2_000_000)


def test_limit_without_price_raises() -> None:
    with pytest.raises(BadParameter):
        validate_price(None, "LIMIT")


def test_market_ignores_price_returns_none() -> None:
    assert validate_price(100.0, "MARKET") is None


def test_valid_buy_sell() -> None:
    assert validate_side("buy") == "BUY"
    assert validate_side("SELL") == "SELL"


def test_invalid_side_raises() -> None:
    with pytest.raises(BadParameter):
        validate_side("HOLD")


def test_stop_limit_without_stop_price_raises() -> None:
    with pytest.raises(BadParameter):
        validate_stop_price(None, "STOP_LIMIT")


def test_valid_stop_limit_with_stop_price() -> None:
    assert validate_stop_price(100.0, "STOP_LIMIT") == 100.0


def test_validate_order_type_valid() -> None:
    assert validate_order_type("market") == "MARKET"


def test_validate_order_type_invalid() -> None:
    with pytest.raises(BadParameter):
        validate_order_type("FOK")
