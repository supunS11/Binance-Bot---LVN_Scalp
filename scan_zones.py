#!/usr/bin/env python3
"""Which Binance USDT perps have a FRESH 1H/5m LVN zone with a STRONG 1H trend right now?

Python port of Scalp_LVN_1H5m.pine with its default settings, on closed 5m candles and the last 15 days of 1m data.
5m zones must also have a stop >= 0.30% and a 4H trend on the same side. LVNs must be deep (<= 0.50) and fast (time at price <= 0.50).
Lists zones in the trend direction that price has not passed, nearest first. Reads public Binance data only.

    python scan_zones.py
    python scan_zones.py --top 50
    python scan_zones.py --symbols ETHUSDT LINKUSDT
    python scan_zones.py --micro   # Scalp_LVN_15m1m.pine: 1m zones, 15m trend + legs, 1H filter, no min stop
"""
import argparse
import datetime as dt
import os
import time
import types

import numpy as np

import backtest as bt
from backtest import MIN, add_indicators, get_json, resample
from backtest_scalp_1h5m import strength

API = "https://fapi.binance.com/fapi/v1/"
DAYS = 15
KEYS = ("t", "o", "h", "l", "c", "v", "tb")


def top_symbols(n):
    info = get_json(API + "exchangeInfo")["symbols"]
    ok = {s["symbol"] for s in info if s["contractType"] == "PERPETUAL" and s["status"] == "TRADING" and s["quoteAsset"] == "USDT" and s["symbol"].isascii()}
    rows = [r for r in get_json(API + "ticker/24hr") if r["symbol"] in ok]
    rows.sort(key=lambda r: float(r["quoteVolume"]), reverse=True)
    return [r["symbol"] for r in rows[:n]]


def load_recent(sym, cache):
    """Last DAYS of 1m candles. Only candles after the cached ones are downloaded."""
    os.makedirs(cache, exist_ok=True)
    path = os.path.join(cache, sym + ".npz")
    now = int(time.time() * 1000) // MIN * MIN
    start = now - DAYS * 1440 * MIN
    old = None
    if os.path.exists(path):
        d = np.load(path)
        if int(d["t"][-1]) >= start:
            old = {k: d[k] for k in KEYS}
    cur = int(old["t"][-1]) + MIN if old else start
    rows = []
    while cur < now:
        chunk = get_json(f"{API}klines?symbol={sym}&interval=1m&startTime={cur}&endTime={now - 1}&limit=1500")
        if not chunk:
            break
        rows += [(r[0], float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[5]), float(r[9])) for r in chunk]
        cur = chunk[-1][0] + MIN
    if rows:
        a = np.array(rows)
        new = dict(t=a[:, 0].astype(np.int64), o=a[:, 1], h=a[:, 2], l=a[:, 3], c=a[:, 4], v=a[:, 5], tb=a[:, 6])
        old = {k: np.r_[old[k], new[k]] for k in KEYS} if old else new
    keep = old["t"] >= start
    m = {k: old[k][keep] for k in KEYS}
    np.savez(path, **m)
    return m


