#!/usr/bin/env python3
"""Limit entry before the zone edge: does it pay for the near misses?

Current 4H/15m defaults. Limit order N x 15m ATR before the near edge of a FRESH bias-aligned zone, one trade per zone.
Stop stays 0.5 x ATR beyond the far edge, target 2R of the wider risk, costs 0.05% per side.
Near miss = filled, then closed before price ever reached the real edge. Nothing was tuned on the result.

    python backtest_near_miss.py
"""
import multiprocessing as mp
import types

import backtest as bt
from backtest import load_1m, ms, run_symbol, summarize
from backtest_leg_rules import DATA, END, SETS, START, use

BUFFERS = (0.0, 0.10, 0.25, 0.50)
SPLIT = "2026-04-19"
HEAD = "| Set | Buffer x ATR | Trades | Near miss % | Win % | Avg R | 95% range | First half R | Second half R | Median stop % |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"


def job(task):
    buf, (sym, a, z) = task
    use(True, True)
    bt.ENTRY_BUF = buf
    args = types.SimpleNamespace(fee=0.0005, slip=0.0, rr=2.0, atr_mult=0.5)
    trades, _ = run_symbol(sym, load_1m(sym, ms(a), ms(z), "cache"), args)
    keep = [t for t in trades if t["aligned"] and ms(START) <= t["entry_time"] < ms(END)]
    print(buf, sym, len(keep), flush=True)
    return buf, keep


def avg(rows):
    s = summarize(rows, boot=1)
    return f"{s['avg']:+.3f} ({s['n']})" if s else "-"


def row(name, buf, rows):
    s = summarize(rows)
    if not s:
        return f"| {name} | {buf} | 0 | | | | | | | |"
    near = sum(not t["reached"] for t in rows) / len(rows) * 100
    a = [t for t in rows if t["entry_time"] < ms(SPLIT)]
    b = [t for t in rows if t["entry_time"] >= ms(SPLIT)]
    return f"| {name} | {buf} | {s['n']} | {near:.1f} | {s['win']:.1f} | {s['avg']:+.3f} | {s['lo']:+.3f} to {s['hi']:+.3f} | {avg(a)} | {avg(b)} | {s['risk']:.2f} |"


def main():
    with mp.Pool(4) as p:
        done = p.map(job, [(b, d) for b in BUFFERS for d in DATA], chunksize=1)
    o = [f"# Entry before the zone edge, 4H/15m, {START} to {END}: " + ", ".join(d[0] for d in DATA), "", HEAD]
    for g, members in SETS:
        for b in BUFFERS:
            rows = [t for x, keep in done if x == b for t in keep if t["group"] in members]
            o.append(row(g, b, rows))
    text = "\n".join(o) + "\n"
    with open("backtest_near_miss_report.md", "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
