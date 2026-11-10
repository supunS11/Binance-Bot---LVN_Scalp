#!/usr/bin/env python3
"""Connects to Binance USD-M with the keys in .env and checks the account. Places no orders.

    python -m bot.account

Shows: testnet or mainnet, clock offset, USDT balance, position mode, open positions, open orders.
On mainnet it also reads the key's permissions and warns if withdrawals are on or there is no IP whitelist.
"""
import sys

from bot import config as C
from bot.exchange.rest import ApiError, RestClient


def client():
    """Signed client for the account in .env (testnet unless USE_TESTNET=false)."""
    if not C.BINANCE_API_KEY or not C.BINANCE_API_SECRET:
        raise SystemExit("No API key: copy .env.example to .env and fill BINANCE_API_KEY / BINANCE_API_SECRET.")
    rest = RestClient()
    rest.sync_time()
    return rest


def key_restrictions():
    """Mainnet only: permissions of the key (this endpoint is on the spot API host)."""
    rest = RestClient()
    rest.base = "https://api.binance.com"
    rest.sync_time = lambda: 0  # spot host has no /fapi/v1/time; the futures offset is close enough
    return rest._request("GET", "/sapi/v1/account/apiRestrictions", weight=1, signed=True)


def check():
    net = "TESTNET" if C.USE_TESTNET else "MAINNET (real money)"
    print(f"Account:  {net}")
    print(f"Trading:  {'ENABLED - the bot may place orders' if C.TRADING_ENABLED else 'off (signals only)'}")
    rest = client()
    print(f"Clock:    local clock is {-rest._time_offset_ms:+d} ms vs Binance (corrected when signing)")
    ok = True
    try:
        acc = rest.account()
    except ApiError as e:
        print(f"FAILED to read the account: {e}")
        if e.code in (-2014, -2015):
            print("  -> wrong key / secret, key not enabled for Futures, or this IP is not on the key's whitelist."
                  + (" Testnet keys come from testnet.binancefuture.com, not from binance.com." if C.USE_TESTNET else ""))
        return False
    usdt = next((a for a in acc.get("assets", []) if a["asset"] == "USDT"), None)
    if usdt:
        print(f"USDT:     wallet {float(usdt['walletBalance']):.2f}, available {float(usdt['availableBalance']):.2f}, "
              f"unrealized PnL {float(usdt['unrealizedProfit']):+.2f}")
    print(f"Can trade: {acc.get('canTrade')}")
    dual = rest.position_mode().get("dualSidePosition")
    print(f"Position mode: {'HEDGE (two-way)' if dual else 'ONE-WAY'}" + ("  <- the bot expects ONE-WAY" if dual else ""))
    ok &= not dual
    pos = [p for p in rest.position_risk() if float(p["positionAmt"]) != 0]
    print(f"Open positions: {len(pos)}")
    for p in pos:
        print(f"  {p['symbol']} {float(p['positionAmt']):+g} @ {float(p['entryPrice']):g}, "
              f"PnL {float(p['unRealizedProfit']):+.2f}, leverage {p.get('leverage')}")
    orders, algos = rest.open_orders(), rest.open_algo_orders()
    print(f"Open orders: {len(orders)} normal, {len(algos) if isinstance(algos, list) else '?'} stop/TP (algo)")
    if not C.USE_TESTNET:
        try:
            r = key_restrictions()
            print(f"Key: futures {r.get('enableFutures')}, withdrawals {r.get('enableWithdrawals')}, "
                  f"IP whitelist {r.get('ipRestrict')}")
            if r.get("enableWithdrawals"):
                print("  WARNING: withdrawals are ON for this key. Turn them off on binance.com > API Management.")
                ok = False
            if not r.get("ipRestrict"):
                print("  WARNING: no IP whitelist on this key. Add your IP on binance.com > API Management.")
                ok = False
        except ApiError as e:
            print(f"Key permissions: could not read ({e})")
    print("RESULT: OK" if ok else "RESULT: connected, but fix the warnings above")
    return ok


if __name__ == "__main__":
    sys.exit(0 if check() else 1)
