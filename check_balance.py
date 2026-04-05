"""Print Binance Futures Testnet wallet balances with non-zero balance.

Run from project root after configuring .env (same credentials as cli.py).

Usage:
    python check_balance.py
"""

from __future__ import annotations

from binance.client import Client

from config import API_KEY, API_SECRET, TESTNET_BASE_URL, require_credentials


def main() -> None:
    require_credentials()
    client = Client(API_KEY, API_SECRET, testnet=True)
    client.FUTURES_TESTNET_URL = f"{TESTNET_BASE_URL.rstrip('/')}/fapi"
    balances = client.futures_account_balance()
    shown = False
    for row in balances:
        bal = float(row.get("balance", 0) or 0)
        if bal > 0:
            print(row)
            shown = True
    if not shown:
        print("No non-zero balances. Use the testnet dashboard Get Funds / voucher first.")


if __name__ == "__main__":
    main()
