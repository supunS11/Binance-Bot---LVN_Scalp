#!/usr/bin/env python3
"""Old vs new impulse leg rules on the 4H/15m LVN zones.

Old: max candles 10, 30% pullback ends a leg, volume against the 20-bar average.
New: max candles 30 on 15m and 16 on 4H, pullback must also be >= 2 x ATR, volume against the 100-bar median.
New + slow: also no BOS requirement and min efficiency 0.15, the values the blue LINK leg needs.
Trade as in backtest.py: first touch of a FRESH bias-aligned zone, limit at the near edge, stop 0.5 x ATR beyond the
far edge, target 2R, costs 0.05% per side. Nothing was tuned on the result.

    python backtest_leg_rules.py
    python backtest_leg_rules.py --legs LINKUSDT 2026-10-20 2026-11-02
"""
import argparse
import types

import backtest as bt
from backtest import MIN, add_indicators, load_1m, ms, resample, run_symbol, stamp, summarize

DATA = (("BTCUSDT", "2025-10-01", "2026-10-31"), ("ETHUSDT", "2025-10-01", "2026-10-31"),
        ("SOLUSDT", "2025-10-01", "2026-10-19"), ("XRPUSDT", "2025-10-01", "2026-10-19"))
START, END = "2025-10-19", "2026-10-19"
SETS = (("15m nested", ("5m A+", "5m nested (not A+)")), ("15m non-nested", ("5m non-nested",)), ("4H", ("1H",)))
HEAD = "| Rules | Set | Trades | Win % | Avg R | 95% range | Total R | Median stop % |\n|---|---|---:|---:|---:|---:|---:|---:|"


def use(new, slow=False):
    bt.REQ_BOS = not slow
    bt.MIN_EFF = 0.15 if slow else 0.30
    bt.CHART, bt.HTF, bt.CTX = 15 * MIN, 240 * MIN, 1440 * MIN
    bt.MAX_BARS = 30 if new else 10
    bt.MAX_BARS_HTF = 16 if new else None
    bt.PB_ATR = 2.0 if new else 0.0
    bt.VOL_MEDIAN = 100 if new else 0


def legs(sym, a, z, cache):
    m = load_1m(sym, ms(a), ms(z), cache)
    for new, slow in ((False, False), (True, True)):
        use(new, slow)
        b = add_indicators(resample(m, bt.CHART))
        e = bt.Engine(b, bt.MIN_VOL_CHART)
        print("NEW" if new else "OLD")
        for _ in range(len(b["t"])):
            for g in e.feed():
                print(f"  {'UP' if g['dir'] == 1 else 'DN'} {stamp(g['t0'])} -> {stamp(g['t1'])} {g['lo']}-{g['hi']} LVNs {[(round(x, 3), round(y, 3)) for x, y in bt.find_lvns(m, g)]}")


def row(name, g, rows):
    s = summarize(rows)
    if not s:
        return f"| {name} | {g} | 0 | | | | | |"
    return f"| {name} | {g} | {s['n']} | {s['win']:.1f} | {s['avg']:+.3f} | {s['lo']:+.3f} to {s['hi']:+.3f} | {s['total']:+.1f} | {s['risk']:.2f} |"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cache", default="cache")
    ap.add_argument("--out", default="backtest_leg_rules_report.md")
    ap.add_argument("--legs", nargs=3)
    args = ap.parse_args()
    if args.legs:
        legs(*args.legs, args.cache)
        return
    run_args = types.SimpleNamespace(fee=0.0005, slip=0.0, rr=2.0, atr_mult=0.5)
    o = [f"# Impulse leg rules, 4H/15m, {START} to {END}: " + ", ".join(d[0] for d in DATA), "", HEAD]
    counts = []
    for new, slow, name in ((False, False, "Old"), (True, False, "New"), (True, True, "New + slow")):
        use(new, slow)
        rows = []
        for sym, a, z in DATA:
            m = load_1m(sym, ms(a), ms(z), args.cache)
            tr, st = run_symbol(sym, m, run_args)
            rows += [t for t in tr if t["aligned"] and ms(START) <= t["entry_time"] < ms(END)]
            counts.append(f"- {name} {sym}: {st}")
            print(name, sym, len(rows), flush=True)
        for g, members in SETS:
            o.append(row(name, g, [t for t in rows if t["group"] in members]))
    o += ["", "## Counts", ""] + counts
    text = "\n".join(o) + "\n"
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
