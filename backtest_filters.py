#!/usr/bin/env python3
"""Confirmation filters for LVN zone entries, picked on one data set and checked once on another.

Fixed before running:
- Signal: first touch of a FRESH bias-aligned zone. Sets: all 5m zones, and 1H zones.
- Base entry: a 5m close back outside the zone on the trade side within 6 bars including the touch bar,
  then market at the next 5m open. A 5m close beyond the far edge first cancels the trade.
- Stop: far edge plus 1.0 x ATR(1H). Costs 0.05% per side.
- Filters on the confirming bar q (touch bar j), for a long; a short is the mirror:
  delta: (taker buy - taker sell) / volume >= 0.10
  volume: volume >= 1.5 x 20-bar average
  sweep: a low in j..q takes out the lowest low of the 24 bars before j
  structure: close above the highest high of the 5 bars before q
  approach: mean range of the 6 bars before j <= ATR(5m) before them
  session: entry between 07:00 and 21:00 UTC
  delta+volume: both
- Target: 2R, or the leg's extreme with at least 1R of room (otherwise no trade).
- Pick per set on the pick data: highest Avg R with at least 100 trades.
- Check data shows the pick only. Pass: Avg R > 0 and the low end of its 95% range > 0.

    python backtest_filters.py
"""
import argparse
import datetime as dt

import numpy as np

from backtest import CHART, add_indicators, load_1m, ms, resample, run_symbol, simulate_exit, summarize

WINDOW = 6
STOP_ATR = 1.0
MIN_TRADES = 100
SETS = ("5m", "1H")
FILTERS = ("base", "delta", "volume", "sweep", "structure", "approach", "session", "delta+volume")
TARGETS = ("2R", "leg extreme")


def confirm_bar(sig, bc):
    d, top, bot, j = sig["d"], sig["top"], sig["bot"], sig["j"]
    for q in range(j, min(j + WINDOW, len(bc["t"]) - 1)):
        cl = bc["cL"][q]
        if (cl < bot) if d == 1 else (cl > top):
            return None
        if (cl > top) if d == 1 else (cl < bot):
            return q
    return None


def passes(name, sig, q, bc):
    d, j = sig["d"], sig["j"]
    h, l, v = bc["hL"], bc["lL"], bc["vL"]
    if name == "base":
        return True
    if name == "delta":
        return v[q] > 0 and d * (2 * bc["tbL"][q] - v[q]) / v[q] >= 0.10
    if name == "volume":
        return bc["vaL"][q - 1] > 0 and v[q] >= 1.5 * bc["vaL"][q - 1]
    if name == "delta+volume":
        return passes("delta", sig, q, bc) and passes("volume", sig, q, bc)
    if name == "sweep":
        if j < 24:
            return False
        if d == 1:
            return min(l[j:q + 1]) < min(l[j - 24:j])
        return max(h[j:q + 1]) > max(h[j - 24:j])
    if name == "structure":
        if q < 5:
            return False
        return bc["cL"][q] > max(h[q - 5:q]) if d == 1 else bc["cL"][q] < min(l[q - 5:q])
    if name == "approach":
        if j < 7:
            return False
        return np.mean([h[k] - l[k] for k in range(j - 6, j)]) <= bc["atrL"][j - 7]
    if name == "session":
        hour = dt.datetime.fromtimestamp(int(bc["t"][q + 1]) / 1000, dt.timezone.utc).hour
        return 7 <= hour < 21
    raise ValueError(name)


def trade(sig, q, target, m, bc, cost):
    d = sig["d"]
    k = int(np.searchsorted(m["t"], bc["t"][q + 1]))
    entry = m["o"][k]
    atr = sig["atr1h"]
    if atr is None or atr != atr:
        return None
    sl = sig["bot"] - STOP_ATR * atr if d == 1 else sig["top"] + STOP_ATR * atr
    risk = (entry - sl) * d
    if risk <= 0:
        return None
    tp = entry + d * 2 * risk
    if target == "leg extreme":
        tp = sig["ext"]
        if (tp - entry) * d < risk:
            return None
    ex = simulate_exit(m, k, d, entry, sl, tp)
    if ex is None:
        return None
    xi, px, _ = ex
    net = (px - entry) * d / risk - (entry + px) * cost / risk
    return dict(entry_time=int(m["t"][k]), exit_time=int(m["t"][xi]), net_r=net, risk_pct=risk / entry * 100)


