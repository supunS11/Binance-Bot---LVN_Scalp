#!/usr/bin/env python3
"""1H/5m zones widened on the entry side by N x 5m ATR. Trades as in backtest_scalp_1h5m.py, STRONG 1H trend only.

Limit at the widened edge, stop unchanged beyond the far edge, target 2R of the wider risk, one trade per zone.

    python backtest_scalp_pad.py
"""
import multiprocessing as mp

import backtest as bt
from backtest import summarize
from backtest_scalp_1h5m import DATA, job, row, HEAD, START, END

PADS = (0.0, 0.10, 0.25, 0.50)


def run(task):
    pad, d = task
    bt.ENTRY_BUF = pad
    return pad, job(d)


def main():
    with mp.Pool(4) as p:
        done = p.map(run, [(x, d) for x in PADS for d in DATA], chunksize=1)
    nested = ("5m A+", "5m nested (not A+)")
    sets = (("5m nested", lambda t: t["group"] in nested), ("5m non-nested", lambda t: t["group"] == "5m non-nested"), ("1H", lambda t: t["group"] == "1H"))
    o = [f"# 1H/5m zones widened on the entry side, STRONG 1H, {START} to {END}", "", HEAD]
    for name, f in sets:
        for x in PADS:
            o.append(row(f"{name}, pad {x}", [t for y, ts in done if y == x for t in ts if t["strong"] and f(t)]))
    text = "\n".join(o) + "\n"
    with open("backtest_scalp_pad_report.md", "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
