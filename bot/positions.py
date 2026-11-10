"""Risk limits, order execution and trade management.

RISK (checked before every entry, against the exchange's positions, not local belief):
  - KILL_SWITCH file present -> no new entries (open trades keep their stop / target).
  - Realised R today <= -DAILY_LOSS_LIMIT_R -> no new entries until 00:00 UTC.
  - CONSECUTIVE_LOSS_LIMIT losses in a row -> no new entries for COOLDOWN_H hours.
  - At most MAX_POSITIONS open, one per symbol.
  - Live size: fixed margin MARGIN_USDT x the symbol's max leverage (lowered only if liquidation would come
    before the stop, see bot/sizing.py). Paper size: RISK_PCT % of PAPER_EQUITY at the stop (results are in R).

LIVE (TRADING_ENABLED=true): market entry, then the stop, then the target (bot.exchange.router).
  reconcile() every 15 s, as binance_ai_bot_vp does it:
    1. a managed position that is gone -> cancel what is left (no OCO on Binance), settle from userTrades.
    2. a managed position with no stop -> place it; if that fails, close at market. Unknown positions are never touched.
    3. our own exit orders with no position behind them -> cancel.
    4. a managed position with no target -> place it again.
    5. break-even: price reached BE_AT_R x risk -> stop moved to entry + fees.
PAPER (TRADING_ENABLED=false): the same signals, filled at the confirmation close, stop / target / break-even
  walked on the next 1m candles (stop first when both are inside one candle). Logged as mode=paper.
"""
import datetime as dt
import logging
import os
import time

import numpy as np

from bot import config as C
from bot import journal
from bot.config import MIN
from bot.exchange import filters
from bot.exchange.rest import ApiError
from bot.exchange.router import ROLE_ENTRY, order_role, spread_bps
from bot.market import now_ms
from bot.plan import rr_net
from bot.sizing import pick_leverage

log = logging.getLogger("bot.positions")


def utc_day(ms=None):
    t = time.time() if ms is None else ms / 1000
    return dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m-%d")


def r_result(d, entry, exit_px, risk, fees_usd=None, qty=None):
    gross = (exit_px - entry) * d / risk
    fees = (entry + exit_px) * C.FEE / risk if fees_usd is None else fees_usd / (risk * qty)
    return gross, gross - fees


class Risk:
    def __init__(self, state):
        self.s = state.setdefault("risk", dict(day=utc_day(), r_today=0.0, losses_in_row=0, cooldown_until=0))

    def _roll(self):
        if self.s["day"] != utc_day():
            self.s.update(day=utc_day(), r_today=0.0)

    def blocked(self, sym, open_syms, own_count):
        """Reasons no new entry is allowed now (empty = allowed). open_syms = every symbol with a position on
        the account (another bot's too: one-way mode allows one position per symbol); own_count = this bot's."""
        self._roll()
        why = []
        if os.path.exists(C.KILL_SWITCH_FILE):
            why.append("KILL_SWITCH file present")
        if self.s["r_today"] <= -C.DAILY_LOSS_LIMIT_R:
            why.append(f"daily loss limit: {self.s['r_today']:+.2f} R today")
        if time.time() * 1000 < self.s["cooldown_until"]:
            why.append(f"{C.CONSECUTIVE_LOSS_LIMIT} losses in a row: cooldown until "
                       f"{dt.datetime.fromtimestamp(self.s['cooldown_until'] / 1000):%H:%M}")
        if sym in open_syms:
            why.append("already a position on this symbol")
        if own_count >= C.MAX_POSITIONS:
            why.append(f"{own_count} LVN positions open (max {C.MAX_POSITIONS})")
        return why

    def record(self, net_r):
        self._roll()
        net_r = float(net_r)
        self.s["r_today"] += net_r
        if net_r <= -0.05:  # a break-even exit (about 0 R) is not counted as a loss
            self.s["losses_in_row"] += 1
        elif net_r >= 0.05:
            self.s["losses_in_row"] = 0
        if self.s["losses_in_row"] >= C.CONSECUTIVE_LOSS_LIMIT:
            self.s["cooldown_until"] = int(time.time() * 1000 + C.COOLDOWN_H * 3_600_000)
            self.s["losses_in_row"] = 0


def _be_price(d, entry):
    return entry * (1 + d * 2 * C.FEE)


