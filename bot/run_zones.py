#!/usr/bin/env python3
"""Step 1 of the bot: live 1H/5m LVN zone engine (no orders).

Keeps the last 21 days of closed 1m candles per symbol (Binance WebSocket, REST backfill for gaps).
After every 5m close it runs the backtest zone engine (backtest.run_symbol, Scalp_LVN_1H5m.pine defaults) and writes:
  live/zones.md      table: zones that pass every script filter + all live zones (to compare with TradingView)
  live/zones.json    the same, for the next bot steps
  logs/zone_events.jsonl   NEW zone / status change / zone gone, one line each

    python -m bot.run_zones --symbols BTCUSDT ETHUSDT SOLUSDT
    python -m bot.run_zones --top 20
    python -m bot.run_zones --symbols BTCUSDT --once     # one snapshot and exit
"""
import argparse
import asyncio
import datetime as dt
import json
import os
import time

import websockets

from bot import config as C
from bot.config import MIN
from bot.market import Store, now_ms, top_symbols
from bot.zones import entry_zone_why, snapshot

FIVE = 5 * MIN


def ts(t):
    return dt.datetime.fromtimestamp(t / 1000).strftime("%m-%d %H:%M")


def log(msg):
    print(f"[{dt.datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def trend_txt(s):
    t = {1: "UP", -1: "DOWN", 0: "none"}
    return f"1H {t[s['trend1h']]}{' STRONG' if s['strong1h'] else ' weak'}, 4H {t[s['trend4h']]}"


def report(snaps):
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    ok = sorted((z for s in snaps for z in s["zones"] if z["ok"]), key=lambda z: z["dist_pct"])
    o = [f"# Live LVN zones {now} (local time)", "",
         "Trend: " + "; ".join(f"{s['sym']} {trend_txt(s)}" for s in snaps), "",
         "## Zones the bot would arm (FRESH, NESTED, STRONG 1H, trend side, 4H, stop >= 0.30%)", "",
         "| Symbol | Side | TF | Nested | Zone | Price | Distance % | x ATR | Base gap (ATR) | Made | Age h | Ready |",
         "|---|---|---|---|---:|---:|---:|---:|---:|---|---:|---|"]
    px = {s["sym"]: s["close"] for s in snaps}
    for z in ok:
        o.append(f"| {z['sym']} | {z['side']} | {z['tf']} | {'yes' if z['nested'] else ''} | {z['bot']:.6g} - {z['top']:.6g} | "
                 f"{px[z['sym']]:.6g} | {z['dist_pct']:.2f} | {z['dist_atr']:.1f} | {'' if z['gap'] is None else round(z['gap'], 1)} | "
                 f"{ts(z['made'])} | {z['age_h']:.1f} | {'yes' if z['ready'] else 'WAIT'} |")
    if not ok:
        o.append("| none | | | | | | | | | | | |")
    o += ["", "## All live zones", "",
          "| Symbol | Side | TF | Status | Nested | Zone (incl. 0.25 ATR pad) | LVN/HVN | Made | Distance % | Not a trade because |",
          "|---|---|---|---|---|---:|---:|---|---:|---|"]
    for s in snaps:
        for z in sorted(s["zones"], key=lambda z: -z["made"]):
            o.append(f"| {z['sym']} | {z['side']} | {z['tf']} | {z['status']} | {'yes' if z['nested'] else ''} | "
                     f"{z['bot']:.6g} - {z['top']:.6g} | {z['ratio']:.2f} | {ts(z['made'])} | {z['dist_pct']:.2f} | {', '.join(z['why'])} |")
    return "\n".join(o) + "\n"


class Bot:
    def __init__(self, symbols):
        self.stores = {s: Store(s) for s in symbols}
        self.prev = None  # key -> zone, from the last snapshot
        os.makedirs(C.LIVE, exist_ok=True)
        os.makedirs(C.LOGS, exist_ok=True)

    def load(self):
        for i, st in enumerate(self.stores.values(), 1):
            st.load()
            st.save()
            log(f"{i}/{len(self.stores)} {st.sym}: {len(st.m['t'])} x 1m candles, last {ts(st.last())}")

    def compute(self):
        t0 = time.time()
        snaps = []
        for st in self.stores.values():
            try:
                st.refresh_htf()
                sn = snapshot(st)
                for z in sn["zones"]:
                    z["why"] = entry_zone_why(sn, z)
                    z["ok"] = not z["why"]
                    z["ready"] = z["age_h"] >= C.MIN_AGE_H
                snaps.append(sn)
            except Exception as e:  # one bad symbol must not stop the others
                log(f"{st.sym}: snapshot failed: {e!r}")
        text = report(snaps)
        with open(os.path.join(C.LIVE, "zones.md"), "w", encoding="utf-8") as f:
            f.write(text)
        with open(os.path.join(C.LIVE, "zones.json"), "w", encoding="utf-8") as f:
            json.dump(snaps, f, indent=1)
        self.events(snaps)
        n_ok = sum(z["ok"] for s in snaps for z in s["zones"])
        log(f"5m close done in {time.time() - t0:.1f}s: {sum(len(s['zones']) for s in snaps)} live zones, {n_ok} pass the filters")
        return snaps

    def events(self, snaps):
        cur = {z["key"]: z for s in snaps for z in s["zones"]}
        if self.prev is not None:
            ev = []
            for k, z in cur.items():
                p = self.prev.get(k)
                if p is None:
                    ev.append(("NEW", z))
                elif p["status"] != z["status"] or p["ok"] != z["ok"] or p["ready"] != z["ready"]:
                    ev.append(("CHANGE", z))
            ev += [("GONE", p) for k, p in self.prev.items() if k not in cur and p["sym"] in {s["sym"] for s in snaps}]
            with open(os.path.join(C.LOGS, "zone_events.jsonl"), "a", encoding="utf-8") as f:
                for kind, z in ev:
                    f.write(json.dumps(dict(at=int(time.time() * 1000), event=kind, **z)) + "\n")
                    tag = "TRADEABLE" if z["ok"] else ", ".join(z["why"])
                    log(f"{kind:6} {z['sym']} {z['tf']} {z['side']} {z['bot']:.6g}-{z['top']:.6g} {z['status']} ({tag})")
        self.prev = cur

    async def stream(self):
        url = C.WS + "/".join(f"{s.lower()}@kline_1m" for s in self.stores)
        while True:
            try:
                async with websockets.connect(url, open_timeout=15, ping_interval=None, max_size=2 ** 22) as ws:
                    log("WebSocket connected")
                    async for msg in ws:
                        k = json.loads(msg)["data"]["k"]
                        if k["x"]:  # closed 1m candle
                            st = self.stores[k["s"]]
                            if not st.add(k):
                                await asyncio.to_thread(st.backfill)
            except Exception as e:
                log(f"WebSocket dropped ({e!r}), reconnecting in 5 s")
                await asyncio.sleep(5)

    async def clock(self):
        """Runs the zone engine 4 s after every 5m close. Fills any missing 1m candle from REST first."""
        while True:
            nxt = (now_ms() // FIVE + 1) * FIVE
            await asyncio.sleep((nxt - now_ms()) / 1000 + 4)
            for st in self.stores.values():
                if st.last() != nxt - MIN:
                    n = await asyncio.to_thread(st.backfill)
                    log(f"{st.sym}: WebSocket candle missing at the 5m close, {n} filled from REST")
            await asyncio.to_thread(self.compute)
            if nxt % (60 * MIN) == 0:
                for st in self.stores.values():
                    st.save()

    async def run(self):
        await asyncio.gather(self.stream(), self.clock())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--symbols", nargs="+")
    ap.add_argument("--top", type=int, default=10, help="highest 24h volume perps (when --symbols is not given)")
    ap.add_argument("--once", action="store_true", help="one snapshot, then exit")
    a = ap.parse_args()
    C.apply_script_defaults()
    syms = [s.upper().removesuffix(".P") for s in a.symbols] if a.symbols else top_symbols(a.top)
    log("Symbols: " + " ".join(syms))
    bot = Bot(syms)
    bot.load()
    snaps = bot.compute()
    if a.once:
        print(report(snaps).encode("ascii", "replace").decode())
        return
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        for st in bot.stores.values():
            st.save()
        log("stopped")


if __name__ == "__main__":
    main()
