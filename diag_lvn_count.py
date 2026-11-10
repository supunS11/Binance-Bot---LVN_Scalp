#!/usr/bin/env python3
"""Why does the 4H/15m script show so few 15m LVNs? Counts where 15m legs and their LVNs drop out (script defaults).

    python diag_lvn_count.py BTCUSDT ETHUSDT SOLUSDT
"""
import sys
import types
from collections import Counter

import backtest as bt
from backtest import MIN, Engine, add_indicators, find_lvns, resample, run_symbol
from scan_zones import load_recent

CHECKS = ("bars", "size", "eff", "vol", "dir")


class Diag(Engine):
    """Engine that records every candidate leg and the checks it fails."""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.log = []

    def validate(self, d, s, e, lo, hi):
        b = self.b
        bars = e - s + 1
        if s < 1 or bars < 1:
            return None
        o, c, h, l, v = b["oL"], b["cL"], b["hL"], b["lL"], b["vL"]
        atr, va = b["atrL"][s - 1], b["vaL"][s - 1]
        if not (atr > 0 and va > 0):
            return None
        path = sum(h[k] - l[k] for k in range(s, e + 1))
        ndir = sum(1 for k in range(s, e + 1) if d * (c[k] - o[k]) > 0)
        nden = bars - (d * (c[s] - o[s]) <= 0) - (d * (c[e] - o[e]) <= 0)
        fails = []
        if bars < bt.MIN_BARS or bars > self.max_bars:
            fails.append("bars")
        if (hi - lo) / atr < bt.MIN_ATR:
            fails.append("size")
        if path <= 0 or d * (c[e] - o[s]) / path < bt.MIN_EFF:
            fails.append("eff")
        if sum(v[s:e + 1]) / bars / va < self.min_vol:
            fails.append("vol")
        if ndir / max(nden, 1) < bt.MIN_DIR:
            fails.append("dir")
        leg = super().validate(d, s, e, lo, hi)
        self.log.append(dict(fails=fails, size=(hi - lo) / atr, leg=leg))
        return leg


def main():
    syms = sys.argv[1:] or ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    bt.CHART, bt.HTF, bt.CTX = 15 * MIN, 240 * MIN, 1440 * MIN
    bt.REQ_BOS, bt.MIN_EFF, bt.MAX_BARS, bt.MAX_BARS_HTF, bt.PB_ATR, bt.VOL_MEDIAN = False, 0.15, 30, 16, 2.0, 100
    bt.WEAK_N, bt.FILL_N, bt.BROKE_N, bt.RANGE_N = 3, 6, 2, 30
    for sym in syms:
        m = load_recent(sym, "scan_cache")
        b = add_indicators(resample(m, bt.CHART))
        eng = Diag(b, bt.MIN_VOL_CHART)
        for _ in range(len(b["t"])):
            eng.feed()
        days = (m["t"][-1] - m["t"][0]) / 86400000
        log = [x for x in eng.log if x["size"] >= 2.0]
        alone = Counter(x["fails"][0] for x in log if len(x["fails"]) == 1)
        anyf = Counter(f for x in log for f in x["fails"])
        passed = [x["leg"] for x in eng.log if x["leg"]]
        nlvn = [len(find_lvns(m, g)) for g in passed]
        nolvn = sum(1 for n in nlvn if n == 0)
        # same legs, LVN rule without the HVN/ratio limit -> how many valleys the ratio rule removes
        keep = bt.MAX_RATIO
        bt.MAX_RATIO = 1.0
        nlvn_any = [len(find_lvns(m, g)) for g in passed]
        bt.MAX_RATIO = keep
        _, st = run_symbol(sym, m, types.SimpleNamespace(fee=0.0005, slip=0.0, rr=2.0, atr_mult=0.5))
        live = [z for z in st["live"] if z["tier"] == 0]
        hb = Engine(add_indicators(resample(m, bt.HTF)), bt.MIN_VOL_HTF, bt.MAX_BARS_HTF)
        for _ in range(len(hb.b["t"])):
            hb.feed()
        bias = hb.bias()
        shown = [z for z in live if bias == 0 or z["dir"] == bias]
        print(f"\n## {sym}, {days:.0f} days of 15m")
        print(f"- candidate 15m legs >= 2 ATR: {len(log)}, passed all checks: {len(passed)}")
        print(f"- failed checks (any): " + ", ".join(f"{k} {anyf[k]}" for k in CHECKS))
        print(f"- failed only this check: " + ", ".join(f"{k} {alone[k]}" for k in CHECKS))
        print(f"- passed legs with no LVN: {nolvn} of {len(passed)}; LVNs made: {sum(nlvn)} (with no ratio limit: {sum(nlvn_any)})")
        print(f"- 15m zones made: {st['zones_5m']}, already touched when made: {st['pretouched']}")
        print(f"- still alive at the end: {len(live)} (fresh {sum(z['status'] == 0 for z in live)}), 4H bias {bias}, shown with bias filter: {len(shown)}")


if __name__ == "__main__":
    main()
