"""Input validation for CLI order parameters."""

from __future__ import annotations

import re

import click

_ALLOWED_SUFFIXES = ("USDT", "BTC", "ETH", "BNB")


def validate_symbol(symbol: str) -> str:
    s = symbol.strip().upper()
    if not (3 <= len(s) <= 12):
        raise click.BadParameter("Symbol must be 3–12 characters.")
    if not re.fullmatch(r"[A-Z0-9]+", s):
        raise click.BadParameter("Symbol must be alphanumeric only.")
    if not any(s.endswith(sfx) for sfx in _ALLOWED_SUFFIXES):
        raise click.BadParameter(
            f"Symbol must end with one of: {', '.join(_ALLOWED_SUFFIXES)}."
        )
    return s


def validate_quantity(quantity: float) -> float:
    if quantity <= 0:
        raise click.BadParameter("Quantity must be positive.")
    if quantity <= 0.0001:
        raise click.BadParameter("Quantity must be greater than 0.0001.")
    if quantity > 1_000_000:
        raise click.BadParameter("Quantity must not exceed 1,000,000.")
    return float(quantity)


def validate_price(price: float | None, order_type: str) -> float | None:
    ot = order_type.upper()
    if ot == "MARKET":
        return None
    if ot in ("LIMIT", "STOP_LIMIT"):
        if price is None:
            raise click.BadParameter(f"Price is required for {ot} orders.")
        if price <= 0:
            raise click.BadParameter("Price must be positive.")
        return float(price)
    raise click.BadParameter(f"Unknown order type: {order_type}.")


def validate_side(side: str) -> str:
    s = side.strip().upper()
    if s not in ("BUY", "SELL"):
        raise click.BadParameter("Side must be BUY or SELL.")
    return s


def validate_order_type(order_type: str) -> str:
    o = order_type.strip().upper()
    if o not in ("MARKET", "LIMIT", "STOP_LIMIT"):
        raise click.BadParameter("Order type must be MARKET, LIMIT, or STOP_LIMIT.")
    return o


def validate_stop_price(stop_price: float | None, order_type: str) -> float | None:
    ot = order_type.upper()
    if ot == "STOP_LIMIT":
        if stop_price is None:
            raise click.BadParameter("Stop price is required for STOP_LIMIT orders.")
        if stop_price <= 0:
            raise click.BadParameter("Stop price must be positive.")
        return float(stop_price)
    if stop_price is not None:
        raise click.BadParameter("Stop price must only be set for STOP_LIMIT orders.")
    return None