class PaperExecutor:
    mode = "paper"

    def __init__(self, state, risk):
        self.pos = state.setdefault("paper_positions", {})
        self.risk = risk

    def open_symbols(self):
        return set(self.pos)

    def open(self, sig):
        risk = abs(sig["entry"] - sig["sl"])
        qty = C.PAPER_EQUITY * C.RISK_PCT / 100 / risk
        p = dict(sym=sig["sym"], dir=sig["dir"], entry=sig["entry"], sl=sig["sl"], sl0=sig["sl"], tp=sig["tp"],
                 risk=risk, qty=qty, opened=sig["t"], t_next=sig["t"], key=sig["key"], kind=sig["kind"], be=False)
        self.pos[sig["sym"]] = p
        journal.write("TRADE_OPEN", mode="paper", **p, rr=sig["rr"], tp_kind=sig["tp_kind"], modifiers=sig["modifiers"])
        log.info("PAPER OPEN %s %s entry %.6g sl %.6g tp %.6g", p["sym"], "LONG" if p["dir"] == 1 else "SHORT",
                 p["entry"], p["sl"], p["tp"])

    def on_candles(self, sym, m):
        p = self.pos.get(sym)
        if p is None:
            return
        d = p["dir"]
        k0 = int(np.searchsorted(m["t"], p["t_next"]))
        for k in range(k0, len(m["t"])):
            o, h, l = m["o"][k], m["h"][k], m["l"][k]
            p["t_next"] = int(m["t"][k]) + MIN
            if (l <= p["sl"]) if d == 1 else (h >= p["sl"]):
                px = min(p["sl"], o) if d == 1 else max(p["sl"], o)  # a gap through the stop fills at the open
                return self._close(p, px, "BREAK-EVEN" if p["be"] else "STOP", int(m["t"][k]))
            if (h >= p["tp"]) if d == 1 else (l <= p["tp"]):
                return self._close(p, p["tp"], "TARGET", int(m["t"][k]))
            if C.BE_AT_R and not p["be"] and ((h - p["entry"]) * d if d == 1 else (p["entry"] - l)) >= C.BE_AT_R * p["risk"]:
                p["sl"], p["be"] = _be_price(d, p["entry"]), True
                journal.write("TRADE_BE", mode="paper", sym=sym, sl=p["sl"])

    def _close(self, p, px, why, t):
        gross, net = r_result(p["dir"], p["entry"], px, p["risk"])
        self.pos.pop(p["sym"])
        self.risk.record(net)
        journal.write("TRADE_CLOSE", mode="paper", sym=p["sym"], key=p["key"], dir=p["dir"], entry=p["entry"],
                      exit=px, reason=why, gross_r=gross, net_r=net, opened=p["opened"], closed=t)
        log.info("PAPER CLOSE %s %s %.6g -> %.6g net %+.2f R", p["sym"], why, p["entry"], px, net)

    def reconcile(self):
        pass


