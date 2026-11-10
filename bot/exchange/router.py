"""Order placement, adapted from binance_ai_bot_vp/execution/router.py (same venue rules, same safety order).

- Every order carries a client id starting with ORDER_TAG, so after a crash the bot can tell its own orders
  from manual ones. An unknown outcome (timeout) is resolved by querying that id, never by sending again.
- ENTRY: MARKET (the confirmation is a 1m close; waiting for a passive fill would miss the move).
- STOP FIRST, then target. STOP = STOP_MARKET closePosition through the Algo Order API (Binance moved all
  conditional orders there on 2025-12-09; /fapi/v1/order refuses them with -4120). TARGET = reduce-only LIMIT.
- A stop Binance would trigger at once (-2021) means the position is already past its stop: close at market.
"""
import logging
import uuid

from bot import config as C
from bot.exchange import filters
from bot.exchange.rest import ApiError

log = logging.getLogger("bot.router")
ORDER_TAG = "lvn"
ROLE_ENTRY, ROLE_STOP, ROLE_TARGET, ROLE_CLOSE = "e", "s", "t", "x"


def client_order_id(role, symbol):
    return f"{ORDER_TAG}{role}{symbol.replace('USDT', '')[:6]}{uuid.uuid4().hex[:10]}"[:36]


def is_ours(client_id):
    return bool(client_id) and str(client_id).startswith(ORDER_TAG)


def order_role(client_id):
    return str(client_id)[len(ORDER_TAG):len(ORDER_TAG) + 1] if is_ours(client_id) else ""


def spread_bps(book):
    bid, ask = float(book.get("bidPrice") or 0), float(book.get("askPrice") or 0)
    if bid <= 0 or ask < bid:
        return None
    return (ask - bid) / ((ask + bid) / 2) * 10_000


