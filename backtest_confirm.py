#!/usr/bin/env python3
"""Entry and stop variants for the Nested LVN setup, chosen on train and checked once on test.

Fixed before running:
- Signal: first touch of a FRESH bias-aligned zone, classified at the touch (backtest.py).
- Entry "touch": limit at the near edge.
- Entry "confirm": a 5m close back outside the zone on the trade side, within 6 bars including the
  touch bar, then market at the next 5m open. A 5m close beyond the far edge first cancels the trade.
- Stop: far edge plus 0.5 x ATR(5m), 0.5 x ATR(1H) or 1.0 x ATR(1H). Target 2R, same costs.
- Pick per set: highest train Avg R with at least 30 train trades. Test shows the pick only.
- Pass: test Avg R > 0 and the low end of its 95% range > 0.

    python backtest_confirm.py --symbols BTCUSDT.P ETHUSDT.P
"""
import argparse

import numpy as np

from backtest import CHART, add_indicators, load_1m, ms, resample, run_symbol, simulate_exit, summarize

WINDOW = 6
MIN_TRAIN = 30
ENTRIES = ("touch", "confirm")
STOPS = (("0.5 ATR 5m", "atr5", 0.5), ("0.5 ATR 1H", "atr1h", 0.5), ("1.0 ATR 1H", "atr1h", 1.0))
SETS = ("5m A+", "5m non-nested", "1H")


def evaluate(sig, m, bc, entry_mode, stop, cost, rr):
    d, top, bot = sig["d"], sig["top"], sig["bot"]
    _, src, mult = stop
    if entry_mode == "touch":
        k = sig["k"]
        level = top if d == 1 else bot
        entry = min(level, m["o"][k]) if d == 1 else max(level, m["o"][k])
        atr5 = sig["atr5"]
    else:
        j, n = sig["j"], len(bc["t"])
        fill = None
        for q in range(j, min(j + WINDOW, n - 1)):
            cl = bc["cL"][q]
            if (cl < bot) if d == 1 else (cl > top):
                return None
            if (cl > top) if d == 1 else (cl < bot):
                fill = q + 1
                break
        if fill is None:
            return None
        k = int(np.searchsorted(m["t"], bc["t"][fill]))
        entry = m["o"][k]
        atr5 = bc["atr"][fill - 1]
    atr = atr5 if src == "atr5" else sig["atr1h"]
    if atr is None or atr != atr:
        return None
    sl = bot - mult * atr if d == 1 else top + mult * atr
    risk = (entry - sl) * d
    if risk <= 0:
        return None
    ex = simulate_exit(m, k, d, entry, sl, entry + d * rr * risk)
    if ex is None:
        return None
    xi, px, _ = ex
    net = (px - entry) * d / risk - (entry + px) * cost / risk
    return dict(entry_time=int(m["t"][k]), exit_time=int(m["t"][xi]), net_r=net, risk_pct=risk / entry * 100)


HEAD = "| Set | Entry | Stop | Trades | Win % | Avg R | 95% range | Total R | Max DD (R) | Median stop % |\n|---|---|---|---:|---:|---:|---:|---:|---:|---:|"


def row(group, entry, stop, s):
    if not s:
        return f"| {group} | {entry} | {stop} | 0 | | | | | | |"
    return (f"| {group} | {entry} | {stop} | {s['n']} | {s['win']:.1f} | {s['avg']:+.3f} | {s['lo']:+.3f} to {s['hi']:+.3f} | "
            f"{s['total']:+.1f} | {s['dd']:.1f} | {s['risk']:.2f} |")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--symbols", nargs="+", default=["BTCUSDT", "ETHUSDT"])
    ap.add_argument("--data-start", default="2025-10-01")
    ap.add_argument("--trade-start", default="2025-10-19")
    ap.add_argument("--split", default="2026-04-19")
    ap.add_argument("--test-end", default="2026-10-19")
    ap.add_argument("--data-end", default="2026-10-31")
    ap.add_argument("--rr", type=float, default=2.0)
    ap.add_argument("--atr-mult", type=float, default=0.5)
    ap.add_argument("--fee", type=float, default=0.0004)
    ap.add_argument("--slip", type=float, default=0.0001)
    ap.add_argument("--cache", default="cache")
    ap.add_argument("--out", default="backtest_confirm_report.md")
    args = ap.parse_args()
    args.symbols = [s.upper().removesuffix(".P") for s in args.symbols]
    cost = args.fee + args.slip
    start, split, end = ms(args.trade_start), ms(args.split), ms(args.test_end)

    results = {}
    for sym in args.symbols:
        m = load_1m(sym, ms(args.data_start), ms(args.data_end), args.cache)
        bc = add_indicators(resample(m, CHART))
        trades, _ = run_symbol(sym, m, args)
        sigs = [t for t in trades if t["aligned"] and t["group"] in SETS and start <= t["entry_time"] < end]
        print(f"{sym}: {len(sigs)} signals", flush=True)
        for sig in sigs:
            for e in ENTRIES:
                for st in STOPS:
                    r = evaluate(sig, m, bc, e, st, cost, args.rr)
                    if r and r["entry_time"] < end:
                        r["symbol"] = sym
                        results.setdefault((sig["group"], e, st[0]), []).append(r)

    train = lambda rows: [r for r in rows if r["entry_time"] < split]
    test = lambda rows: [r for r in rows if r["entry_time"] >= split]
    o = ["# Entry and stop variants: " + ", ".join(args.symbols), "", "## Train: all variants", "", HEAD]
    picks = {}
    for g in SETS:
        best = None
        for e in ENTRIES:
            for st in STOPS:
                s = summarize(train(results.get((g, e, st[0]), [])))
                o.append(row(g, e, st[0], s))
                if s and s["n"] >= MIN_TRAIN and (best is None or s["avg"] > best[0]):
                    best = (s["avg"], e, st[0])
        picks[g] = best
    o += ["", "## Test: train pick only", "", HEAD]
    verdicts = []
    for g in SETS:
        if not picks[g]:
            o.append(f"| {g} | no variant with {MIN_TRAIN} train trades | | | | | | | | |")
            verdicts.append(f"- {g}: no pick")
            continue
        _, e, st = picks[g]
        rows = test(results[(g, e, st)])
        s = summarize(rows)
        o.append(row(g, e, st, s))
        ok = bool(s) and s["avg"] > 0 and s["lo"] > 0
        verdicts.append(f"- {g}: {'PASS' if ok else 'FAIL'}")
        for sym in args.symbols:
            o.append(row(f"{g} {sym}", e, st, summarize([r for r in rows if r["symbol"] == sym])))
    o += ["", "## Pass check", ""] + verdicts
    text = "\n".join(o) + "\n"
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
