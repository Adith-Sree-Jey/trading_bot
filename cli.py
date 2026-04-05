"""CLI entry point for Binance Futures Testnet order placement."""

from __future__ import annotations

import logging
import sys

import click
from colorama import Fore, Style, init as colorama_init
from tabulate import tabulate

from bot.client import BinanceClient, TradingBotError
from bot.logging_config import setup_logging
from bot.orders import (
    place_limit_order,
    place_market_order,
    place_stop_limit_order,
)
from bot.validators import (
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_stop_price,
    validate_symbol,
)
from config import API_KEY, API_SECRET, TESTNET_BASE_URL, require_credentials

logger = logging.getLogger(__name__)


def _fmt_num(v: float | None) -> str:
    if v is None:
        return "N/A"
    return str(v)


def _configure_utf8_stdio() -> None:
    """Avoid UnicodeEncodeError on Windows console (cp1252) for tables and symbols."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass


@click.group()
def cli() -> None:
    """Binance Futures Testnet trading bot (USDT-M)."""


@cli.command("trade")
@click.option(
    "--symbol",
    required=True,
    help="Trading pair e.g. BTCUSDT",
)
@click.option(
    "--side",
    required=True,
    type=click.Choice(["BUY", "SELL"], case_sensitive=False),
    metavar="[BUY|SELL]",
    help="Order side",
)
@click.option(
    "--type",
    "order_type",
    required=True,
    type=click.Choice(["MARKET", "LIMIT", "STOP_LIMIT"], case_sensitive=False),
    metavar="[MARKET|LIMIT|STOP_LIMIT]",
    help="Order type",
)
@click.option("--quantity", required=True, type=float, help="Order quantity")
@click.option("--price", type=float, default=None, help="Limit price (LIMIT / STOP_LIMIT)")
@click.option(
    "--stop-price",
    type=float,
    default=None,
    help="Stop trigger price (STOP_LIMIT only)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Validate and preview without placing order",
)
def trade(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: float | None,
    stop_price: float | None,
    dry_run: bool,
) -> None:
    """Place a futures order on Binance Testnet."""
    colorama_init(autoreset=False)
    _configure_utf8_stdio()
    setup_logging()

    try:
        sym = validate_symbol(symbol)
        sd = validate_side(side)
        ot = validate_order_type(order_type)
        qty = validate_quantity(quantity)
        px = validate_price(price, ot)
        sp = validate_stop_price(stop_price, ot)
    except click.BadParameter as e:
        click.echo(str(e), err=True)
        sys.exit(1)

    summary_rows = [
        ["Symbol", sym],
        ["Side", sd],
        ["Order Type", ot],
        ["Quantity", qty],
        ["Price", _fmt_num(px) if px is not None else "N/A"],
        ["Stop Price", _fmt_num(sp) if sp is not None else "N/A"],
    ]
    click.echo(
        tabulate(
            summary_rows,
            headers=["Field", "Value"],
            tablefmt="fancy_grid",
        )
    )

    if dry_run:
        click.echo(
            f"{Fore.YELLOW}DRY RUN — Order not placed.{Style.RESET_ALL}"
        )
        sys.exit(0)

    try:
        require_credentials()
    except EnvironmentError as e:
        click.echo(str(e), err=True)
        sys.exit(1)

    client = BinanceClient(API_KEY, API_SECRET, TESTNET_BASE_URL)

    try:
        if ot == "MARKET":
            result = place_market_order(client, sym, sd, qty)
        elif ot == "LIMIT":
            result = place_limit_order(client, sym, sd, qty, float(px))
        else:
            result = place_stop_limit_order(
                client, sym, sd, qty, float(px), float(sp)
            )
    except TradingBotError as e:
        click.echo(
            f"{Fore.RED}❌ {e}{Style.RESET_ALL}",
            err=True,
        )
        logger.error("TradingBotError: %s", e)
        sys.exit(1)
    except Exception:
        click.echo(
            f"{Fore.RED}❌ Unexpected error — check log file{Style.RESET_ALL}",
            err=True,
        )
        logger.exception("Unexpected error during order placement")
        sys.exit(1)

    resp_rows = [
        ["Order ID", result.order_id],
        ["Status", result.status],
        ["Executed Qty", result.executed_qty],
        ["Avg Price", result.avg_price],
        ["Client Order ID", result.client_order_id],
    ]
    click.echo(
        f"{Fore.GREEN}✅ Order placed.{Style.RESET_ALL}\n"
        + tabulate(
            resp_rows,
            headers=["Field", "Value"],
            tablefmt="fancy_grid",
        )
    )


if __name__ == "__main__":
    cli()