class Router:
    def __init__(self, rest, catalog):
        self.rest, self.catalog = rest, catalog

    def prepare_symbol(self, symbol, leverage):
        try:
            self.rest.set_margin_type(symbol, C.MARGIN_TYPE)
        except ApiError as e:
            log.warning("%s margin type: %s", symbol, e)
        try:
            self.rest.set_leverage(symbol, leverage)
        except ApiError as e:
            log.error("%s leverage %sx refused: %s", symbol, leverage, e)
            return False
        return True

    def market_entry(self, symbol, side, quantity):
        """Returns (order, None) or (None, reason). order has executedQty / avgPrice (RESULT response)."""
        spec = self.catalog.require(symbol)
        qty = filters.round_quantity(quantity, spec.market_step_size)
        cid = client_order_id(ROLE_ENTRY, symbol)
        try:
            filters.check_quantity(qty, spec, market_order=True)
            order = self.rest.new_order(symbol=symbol, side=side, type="MARKET", quantity=filters.quantity_str(qty, spec),
                                        newClientOrderId=cid, newOrderRespType="RESULT")
        except filters.FilterRejection as e:
            return None, f"{e.code}: {e.detail}"
        except ApiError as e:
            if e.code in (None, -1001, -1007):  # unknown outcome: the order may exist
                try:
                    return self.rest.query_order(symbol, client_order_id=cid), None
                except ApiError:
                    pass
            return None, f"{e.code}: {e.message}"
        return order, None

    def place_stop(self, symbol, direction, stop_price):
        """direction = 'BUY' for a long position. Returns (order, None) or (None, reason)."""
        spec = self.catalog.require(symbol)
        pos_side = "LONG" if direction == "BUY" else "SHORT"
        px = filters.round_stop_price(stop_price, spec.tick_size, pos_side)
        try:
            filters.check_price(px, spec)
            order = self.rest.new_algo_order(
                symbol=symbol, side="SELL" if direction == "BUY" else "BUY", type="STOP_MARKET",
                triggerPrice=filters.price_str(px, spec), closePosition="true",
                workingType=C.STOP_WORKING_TYPE, priceProtect="TRUE" if C.STOP_PRICE_PROTECT else "FALSE",
                clientAlgoId=client_order_id(ROLE_STOP, symbol))
        except filters.FilterRejection as e:
            return None, f"stop {e.code}: {e.detail}"
        except ApiError as e:
            if e.code == -2021:
                return None, "STOP_WOULD_TRIGGER_CLOSE_NOW"
            return None, f"stop {e.code}: {e.message}"
        return order, None

    def place_target(self, symbol, direction, target_price, quantity):
        spec = self.catalog.require(symbol)
        pos_side = "LONG" if direction == "BUY" else "SHORT"
        px = filters.round_target_price(target_price, spec.tick_size, pos_side)
        try:
            filters.check_price(px, spec)
            qty = filters.round_quantity(quantity, spec.step_size)
            filters.check_quantity(qty, spec)
            order = self.rest.new_order(symbol=symbol, side="SELL" if direction == "BUY" else "BUY", type="LIMIT",
                                        timeInForce="GTC", price=filters.price_str(px, spec),
                                        quantity=filters.quantity_str(qty, spec), reduceOnly="true",
                                        newClientOrderId=client_order_id(ROLE_TARGET, symbol))
        except filters.FilterRejection as e:
            return None, f"target {e.code}: {e.detail}"
        except ApiError as e:
            return None, f"target {e.code}: {e.message}"
        return order, None

    def close_at_market(self, symbol, reason=""):
        try:
            rows = self.rest.position_risk(symbol) or []
        except ApiError as e:
            log.error("%s cannot read position to close: %s", symbol, e)
            return None
        amt = next((float(r["positionAmt"]) for r in rows if r["symbol"] == symbol), 0.0)
        if amt == 0:
            return None
        spec = self.catalog.require(symbol)
        qty = filters.round_quantity(abs(amt), spec.market_step_size)
        log.warning("%s closing at market (%s), qty %s", symbol, reason, qty)
        try:
            return self.rest.new_order(symbol=symbol, side="SELL" if amt > 0 else "BUY", type="MARKET",
                                       quantity=filters.quantity_str(qty, spec), reduceOnly="true",
                                       newClientOrderId=client_order_id(ROLE_CLOSE, symbol))
        except ApiError as e:
            log.error("%s market close failed: %s", symbol, e)
            return None

    def cancel(self, symbol, order_id):
        try:
            return self.rest.cancel_order(symbol, order_id=order_id)
        except ApiError as e:
            if e.code in (-2011, -2013):
                return {"status": "ALREADY_GONE"}
            log.error("%s cancel failed: %s", symbol, e)
            return None

    def cancel_algo(self, symbol, algo_id):
        try:
            return self.rest.cancel_algo_order(symbol, algo_id=algo_id)
        except ApiError as e:
            if e.code in (-2011, -2013):
                return {"status": "ALREADY_GONE"}
            log.error("%s algo cancel failed: %s", symbol, e)
            return None

    def cancel_ours(self, symbol):
        """Cancels only this bot's open orders (client id starts with ORDER_TAG) on the symbol."""
        try:
            normal = list(self.rest.open_orders(symbol) or [])
            algo = list(self.rest.open_algo_orders(symbol) or [])
        except ApiError as e:
            log.error("%s open orders failed, nothing cancelled: %s", symbol, e)
            return
        for o in normal:
            if is_ours(o.get("clientOrderId")):
                self.cancel(symbol, o.get("orderId"))
        for o in algo:
            if is_ours(o.get("clientAlgoId")):
                self.cancel_algo(symbol, o.get("algoId"))

    def cancel_all(self, symbol):
        for f in (self.rest.cancel_all_orders, self.rest.cancel_all_algo_orders):
            try:
                f(symbol)
            except ApiError as e:
                log.error("%s cancel-all failed: %s", symbol, e)
