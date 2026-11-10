#!/usr/bin/env python3
"""LVN scalp bot, 1H/5m (Scalp_LVN_1H5m.pine rules). Live loop.

    python -m bot.main

Mode comes from .env: TRADING_ENABLED=false -> paper (signals + simulated trades, no orders),
TRADING_ENABLED=true -> real orders on the account in .env (testnet unless USE_TESTNET=false).

EVERY MINUTE (2 s after the 1m close):
  1. make sure every symbol has the closed 1m candle (WebSocket, REST backfill if missing)
  2. zone watch on the new candle(s): touches, CHoCH / BOS, order flow, plan -> signals (bot.watch)
  3. signals -> risk limits -> entry (bot.positions)
  4. at a 5m close: the zone engine runs again for every symbol (bot.zones), zones are re-armed / dropped
  5. live/status.md and live/state.json are written
EVERY 15 s (live): reconcile positions and orders with Binance (stop, target, break-even, settle).
STREAMS: <sym>@kline_1m + !forceOrder@arr (market), <sym>@depth20@500ms for symbols being watched (public).
"""
import asyncio
import datetime as dt
import json
import logging
import os
import threading
import time

import websockets

from bot import config as C
from bot import journal
from bot.config import MIN
from bot.market import Store, now_ms, top_symbols
from bot.orderflow import LiveFlow
from bot.positions import LiveExecutor, PaperExecutor, Risk
from bot.watch import Watcher
from bot.zones import snapshot

log = logging.getLogger("bot")
FIVE = 5 * MIN


