#!/usr/bin/env python3
"""Pre-entry filters on the 1H/5m scalp zones. All values fixed before the first run, nothing tuned on the result.

Base: FRESH zone in the direction of a STRONG 1H trend, limit 0.25 x 5m ATR before the near edge (script default),
stop 0.5 x ATR beyond the far edge, target 2R, costs 0.05% per side.
Depth: LVN / HVN volume <= 0.50. 4H: 4H ATR-swing trend on the same side.
Room: no live opposite 1H or 4H zone between entry and target. Stop: stop distance >= 0.30%.
Slow: average volume of the 6 candles before the touch < the 100-candle median.

    python backtest_scalp_filters.py
"""
import multiprocessing as mp
import types

import numpy as np

import backtest as bt
from backtest import MIN, add_indicators, load_1m, ms, resample, run_symbol
from backtest_scalp_1h5m import DATA, END, HEAD, START, row, strength

FILTERS = (("Depth", lambda t: t["ratio"] <= 0.50), ("4H", lambda t: t["t4"] == t["d"]), ("Room", lambda t: t["clear"]),
           ("Stop", lambda t: t["risk_pct"] >= 0.30), ("Slow", lambda t: t["approach"] < 1.0))


def job(d):
    sym, a, z = d
    bt.CHART, bt.HTF, bt.CTX = 5 * MIN, 60 * MIN, 240 * MIN
    bt.REQ_BOS, bt.MIN_EFF, bt.MAX_BARS, bt.MAX_BARS_HTF, bt.PB_ATR, bt.VOL_MEDIAN, bt.ENTRY_BUF = False, 0.15, 30, 16, 2.0, 100, 0.25
    m = load_1m(sym, ms(a), ms(z), "cache")
    trades, _ = run_symbol(sym, m, types.SimpleNamespace(fee=0.0005, slip=0.0, rr=2.0, atr_mult=0.5))
    b1, b4 = add_indicators(resample(m, 60 * MIN)), add_indicators(resample(m, 240 * MIN))
    tr1, st1 = strength(b1)
    tr4, _ = strength(b4)
    out = []
    for t in trades:
        i = int(np.searchsorted(b1["tc"], t["entry_time"], side="right")) - 1
        k = int(np.searchsorted(b4["tc"], t["entry_time"], side="right")) - 1
        if ms(START) <= t["entry_time"] < ms(END) and i >= 0 and k >= 0 and tr1[i] == t["d"] and st1[i]:
            t["t4"] = int(tr4[k])
            out.append({x: t[x] for x in ("symbol", "group", "d", "entry_time", "exit_time", "net_r", "risk_pct", "ratio", "clear", "approach", "t4")})
    print(sym, len(out), flush=True)
    return out


def main():
    with mp.Pool(4) as p:
        rows = [t for x in p.map(job, DATA, chunksize=1) for t in x]
    o = [f"# 1H/5m pre-entry filters, STRONG 1H, {START} to {END}", "", HEAD]
    for name, f in (("5m", lambda t: t["group"] != "1H"), ("1H", lambda t: t["group"] == "1H")):
        base = [t for t in rows if f(t)]
        o.append(row(f"{name} all", base))
        for fn, g in FILTERS:
            o.append(row(f"{name} {fn} yes", [t for t in base if g(t)]))
            o.append(row(f"{name} {fn} no", [t for t in base if not g(t)]))
        o.append(row(f"{name} all 5 filters", [t for t in base if all(g(t) for _, g in FILTERS)]))
    text = "\n".join(o) + "\n"
    with open("backtest_scalp_filters_report.md", "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
