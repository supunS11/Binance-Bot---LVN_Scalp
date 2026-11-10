#!/usr/bin/env python3
"""1H trend + 5m LVN pullback zones: does a STRONG 1H trend help?

Trend: 1H ATR-size swings (3 x ATR), protected swing, close-based. STRONG = ADX(14) >= 20, DI on the trend side and
close on the trend side of EMA 50. All three fixed before the first run, nothing was tuned on the result.
Trade: first touch of a FRESH zone in the trend direction, limit at the near edge, stop 0.5 x 5m ATR beyond the far
edge, target 2R, costs 0.05% per side.

    python backtest_scalp_1h5m.py
"""
import multiprocessing as mp
import types

import numpy as np

import backtest as bt
from backtest import MIN, add_indicators, load_1m, ms, resample, run_symbol, summarize

DATA = (("BTCUSDT", "2025-10-01", "2026-10-31"), ("ETHUSDT", "2025-10-01", "2026-10-31"),
        ("SOLUSDT", "2025-10-01", "2026-10-19"), ("XRPUSDT", "2025-10-01", "2026-10-19"))
START, END, SPLIT = "2025-10-19", "2026-10-19", "2026-04-19"
HEAD = "| Set | Trades | Win % | Avg R | 95% range | First half R | Second half R | Median stop % |\n|---|---:|---:|---:|---:|---:|---:|---:|"


def wilder(x, n):
    out = np.full(len(x), np.nan)
    if len(x) >= n:
        out[n - 1] = x[:n].mean()
        for i in range(n, len(x)):
            out[i] = (out[i - 1] * (n - 1) + x[i]) / n
    return out


def strength(b, swing_atr=3.0):
    """Returns (trend, strong) per 1H bar, both known at that bar's close."""
    h, l, c, atr = b["h"], b["l"], b["c"], b["atr"]
    n = len(c)
    pc = np.r_[c[0], c[:-1]]
    tr = np.maximum.reduce([h - l, np.abs(h - pc), np.abs(l - pc)])
    up, dn = np.r_[0, np.diff(h)], np.r_[0, -np.diff(l)]
    pdm = np.where((up > dn) & (up > 0), up, 0.0)
    mdm = np.where((dn > up) & (dn > 0), dn, 0.0)
    atr_w = wilder(tr, 14)
    pdi, mdi = 100 * wilder(pdm, 14) / atr_w, 100 * wilder(mdm, 14) / atr_w
    dx = 100 * np.abs(pdi - mdi) / np.where(pdi + mdi > 0, pdi + mdi, np.nan)
    adx = np.full(n, np.nan)
    v = np.nan_to_num(dx, nan=-1.0)
    s = int(np.argmax(v >= 0)) if (v >= 0).any() else n
    if s + 14 <= n:
        adx[s + 13:] = wilder(np.nan_to_num(dx[s:]), 14)[13:]
    ema = np.full(n, np.nan)
    if n >= 50:
        ema[49] = c[:50].mean()
        for i in range(50, n):
            ema[i] = ema[i - 1] + 2 / 51 * (c[i] - ema[i - 1])
    trend = np.zeros(n, dtype=int)
    t, zd, ze, zi = 0, 1, h[0], 0
    sh = sl = None
    shi = sli = 0
    hb = lb = True
    prot_l = prot_h = None
    prot_i = 0
    for i in range(n):
        a = atr[i]
        if a == a:
            if zd == 1:
                if h[i] > ze:
                    ze, zi = h[i], i
                elif ze - l[i] >= swing_atr * a:
                    sh, shi, hb, zd, ze, zi = ze, zi, False, -1, l[i], i
            else:
                if l[i] < ze:
                    ze, zi = l[i], i
                elif h[i] - ze >= swing_atr * a:
                    sl, sli, lb, zd, ze, zi = ze, zi, False, 1, h[i], i
        if not hb and c[i] > sh:
            hb = True
            if t >= 0:
                k = shi + int(np.argmin(l[shi:i + 1]))
                prot_l, prot_i, t = l[k], k, 1
        if not lb and c[i] < sl:
            lb = True
            if t <= 0:
                k = sli + int(np.argmax(h[sli:i + 1]))
                prot_h, prot_i, t = h[k], k, -1
        if t == 1 and prot_l is not None and c[i] < prot_l:
            k = prot_i + int(np.argmax(h[prot_i:i + 1]))
            prot_h, prot_i, t, lb = h[k], k, -1, True
        elif t == -1 and prot_h is not None and c[i] > prot_h:
            k = prot_i + int(np.argmin(l[prot_i:i + 1]))
            prot_l, prot_i, t, hb = l[k], k, 1, True
        trend[i] = t
    with np.errstate(invalid="ignore"):
        strong = (adx >= 20) & (((trend == 1) & (pdi > mdi) & (c > ema)) | ((trend == -1) & (mdi > pdi) & (c < ema)))
    return trend, strong