def run_data(symbols, start, end, cost, args):
    """-> {(set, filter, target): [trade, ...]}"""
    args.fee, args.slip = cost, 0.0
    out = {}
    for sym in symbols:
        warm = (dt.datetime.strptime(start, "%Y-%m-%d") - dt.timedelta(days=18)).strftime("%Y-%m-%d")
        m = load_1m(sym, ms(warm), ms(end), args.cache)
        bc = add_indicators(resample(m, CHART))
        trades, _ = run_symbol(sym, m, args)
        sigs = [t for t in trades if t["aligned"] and ms(start) <= t["entry_time"] < ms(end)]
        print(f"{sym}: {len(sigs)} signals, {len(m['t'])} candles", flush=True)
        for sig in sigs:
            q = confirm_bar(sig, bc)
            if q is None:
                continue
            group = "1H" if sig["group"] == "1H" else "5m"
            for name in FILTERS:
                if passes(name, sig, q, bc):
                    for target in TARGETS:
                        r = trade(sig, q, target, m, bc, cost)
                        if r:
                            r["symbol"] = sym
                            out.setdefault((group, name, target), []).append(r)
    return out


HEAD = "| Set | Filter | Target | Trades | Win % | Avg R | 95% range | Total R | PF | Max DD (R) | Median stop % |\n|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"


def row(group, name, target, s):
    if not s:
        return f"| {group} | {name} | {target} | 0 | | | | | | | |"
    return (f"| {group} | {name} | {target} | {s['n']} | {s['win']:.1f} | {s['avg']:+.3f} | {s['lo']:+.3f} to {s['hi']:+.3f} | "
            f"{s['total']:+.1f} | {s['pf']:.2f} | {s['dd']:.1f} | {s['risk']:.2f} |")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pick-symbols", nargs="+", default=["BTCUSDT", "ETHUSDT"])
    ap.add_argument("--pick-start", default="2024-10-19")
    ap.add_argument("--pick-end", default="2025-10-19")
    ap.add_argument("--check-symbols", nargs="+", default=["SOLUSDT", "XRPUSDT"])
    ap.add_argument("--check-start", default="2025-10-19")
    ap.add_argument("--check-end", default="2026-10-19")
    ap.add_argument("--cost", type=float, default=0.0005)
    ap.add_argument("--cache", default="cache")
    ap.add_argument("--out", default="backtest_filters_report.md")
    args = ap.parse_args()
    args.rr, args.atr_mult = 2.0, 0.5

    pick = run_data(args.pick_symbols, args.pick_start, args.pick_end, args.cost, args)
    o = [f"# Confirmation filters", "", f"Pick data: {', '.join(args.pick_symbols)} {args.pick_start} to {args.pick_end}. "
         f"Check data: {', '.join(args.check_symbols)} {args.check_start} to {args.check_end}.", "",
         "## Pick data: all variants", "", HEAD]
    picks = {}
    for g in SETS:
        best = None
        for name in FILTERS:
            for target in TARGETS:
                s = summarize(pick.get((g, name, target), []))
                o.append(row(g, name, target, s))
                if s and s["n"] >= MIN_TRADES and (best is None or s["avg"] > best[0]):
                    best = (s["avg"], name, target)
        picks[g] = best
    print({g: picks[g] for g in SETS}, flush=True)

    check = run_data(args.check_symbols, args.check_start, args.check_end, args.cost, args)
    o += ["", "## Check data: pick only", "", HEAD]
    verdicts = []
    for g in SETS:
        if not picks[g]:
            verdicts.append(f"- {g}: no variant with {MIN_TRADES} trades")
            continue
        _, name, target = picks[g]
        rows = check.get((g, name, target), [])
        s = summarize(rows)
        o.append(row(g, name, target, s))
        for sym in args.check_symbols:
            o.append(row(f"{g} {sym}", name, target, summarize([r for r in rows if r["symbol"] == sym])))
        verdicts.append(f"- {g}: {'PASS' if s and s['avg'] > 0 and s['lo'] > 0 else 'FAIL'}")
    o += ["", "## Pass check", ""] + verdicts
    text = "\n".join(o) + "\n"
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