def scan(sym, cache, micro=False):
    m = load_recent(sym, cache)
    if len(m["t"]) < 7 * 1440:
        return None, "too little data"
    args = types.SimpleNamespace(fee=0.0005, slip=0.0, rr=2.0, atr_mult=0.5)
    _, st = bt.run_symbol(sym, m, args)
    trend, strong = strength(add_indicators(resample(m, bt.HTF)))
    d, is_strong = int(trend[-1]), bool(strong[-1])
    t4 = int(strength(add_indicators(resample(m, bt.CTX)))[0][-1])
    min_stop = 0.0 if micro else 0.30
    px, atr = st["close"], st["atr"]
    out = []
    if is_strong:
        for z in st["live"]:
            if z["tier"] == 2 or z["dir"] != d or z["status"] != 0:
                continue
            near = z["top"] if d == 1 else z["bot"]
            if not z["tier"] and (t4 != d or (z["top"] - z["bot"] + 0.5 * atr) / near * 100 < min_stop):
                continue
            gap = px - z["top"] if d == 1 else z["bot"] - px
            if gap > 0:
                f = 5 if micro else 1  # 1m chart: time windows / 5
                age = (int(m["t"][-1]) + MIN - z["made"]) / 60000  # minutes since the zone was made
                w = 30 // f
                ext = m["h"][-w:].max() if d == 1 else m["l"][-w:].min()
                appr = ((ext - near) if d == 1 else (near - ext)) / atr
                ready = z["tier"] or age >= 120 / f
                slow = not z["tier"] and appr <= 2.0
                tf = ("15m" if z["tier"] else "1m") if micro else ("1H" if z["tier"] else "5m")
                out.append(dict(sym=sym, side="LONG" if d == 1 else "SHORT", tf=tf, nested=z["nested"],
                                bot=z["bot"], top=z["top"], px=px, pct=gap / px * 100, atrs=gap / atr,
                                base=z.get("gap"), age=age, ready=ready, appr=appr, slow=slow))
    return out, "STRONG" if is_strong else "weak"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--top", type=int, default=30, help="highest 24h volume perps")
    ap.add_argument("--skip", type=int, default=0, help="leave out this many of the highest volume perps")
    ap.add_argument("--symbols", nargs="+")
    ap.add_argument("--near", type=float, default=2.0, help="only zones within this % of price")
    ap.add_argument("--cache", default="scan_cache")
    ap.add_argument("--out", default="scan_results.md")
    ap.add_argument("--micro", action="store_true", help="15m/1m script instead of 1H/5m")
    args = ap.parse_args()
    bt.CHART, bt.HTF, bt.CTX = 5 * MIN, 60 * MIN, 240 * MIN
    bt.REQ_BOS, bt.MIN_EFF, bt.MAX_BARS, bt.MAX_BARS_HTF, bt.PB_ATR, bt.VOL_MEDIAN, bt.ZONE_PAD = False, 0.15, 30, 16, 2.0, 100, 0.25
    bt.MAX_RATIO, bt.MAX_TIME, bt.MAX_GAP = 0.50, 0.50, 3.0
    if args.micro:
        bt.CHART, bt.HTF, bt.CTX = MIN, 15 * MIN, 60 * MIN

    symbols = [s.upper().removesuffix(".P") for s in args.symbols] if args.symbols else top_symbols(args.top + args.skip)[args.skip:]
    rows, counts = [], {"STRONG": 0, "weak": 0, "too little data": 0}
    for i, s in enumerate(symbols, 1):
        z, state = scan(s, args.cache, args.micro)
        counts[state] += 1
        rows += z or []
        print(f"{i}/{len(symbols)} {s}: {state}, {len(z or [])} zones", flush=True)

    rows = [r for r in rows if r["pct"] <= args.near]
    rows.sort(key=lambda r: r["pct"])
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    o = [f"# Zone scan {now}", "",
         f"{len(symbols)} symbols: {counts['STRONG']} STRONG {'15m' if args.micro else '1H'} trend, {counts['weak']} weak (no zones listed), {counts['too little data']} too little data. FRESH zones within {args.near}% of price.", "",
         "Base = gap from the LVN far edge to its leg base S/D (x ATR, LVNs > 3 are not listed). Ready = zone old enough (5m: 2 h, 1m: 24 min). "
         "Approach = how far price travelled toward the zone in the last 30 min (1m: 6 min), x ATR; SLOW = 2 or less; shown only when price is within 1 ATR of the zone (far = not yet).", "",
         "| Symbol | Side | Zone | Nested | Zone range | Price | Distance % | Distance x " + ("1m" if args.micro else "5m") + " ATR | Base (ATR) | Age | Ready | Approach |",
         "|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|"]
    for r in rows:
        o.append(f"| {r['sym']} | {r['side']} | {r['tf']} | {'yes' if r['nested'] else ''} | {r['bot']:.6g} – {r['top']:.6g} | {r['px']:.6g} | {r['pct']:.2f} | {r['atrs']:.1f} | {'' if r['base'] is None else round(r['base'], 1)} | {r['age'] / 60:.1f} h | {'yes' if r['ready'] else 'WAIT'} | {(str(round(r['appr'], 1)) + (' SLOW' if r['slow'] else '')) if r['atrs'] <= 1 else 'far'} |")
    text = "\n".join(o) + "\n"
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(text)
    print(text.encode("ascii", "replace").decode())


if __name__ == "__main__":
    main()