def job(d):
    sym, a, z = d
    bt.CHART, bt.HTF, bt.CTX = 5 * MIN, 60 * MIN, 240 * MIN
    bt.REQ_BOS, bt.MIN_EFF, bt.MAX_BARS, bt.MAX_BARS_HTF, bt.PB_ATR, bt.VOL_MEDIAN = False, 0.15, 30, 16, 2.0, 100
    m = load_1m(sym, ms(a), ms(z), "cache")
    args = types.SimpleNamespace(fee=0.0005, slip=0.0, rr=2.0, atr_mult=0.5)
    trades, st = run_symbol(sym, m, args)
    b = add_indicators(resample(m, 60 * MIN))
    trend, strong = strength(b)
    out = []
    for t in trades:
        if not ms(START) <= t["entry_time"] < ms(END):
            continue
        i = int(np.searchsorted(b["tc"], t["entry_time"], side="right")) - 1
        if i < 0 or trend[i] != t["d"]:
            continue
        t["strong"] = bool(strong[i])
        out.append(t)
    print(sym, len(out), st, flush=True)
    return out


def avg(rows):
    s = summarize(rows, boot=1)
    return f"{s['avg']:+.3f} ({s['n']})" if s else "-"


def row(name, rows):
    s = summarize(rows)
    if not s:
        return f"| {name} | 0 | | | | | | |"
    a = [t for t in rows if t["entry_time"] < ms(SPLIT)]
    b = [t for t in rows if t["entry_time"] >= ms(SPLIT)]
    return f"| {name} | {s['n']} | {s['win']:.1f} | {s['avg']:+.3f} | {s['lo']:+.3f} to {s['hi']:+.3f} | {avg(a)} | {avg(b)} | {s['risk']:.2f} |"


def main():
    with mp.Pool(4) as p:
        done = p.map(job, DATA, chunksize=1)
    rows = [t for x in done for t in x]
    nested = ("5m A+", "5m nested (not A+)")
    sets = (("5m nested", lambda t: t["group"] in nested), ("5m non-nested", lambda t: t["group"] == "5m non-nested"), ("1H", lambda t: t["group"] == "1H"))
    o = [f"# 1H trend + 5m LVN zones, {START} to {END}: " + ", ".join(d[0] for d in DATA), "", HEAD]
    for name, f in sets:
        o.append(row(name + ", STRONG 1H", [t for t in rows if f(t) and t["strong"]]))
        o.append(row(name + ", WEAK 1H", [t for t in rows if f(t) and not t["strong"]]))
    o += ["", "## STRONG 1H by coin", "", HEAD]
    for d in DATA:
        for name, f in sets:
            o.append(row(f"{d[0]} {name}", [t for t in rows if t["symbol"] == d[0] and f(t) and t["strong"]]))
    text = "\n".join(o) + "\n"
    with open("backtest_scalp_1h5m_report.md", "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