def load_state():
    try:
        with open(C.STATE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


class Bot:
    def __init__(self, symbols):
        os.makedirs(C.LIVE, exist_ok=True)
        self.state = load_state()
        self.flow = LiveFlow()
        self.stores = {s: Store(s) for s in symbols}
        self.watchers = {}
        self.snaps = {}
        self.risk = Risk(self.state)
        self.ex_lock = threading.Lock()  # entry and reconcile must never interleave (duplicate stops)
        self.w_lock = threading.RLock()  # watchers: 1m step and zone updates must never interleave
        self.zone_busy = threading.Lock()  # one zone pass at a time (it runs in its own thread)
        if C.TRADING_ENABLED:
            from bot.account import client
            from bot.exchange.router import Router
            from bot.exchange.symbols import SymbolCatalog
            rest = client()
            if rest.position_mode().get("dualSidePosition"):
                raise SystemExit("Account is in HEDGE mode. Set Binance Futures to ONE-WAY mode first.")
            catalog = SymbolCatalog(rest)
            self.ex = LiveExecutor(self.state, self.risk, rest, catalog, Router(rest, catalog))
        else:
            self.ex = PaperExecutor(self.state, self.risk)

    # ------------------------------------------------------------ start
    def load(self):
        saved = self.state.get("watchers", {})
        for i, st in enumerate(self.stores.values(), 1):
            st.load()
            st.save()
            w = Watcher(st, self.flow)
            w.warmup()
            w.load_state(saved.get(st.sym, {}))
            self.watchers[st.sym] = w
            log.info("%d/%d %s loaded: %d x 1m candles", i, len(self.stores), st.sym, len(st.m["t"]))
        self.zone_pass()
        self._reconcile()

    def zone_pass(self):
        """Zone engine for every symbol. The heavy part runs without the watcher lock, so the 1m watch
        (touches, confirmations, entries) is never held up, even with 200 symbols (~1-2 min per pass)."""
        if not self.zone_busy.acquire(blocking=False):
            log.warning("previous zone pass still running, this 5m pass skipped")
            return
        try:
            t0 = time.time()
            for sym, st in self.stores.items():
                try:
                    st.refresh_htf()
                    snap = snapshot(st)
                except Exception as e:  # one symbol must not stop the others
                    log.exception("%s zone engine failed: %s", sym, e)
                    continue
                with self.w_lock:
                    self.snaps[sym] = snap
                    self.watchers[sym].on_snapshot(snap)
            with self.w_lock:
                log.info("zones updated in %.1fs: %d armed, %d watching", time.time() - t0,
                         sum(len(w.armed) for w in self.watchers.values()), sum(len(w.watches) for w in self.watchers.values()))
        finally:
            self.zone_busy.release()

    def save(self):
        with self.w_lock:
            self.state["watchers"] = {s: w.to_state() for s, w in self.watchers.items()}
        tmp = C.STATE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.state, f, default=float)
        os.replace(tmp, C.STATE)

    # ------------------------------------------------------------ every minute
    def minute(self, close_ms):
        for st in self.stores.values():
            if st.last() != close_ms - MIN:
                n = st.backfill()
                if n:
                    log.info("%s: %d x 1m filled from REST", st.sym, n)
        with self.w_lock:
            for sym, w in self.watchers.items():
                for sig in w.on_candles():
                    self.on_signal(sig)
                self.ex.on_candles(sym, self.stores[sym].m)
        if close_ms % FIVE == 0:
            threading.Thread(target=self.zone_pass, name="zone-pass", daemon=True).start()
        if close_ms % (60 * MIN) == 0:
            for st in self.stores.values():
                st.save()
        self.save()
        self.status()

    def on_signal(self, sig):
        age = now_ms() - sig["t"]
        if age > 90_000:
            journal.write("ENTRY_SKIP", sym=sig["sym"], key=sig["key"], why=f"signal is {age / 1000:.0f} s old (data was late)")
            return
        why = self.risk.blocked(sig["sym"], self.ex.open_symbols(), len(self.ex.pos))
        if why:
            journal.write("ENTRY_SKIP", sym=sig["sym"], key=sig["key"], why="; ".join(why))
            log.warning("%s signal not taken: %s", sig["sym"], "; ".join(why))
            return
        try:
            with self.ex_lock:
                self.ex.open(sig)
        except Exception as e:
            log.exception("%s entry failed: %s", sig["sym"], e)
            journal.write("ENTRY_SKIP", sym=sig["sym"], key=sig["key"], why=f"error: {e!r}")

    # ------------------------------------------------------------ report
    def status(self):
        with self.w_lock:
            self._status()

    def _status(self):
        now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
        r = self.risk.s
        o = [f"# LVN bot status {now}", "",
             f"Mode: **{'LIVE ' + ('TESTNET' if C.USE_TESTNET else 'MAINNET') if C.TRADING_ENABLED else 'PAPER'}**, "
             f"confirm {C.CONFIRM}, nested only {C.REQUIRE_NESTED}, BE at {C.BE_AT_R}R. Today (UTC {r['day']}): {r['r_today']:+.2f} R. "
             f"Kill switch: {'ON' if os.path.exists(C.KILL_SWITCH_FILE) else 'off'}", "", "## Open positions", ""]
        for p in self.ex.pos.values():
            o.append(f"- {p['sym']} {'LONG' if p['dir'] == 1 else 'SHORT'} entry {p['entry']:.6g} stop {p['sl']:.6g} "
                     f"target {p['tp']:.6g}{' (break-even)' if p['be'] else ''}")
        o += ["", "## Watching (zone touched, waiting for confirmation)", ""]
        for w in self.watchers.values():
            for x in w.watches.values():
                o.append(f"- {x['sym']} {x['side']} {x['kind']} {x['bot']:.6g} - {x['top']:.6g}, step "
                         f"{('touched', 'touched', 'CHoCH', 'BOS')[x['react'].step]}, reaction extreme {x['ext_px']:.6g}")
            for p in w.pending.values():
                o.append(f"- {w.sym} fallback S/D {p['bot']:.6g} - {p['top']:.6g} (waiting for the touch)")
        o += ["", "## Armed zones (valid, waiting for the first touch)", "",
              "| Symbol | Side | Zone | Price | Distance x ATR | Age h | S/D gap ATR | Trend |", "|---|---|---:|---:|---:|---:|---:|---|"]
        for sym, w in self.watchers.items():
            s = self.snaps.get(sym)
            for z in sorted(w.armed.values(), key=lambda z: z["dist_atr"]):
                o.append(f"| {sym} | {z['side']} | {z['bot']:.6g} - {z['top']:.6g} | {s['close']:.6g} | {z['dist_atr']:.1f} | "
                         f"{z['age_h']:.1f} | {'' if z['gap'] is None else round(z['gap'], 1)} | "
                         f"1H {'UP' if s['trend1h'] == 1 else 'DOWN'} STRONG |")
        o += ["", "## Trend per symbol", ""]
        for sym, s in self.snaps.items():
            t = {1: "UP", -1: "DOWN", 0: "none"}
            o.append(f"- {sym}: 1H {t[s['trend1h']]} {'STRONG' if s['strong1h'] else 'weak'}, 4H {t[s['trend4h']]}")
        with open(os.path.join(C.LIVE, "status.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(o) + "\n")

    # ------------------------------------------------------------ async loops
    async def market_stream(self):
        url = C.WS + "/".join([f"{s.lower()}@kline_1m" for s in self.stores] + ["!forceOrder@arr"])
        while True:
            try:
                async with websockets.connect(url, open_timeout=15, ping_interval=None, max_size=2 ** 22) as ws:
                    log.info("market stream connected (%d symbols)", len(self.stores))
                    async for msg in ws:
                        x = json.loads(msg)
                        data = x["data"]
                        if x["stream"] == "!forceOrder@arr":
                            self.flow.on_liquidation(data["o"])
                            continue
                        k = data["k"]
                        if k["x"]:
                            st = self.stores.get(k["s"])
                            if st and not st.add(k):
                                await asyncio.to_thread(st.backfill)
            except Exception as e:
                log.warning("market stream dropped (%r), reconnecting in 5 s", e)
                await asyncio.sleep(5)

    def _watched(self):
        # no lock: this runs on the asyncio loop, which must never wait for an entry; the watcher keys
        # are fixed after load and a dict's truth value is read atomically
        return sorted(s for s, w in list(self.watchers.items()) if w.watches)

    async def depth_stream(self):
        """Top-20 book of the symbols with an active watch. Reconnects when that set changes."""
        while True:
            syms = self._watched()
            if not syms:
                await asyncio.sleep(5)
                continue
            url = C.WS_PUBLIC + "/".join(f"{s.lower()}@depth20@500ms" for s in syms)
            try:
                async with websockets.connect(url, open_timeout=15, ping_interval=None, max_size=2 ** 22) as ws:
                    while self._watched() == syms:
                        try:
                            msg = await asyncio.wait_for(ws.recv(), 5)
                        except asyncio.TimeoutError:
                            continue
                        x = json.loads(msg)
                        self.flow.on_depth(x["data"]["s"], x["data"])
            except Exception as e:
                log.warning("depth stream dropped (%r)", e)
                await asyncio.sleep(5)

    async def clock(self):
        while True:
            nxt = (now_ms() // MIN + 1) * MIN  # Binance time
            await asyncio.sleep((nxt - now_ms()) / 1000 + 2)
            # the closing kline of a quiet symbol can come a few seconds late: wait up to 10 s for the
            # WebSocket before the minute step backfills the missing ones over REST
            while now_ms() < nxt + 10_000 and any(st.last() != nxt - MIN for st in self.stores.values()):
                await asyncio.sleep(0.25)
            try:
                await asyncio.to_thread(self.minute, nxt)
            except Exception as e:
                log.exception("minute step failed: %s", e)

    async def reconcile_loop(self):
        while True:
            await asyncio.sleep(15)
            try:
                await asyncio.to_thread(self._reconcile)
            except Exception as e:
                log.exception("reconcile failed: %s", e)

    def _reconcile(self):
        with self.ex_lock:
            self.ex.reconcile()

    async def run(self):
        await asyncio.gather(self.market_stream(), self.depth_stream(), self.clock(), self.reconcile_loop())


def main():
    journal.setup_logging()
    C.apply_script_defaults()
    mode = ("LIVE on " + ("TESTNET" if C.USE_TESTNET else "MAINNET - REAL MONEY")) if C.TRADING_ENABLED else "PAPER (no orders)"
    log.info("LVN bot starting: %s", mode)
    syms = C.SCAN_SYMBOLS or top_symbols(C.UNIVERSE_SIZE)
    log.info("symbols (%d): %s", len(syms), " ".join(syms))
    bot = Bot(syms)
    bot.load()
    bot.save()
    bot.status()
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        bot.save()
        for st in bot.stores.values():
            st.save()
        log.info("stopped (open positions keep their stop and target on Binance)")


if __name__ == "__main__":
    main()