class LiveExecutor:
    mode = "live"

    def __init__(self, state, risk, rest, catalog, router):
        self.pos = state.setdefault("live_positions", {})
        self.risk, self.rest, self.catalog, self.router = risk, rest, catalog, router
        self.exchange_syms = set()

    def open_symbols(self):
        return set(self.pos) | self.exchange_syms

    def equity(self):
        acc = self.rest.account()
        u = next(a for a in acc["assets"] if a["asset"] == "USDT")
        return float(u["walletBalance"]), float(u["availableBalance"])

    def open(self, sig):
        sym, d = sig["sym"], sig["dir"]
        side = "BUY" if d == 1 else "SELL"
        book = self.rest.book_ticker(sym)
        sp = spread_bps(book)
        if sp is None or sp > C.MAX_SPREAD_BPS:
            return self._skip(sig, f"spread {sp} bps > {C.MAX_SPREAD_BPS}")
        est = float(book["askPrice"] if d == 1 else book["bidPrice"])
        if (est - sig["sl"]) * d <= 0 or (sig["tp"] - est) * d <= 0:
            return self._skip(sig, f"price {est} already outside stop / target")
        rr = rr_net(est, sig["sl"], sig["tp"])
        if rr < C.MIN_RR:
            return self._skip(sig, f"RR at the live price {est} is {rr:.2f} < {C.MIN_RR}")
        spec = self.catalog.require(sym)
        wallet, avail = self.equity()
        margin = C.MARGIN_USDT
        if margin > avail * 0.95:
            return self._skip(sig, f"margin {margin} USDT > available {avail:.2f}")
        try:
            brackets = self.rest.leverage_brackets(sym)
        except ApiError as e:
            return self._skip(sig, f"leverage brackets: {e}")
        lv, why = pick_leverage(brackets, margin, est, sig["sl"], d, C.LIQ_BUFFER)
        if lv is None:
            return self._skip(sig, why)
        if lv["lev"] < lv["max_lev"]:
            log.warning("%s max leverage %sx puts liquidation before the stop, using %sx",
                        sym, lv["max_lev"], lv["lev"])
        qty = float(filters.round_quantity(lv["qty"], spec.market_step_size))
        try:
            filters.check_quantity(qty, spec, market_order=True)
            filters.check_notional(est, qty, spec)
        except filters.FilterRejection as e:
            return self._skip(sig, f"size: {e.code} {e.detail} (margin {margin} x {lv['lev']}x)")
        if not self.router.prepare_symbol(sym, lv["lev"]):
            return self._skip(sig, f"leverage {lv['lev']}x refused")
        sig = dict(sig, lev=lv["lev"], max_lev=lv["max_lev"], margin=margin, liq_est=lv["liq"],
                   risk_usdt=qty * (est - sig["sl"]) * d)
        order, err = self.router.market_entry(sym, side, qty)
        if order is None:
            return self._skip(sig, f"entry refused: {err}")
        filled = float(order.get("executedQty") or 0)
        fill_px = float(order.get("avgPrice") or 0) or est
        if filled <= 0:
            return self._skip(sig, f"entry not filled: {order.get('status')}")
        p = dict(sym=sym, dir=d, direction=side, entry=fill_px, sl=sig["sl"], sl0=sig["sl"], tp=sig["tp"],
                 risk=abs(fill_px - sig["sl"]), qty=filled, opened=now_ms(), key=sig["key"],
                 kind=sig["kind"], be=False, stop_id=None, target_id=None,
                 lev=sig["lev"], margin=sig["margin"], liq_est=sig["liq_est"])
        self.pos[sym] = p
        stop, err = self.router.place_stop(sym, side, p["sl"])
        if stop is None:
            log.error("%s stop refused after entry (%s) - closing at market", sym, err)
            self.router.close_at_market(sym, reason=f"stop refused: {err}")
            journal.write("TRADE_OPEN", mode="live", **p, note=f"stop refused ({err}), closed at market")
            return
        p["stop_id"] = int(stop.get("algoId") or 0)
        tgt, err = self.router.place_target(sym, side, p["tp"], filled)
        if tgt is not None:
            p["target_id"] = int(tgt.get("orderId") or 0)
        else:
            log.warning("%s target not placed (%s), retried by reconcile", sym, err)
        journal.write("TRADE_OPEN", mode="live", **p, rr=rr_net(fill_px, p["sl"], p["tp"]), tp_kind=sig["tp_kind"],
                      modifiers=sig["modifiers"], signal_entry=sig["entry"])
        log.info("LIVE OPEN %s %s %s @ %.6g sl %.6g tp %.6g | margin %s USDT x %sx (max %sx), liq ~%.6g",
                 sym, side, filled, fill_px, p["sl"], p["tp"], p["margin"], p["lev"], sig["max_lev"], p["liq_est"])

    def _skip(self, sig, why):
        journal.write("ENTRY_SKIP", sym=sig["sym"], key=sig["key"], why=why)
        log.warning("%s entry skipped: %s", sig["sym"], why)

    def on_candles(self, sym, m):
        pass

    # ------------------------------------------------------------ reconcile
    def reconcile(self):
        try:
            rows = self.rest.position_risk()
        except ApiError as e:
            log.error("positionRisk failed, reconcile skipped: %s", e)
            return
        ex = {r["symbol"]: r for r in rows if float(r["positionAmt"]) != 0}
        self.exchange_syms = set(ex)
        orders = {}

        def open_orders(sym):
            if sym not in orders:
                try:
                    orders[sym] = list(self.rest.open_orders(sym) or []) + list(self.rest.open_algo_orders(sym) or [])
                except ApiError as e:
                    log.error("%s open orders failed: %s", sym, e)
                    return None
            return orders[sym]

        for sym in list(self.pos):  # 1. finished
            if sym not in ex:
                p = self.pos.pop(sym)
                self.router.cancel_ours(sym)  # never cancel another bot's orders on this symbol
                self._settle(p)
        for sym, r in ex.items():  # 2. no stop
            p = self.pos.get(sym)
            oo = open_orders(sym)
            if oo is None:
                continue
            has_stop = any((o.get("type") or o.get("orderType")) in ("STOP_MARKET", "STOP") for o in oo)
            if not has_stop:
                if p is None:
                    log.error("%s UNMANAGED position %s with no stop - not touching it", sym, r["positionAmt"])
                    continue
                log.error("%s managed position has no stop - placing it", sym)
                stop, err = self.router.place_stop(sym, p["direction"], p["sl"])
                if stop is None:
                    self.router.close_at_market(sym, reason=f"unprotectable: {err}")
                else:
                    p["stop_id"] = int(stop.get("algoId") or 0)
                orders.pop(sym, None)
                continue
            if p is None:
                continue
            has_tgt = any(o.get("type") == "LIMIT" and o.get("reduceOnly") in (True, "true") for o in oo)
            if not has_tgt:  # 4. no target
                tgt, err = self.router.place_target(sym, p["direction"], p["tp"], abs(float(r["positionAmt"])))
                if tgt is not None:
                    p["target_id"] = int(tgt.get("orderId") or 0)
            mark = float(r.get("markPrice") or 0)  # 5. break-even
            if C.BE_AT_R and not p["be"] and mark and (mark - p["entry"]) * p["dir"] >= C.BE_AT_R * p["risk"]:
                self._move_stop(p, _be_price(p["dir"], p["entry"]))
        try:  # 3. orphan orders
            allo = list(self.rest.open_orders() or []) + list(self.rest.open_algo_orders() or [])
        except ApiError as e:
            log.error("open orders failed: %s", e)
            return
        for o in allo:
            sym = o.get("symbol")
            cid = o.get("clientOrderId") or o.get("clientAlgoId") or ""
            if order_role(cid) == ROLE_ENTRY:
                self.router.cancel(sym, o.get("orderId"))
                continue
            if sym in ex or not order_role(cid):
                continue
            if "algoId" in o:
                self.router.cancel_algo(sym, o["algoId"])
            else:
                self.router.cancel(sym, o.get("orderId"))
            log.warning("%s cancelled orphan exit order (no position)", sym)

    def _move_stop(self, p, new_sl):
        sym = p["sym"]
        if p.get("stop_id"):
            self.router.cancel_algo(sym, p["stop_id"])
        stop, err = self.router.place_stop(sym, p["direction"], new_sl)
        if stop is None:
            log.error("%s break-even stop refused (%s) - putting the old stop back", sym, err)
            stop, err = self.router.place_stop(sym, p["direction"], p["sl"])
            if stop is None:
                self.router.close_at_market(sym, reason=f"no stop possible: {err}")
                return
        else:
            p["sl"], p["be"] = new_sl, True
            journal.write("TRADE_BE", mode="live", sym=sym, sl=new_sl)
        p["stop_id"] = int(stop.get("algoId") or 0)

    def _settle(self, p):
        """Exit from userTrades (only fills carry the real price and fees). R against the original stop."""
        sym = p["sym"]
        try:
            trades = self.rest.user_trades(sym, start_ms=p["opened"] - 5000)
        except ApiError as e:
            log.error("%s userTrades failed: %s", sym, e)
            trades = []
        exit_side = "SELL" if p["dir"] == 1 else "BUY"
        q = v = fee = 0.0
        for tr in trades:
            fee += float(tr.get("commission") or 0)
            if tr.get("side") == exit_side:
                q += float(tr["qty"])
                v += float(tr["qty"]) * float(tr["price"])
        if q <= 0:
            journal.write("TRADE_CLOSE", mode="live", sym=sym, key=p["key"], reason="UNKNOWN (no exit fills found)")
            log.error("%s closed but no exit fills found - R not recorded", sym)
            return
        px = v / q
        risk0 = abs(p["entry"] - p["sl0"])
        gross, net = r_result(p["dir"], p["entry"], px, risk0, fees_usd=fee, qty=q)
        why = "TARGET" if (px - p["tp"]) * p["dir"] >= 0 else "BREAK-EVEN" if p["be"] and abs(px - p["sl"]) < risk0 * 0.2 \
            else "STOP" if (px - p["sl0"]) * p["dir"] <= 0 else "OTHER"
        self.risk.record(net)
        journal.write("TRADE_CLOSE", mode="live", sym=sym, key=p["key"], dir=p["dir"], entry=p["entry"], exit=px,
                      reason=why, gross_r=gross, net_r=net, fees=fee, qty=q, opened=p["opened"])
        log.info("LIVE CLOSE %s %s %.6g -> %.6g net %+.2f R (fees %.4f)", sym, why, p["entry"], px, net, fee)
