#!/usr/bin/env python3
"""FIB / FVG / OB score of LVN zones on 1H/5m, same rules as LVN_Confluence_1H5m.pine.

Fixed before running:
- Signal: first touch of a FRESH bias-aligned zone. Sets: 5m A+ and 1H. 4H context blocks both.
- Entry: a 5m close back outside the zone within 6 bars including the touch bar, then the next 5m open.
  A 5m close beyond the far edge first cancels the trade.
- Stop: far edge plus 1.0 x ATR(1H). Target 2R. Costs 0.05% per side.
- Question: does Avg R rise with the score, and is score >= 1 (script default) or >= 2 above 0?
- Pass: Avg R > 0 and the low end of its 95% range > 0.

    python backtest_confluence.py
"""
import argparse

import backtest as bt
from backtest import add_indicators, load_1m, ms, resample, run_symbol, summarize
from backtest_filters import confirm_bar, trade

SETS = ("5m A+", "1H")
DATA = (("BTCUSDT", "2025-10-01", "2026-10-31"), ("ETHUSDT", "2025-10-01", "2026-10-31"),
        ("SOLUSDT", "2025-10-01", "2026-10-19"), ("XRPUSDT", "2025-10-01", "2026-10-19"))
START, END = "2025-10-19", "2026-10-19"
HEAD = "| Set | Filter | Trades | Win % | Avg R | 95% range | Total R | Max DD (R) |\n|---|---|---:|---:|---:|---:|---:|---:|"


def row(group, name, rows):
    s = summarize(rows)
    if not s:
        return f"| {group} | {name} | 0 | | | | | |"
    return f"| {group} | {name} | {s['n']} | {s['win']:.1f} | {s['avg']:+.3f} | {s['lo']:+.3f} to {s['hi']:+.3f} | {s['total']:+.1f} | {s['dd']:.1f} |"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cache", default="cache")
    ap.add_argument("--out", default="backtest_confluence_report.md")
    ap.add_argument("--chart", type=int, default=5, help="chart TF in minutes")
    ap.add_argument("--htf", type=int, default=60, help="HTF in minutes")
    ap.add_argument("--ctx", type=int, default=240, help="context TF in minutes")
    ap.add_argument("--sets", nargs="+", default=list(SETS), help="trade groups as named in backtest.py")
    ap.add_argument("--start", default=START)
    ap.add_argument("--end", default=END)
    ap.add_argument("--symbols", nargs="+", default=[d[0] for d in DATA])
    args = ap.parse_args()
    args.fee, args.slip, args.rr, args.atr_mult = 0.0005, 0.0, 2.0, 0.5
    bt.CHART, bt.HTF, bt.CTX = args.chart * bt.MIN, args.htf * bt.MIN, args.ctx * bt.MIN
    out = []
    for sym, data_start, data_end in [d for d in DATA if d[0] in args.symbols]:
        m = load_1m(sym, ms(data_start), ms(data_end), args.cache)
        bc = add_indicators(resample(m, bt.CHART))
        trades, stats = run_symbol(sym, m, args)
        sigs = [t for t in trades if t["aligned"] and not t["blocked"] and t["group"] in args.sets and ms(args.start) <= t["entry_time"] < ms(args.end)]
        print(sym, len(sigs), "signals", stats, flush=True)
        for sig in sigs:
            q = confirm_bar(sig, bc)
            if q is None:
                continue
            r = trade(sig, q, "2R", m, bc, 0.0005)
            if r:
                r.update(symbol=sym, group=sig["group"], fib=sig["fib"], fvg=sig["fvg"], ob=sig["ob"], score=sig["fib"] + sig["fvg"] + sig["ob"])
                out.append(r)
    o = [f"# LVN confluence score, {args.chart}m/{args.htf}m/{args.ctx}m, {args.start} to {args.end}: " + ", ".join(args.symbols), "", HEAD]
    for g in args.sets:
        rows = [r for r in out if r["group"] == g]
        o.append(row(g, "all", rows))
        for n in range(4):
            o.append(row(g, f"score = {n}", [r for r in rows if r["score"] == n]))
        for n in (1, 2):
            o.append(row(g, f"score >= {n}", [r for r in rows if r["score"] >= n]))
        for k in ("fib", "fvg", "ob"):
            o.append(row(g, f"{k} yes", [r for r in rows if r[k]]))
            o.append(row(g, f"{k} no", [r for r in rows if not r[k]]))
        for sym in args.symbols:
            o.append(row(g, f"score >= 1, {sym}", [r for r in rows if r["score"] >= 1 and r["symbol"] == sym]))
    text = "\n".join(o) + "\n"
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
