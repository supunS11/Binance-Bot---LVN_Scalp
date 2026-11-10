#!/usr/bin/env python3
"""Do the 1H/5m scalp LVNs react better than random levels of the same leg? No TP/SL, no trade results.

Zones: every LVN of every 5m and 1H leg (script defaults), widened 0.25 x 5m ATR on the entry side.
Random: 2 levels per LVN, same width, random place in the same leg (inner 80%), not overlapping its LVNs.
Both are followed the same way: still untouched when the leg is known, first touch within 3 days.
Reaction: from the near edge, price moves 1 / 2 x 5m ATR in the zone direction before a 1m close beyond the far edge
(within 1 day). All thresholds fixed before the first run, nothing tuned on the result.

    python backtest_lvn_reaction.py
    python backtest_lvn_reaction.py --script   # LVNs as the script now finds them (deep + fast), random levels as before
    python backtest_lvn_reaction.py --swing    # 4H/15m script: 15m + 4H legs, no zone widening, 15m ATR, first touch within 9 days, 3 days to react
    python backtest_lvn_reaction.py --micro    # 15m/1m scalp: 1m + 15m legs, profile from 1m bars only, 1m ATR, 1H filter,
                                               # last 3 months of each period, first touch within 14.4 hours, 4.8 hours to react
"""
import datetime as dt
import math
import sys
import multiprocessing as mp

import numpy as np

import backtest as bt
from backtest import MIN, Engine, add_indicators, came_back, find_lvns, load_1m, ms, resample
from backtest_scalp_1h5m import strength

DATA = (("BTCUSDT", "2025-10-01", "2026-10-31", "2025-10-19", "2026-10-19"), ("ETHUSDT", "2025-10-01", "2026-10-31", "2025-10-19", "2026-10-19"),
        ("SOLUSDT", "2025-10-01", "2026-10-19", "2025-10-19", "2026-10-19"), ("XRPUSDT", "2025-10-01", "2026-10-19", "2025-10-19", "2026-10-19"),
        ("BTCUSDT", "2024-10-01", "2025-10-19", "2024-10-19", "2025-10-19"), ("ETHUSDT", "2024-10-01", "2025-10-19", "2024-10-19", "2025-10-19"))
WAIT, HOLD = 3 * 1440, 1440
PAD, N_RAND = 0.25, 2

# fixed before the first run
FILTERS = (("Depth: LVN/HVN <= 0.50", "z", lambda z: z["ratio"] <= 0.50),
           ("Fast: time at price <= 0.5 x leg average", "z", lambda z: z["prints"] <= 0.5),
           ("Middle: 38-62% of the leg", "z", lambda z: 0.38 <= z["depth"] <= 0.62),
           ("Nested in a 1H LVN", "z", lambda z: z["nested"]),
           ("Leg efficiency >= 0.30", "l", lambda z: z["eff"] >= 0.30),
           ("Leg made a BOS", "l", lambda z: z["bos"]),
           ("Leg delta >= 5% in direction", "l", lambda z: z["delta"] >= 0.05),
           ("Leg volume >= 2 x median", "l", lambda z: z["vol"] >= 2.0))


def leg_info(b, eng, m, leg):
    d, s, e = leg["dir"], leg["s"], leg["e"]
    o, c, h, l = b["oL"], b["cL"], b["hL"], b["lL"]
    path = sum(h[k] - l[k] for k in range(s, e + 1))
    piv = eng.ph if d == 1 else eng.pl
    lvl = next((x for i, x in reversed(piv) if i < s), None)
    i0, i1 = np.searchsorted(m["t"], [leg["t0"], leg["t1"]])
    v, tb = m["v"][i0:i1].sum(), m["tb"][i0:i1].sum()
    return dict(eff=d * (c[e] - o[s]) / path if path > 0 else 0.0,
                bos=lvl is not None and (leg["hi"] > lvl if d == 1 else leg["lo"] < lvl),
                delta=d * (2 * tb - v) / v if v > 0 else 0.0,
                vol=sum(b["vL"][s:e + 1]) / (e - s + 1) / b["vaL"][s - 1] if b["vaL"][s - 1] > 0 else 0.0)


def prints(m, leg, top, bot):
    """Minutes of the leg that traded at the zone middle, over the leg average minutes per price."""
    i0, i1 = np.searchsorted(m["t"], [leg["t0"], leg["t1"]])
    lo, hi = leg["lo"], leg["hi"]
    h, l = np.minimum(m["h"][i0:i1], hi), np.maximum(m["l"][i0:i1], lo)
    avg = np.clip(h - l, 0, None).sum() / (hi - lo)
    mid = (top + bot) / 2
    return float(((l <= mid) & (h >= mid)).sum() / avg) if avg > 0 else 1.0


def react(m, d, top, bot, born, atr, wait=WAIT, hold=HOLD):
    """(touch index, hit 1 ATR, hit 2 ATR) or None if not touched within WAIT."""
    n = len(m["t"])
    i0 = int(np.searchsorted(m["t"], born))
    i1 = min(n, i0 + wait)
    near, far = (top, bot) if d == 1 else (bot, top)
    hit = m["l"][i0:i1] <= near if d == 1 else m["h"][i0:i1] >= near
    if not hit.any():
        return None
    k = i0 + int(np.argmax(hit))
    k1 = min(n, k + hold)
    fail = m["c"][k:k1] < far if d == 1 else m["c"][k:k1] > far
    f = int(np.argmax(fail)) if fail.any() else k1 - k
    out = [k]
    for x in (1, 2):
        lvl = near + d * x * atr
        win = m["h"][k + 1:k + 1 + f] >= lvl if d == 1 else m["l"][k + 1:k + 1 + f] <= lvl
        out.append(bool(win.any()))
    return out


def job(d):
    sym, a, z, s0, s1, script, mode, *over = d
    swing, micro = mode == "swing", mode == "micro"
    period = s0[:4]  # data period label, kept when micro mode shortens s0
    # pool workers run several jobs: reset every global a job may change
    bt.MIN_ATR, bt.MIN_VOL_CHART, bt.MIN_DIR, bt.PULLBACK = 4.0, 1.5, 0.70, 0.30
    bt.MAX_RATIO, bt.MAX_TIME = (0.50, 0.50) if script else (0.75, 0.0)
    ctf, htf, ctx = (15, 240, 240) if swing else (1, 15, 60) if micro else (5, 60, 240)
    pad, wait, hold = (0.0, 3 * WAIT, 3 * HOLD) if swing else (PAD, WAIT // 5, HOLD // 5) if micro else (PAD, WAIT, HOLD)
    bt.REQ_BOS, bt.MIN_EFF, bt.MAX_BARS, bt.MAX_BARS_HTF, bt.PB_ATR, bt.VOL_MEDIAN = False, 0.15, 30, 16, 2.0, 100
    for k, v in (over[0] if over else {}).items():  # leg rule overrides, e.g. {"MIN_ATR": 3.0}
        setattr(bt, k, v)
    m = load_1m(sym, ms(a), ms(z), "cache")
    if micro:  # 1m legs are slow to run in Python: last 3 months only, 1 week warm-up
        s0 = (dt.datetime.strptime(s1, "%Y-%m-%d") - dt.timedelta(days=92)).strftime("%Y-%m-%d")
        keep = m["t"] >= ms(s0) - 7 * 86400000
        m = {k: v[keep] for k, v in m.items()}
    rng = np.random.default_rng(7)
    b5, b1, b4 = (add_indicators(resample(m, tf * MIN)) for tf in (ctf, htf, ctx))
    tr1, st1 = strength(b1)
    tr4, _ = strength(b4)
    split = (ms(s0) + ms(s1)) // 2
    h_lvns, rows = [], []
    for tier, b, eng in ((1, b1, Engine(b1, bt.MIN_VOL_HTF, bt.MAX_BARS_HTF)), (0, b5, Engine(b5, bt.MIN_VOL_CHART))):
        for j in range(len(b["t"])):
            for leg in eng.feed():
                born = int(b["tc"][j])
                atr = b5["atr"][max(0, int(np.searchsorted(b5["tc"], born, side="right")) - 1)]
                if not atr > 0:
                    continue
                lv = find_lvns(m, leg, True)
                if not lv:
                    continue
                info = leg_info(b, eng, m, leg)
                dd, lo, hi = leg["dir"], leg["lo"], leg["hi"]
                if tier:
                    h_lvns += [(born, dd, t, bo) for t, bo, _ in lv]
                cands = [("lvn", t, bo, r) for t, bo, r in lv]
                for t, bo, _ in lv:
                    w = t - bo
                    for _ in range(N_RAND):
                        for _ in range(20):
                            x = rng.uniform(lo + bt.EDGE * (hi - lo), hi - bt.EDGE * (hi - lo) - w)
                            if not any(x <= t2 and x + w >= b2 for t2, b2, _ in lv):
                                cands.append(("rand", x + w, x, float("nan")))
                                break
                for kind, top, bot, ratio in cands:
                    pt, pb = (top + pad * atr, bot) if dd == 1 else (top, bot - pad * atr)
                    seen = came_back(m, leg["t0"], born, dd, pt, pb)
                    if kind == "lvn" and ms(s0) <= born < ms(s1):
                        rows.append(dict(kind="made", tier=tier, seen=seen, period=period))
                    if seen:
                        continue
                    r = react(m, dd, pt, pb, born, atr, wait, hold)
                    if r is None:
                        continue
                    k, h1, h2 = r
                    tt = int(m["t"][k])
                    if not ms(s0) <= tt < ms(s1):
                        continue
                    i = int(np.searchsorted(b1["tc"], tt, side="right")) - 1
                    q = int(np.searchsorted(b4["tc"], tt, side="right")) - 1
                    if i < 0 or q < 0:
                        continue
                    near = pt if dd == 1 else pb
                    nest = not tier and any(hb < born and born - hb <= (15 if swing else 1 if micro else 5) * 86400000 and hd == dd and pt >= hbo and pb <= ht for hb, hd, ht, hbo in h_lvns)
                    rows.append(dict(sym=sym, kind=kind, tier=tier, h1=h1, h2=h2, late=tt >= split, ratio=ratio,
                                     prints=prints(m, leg, top, bot), depth=((hi - (top + bot) / 2) if dd == 1 else ((top + bot) / 2 - lo)) / (hi - lo),
                                     nested=nest, strong=bool(tr1[i] == dd and st1[i]), t4=bool(tr4[q] == dd),
                                     stop=(pt - pb + 0.5 * atr) / near * 100, period=period, **info))
    print(sym, a, len(rows), flush=True)
    return rows


def rate(rows, key):
    return sum(r[key] for r in rows) / len(rows) if rows else float("nan")


def cell(rows, key):
    return f"{100 * rate(rows, key):.1f}" if rows else "-"


def diff(a, b, key):
    if not a or not b:
        return "-"
    p, q = rate(a, key), rate(b, key)
    se = math.sqrt(p * (1 - p) / len(a) + q * (1 - q) / len(b))
    return f"{100 * (p - q):+.1f} ({100 * (p - q - 1.96 * se):+.1f} to {100 * (p - q + 1.96 * se):+.1f})"


def half(a, b, key):
    if not a or not b:
        return "-"
    return f"{100 * (rate(a, key) - rate(b, key)):+.1f}"


HEAD = ("| Set | LVN n | LVN 1 ATR % | LVN 2 ATR % | Random n | Random 1 ATR % | Random 2 ATR % | LVN - random, 1 ATR (95%) | 1st half | 2nd half | 2024-25 |\n"
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")


def line(name, lvn, rnd):
    new = [r for r in lvn if r["period"] == "2025"], [r for r in rnd if r["period"] == "2025"]
    old = [r for r in lvn if r["period"] == "2024"], [r for r in rnd if r["period"] == "2024"]
    h1 = [r for r in new[0] if not r["late"]], [r for r in new[1] if not r["late"]]
    h2 = [r for r in new[0] if r["late"]], [r for r in new[1] if r["late"]]
    return (f"| {name} | {len(new[0])} | {cell(new[0], 'h1')} | {cell(new[0], 'h2')} | {len(new[1])} | {cell(new[1], 'h1')} | {cell(new[1], 'h2')} | "
            f"{diff(*new, 'h1')} | {half(*h1, 'h1')} | {half(*h2, 'h1')} | {half(*old, 'h1')} |")


def main():
    script = "--script" in sys.argv
    mode = "swing" if "--swing" in sys.argv else "micro" if "--micro" in sys.argv else ""
    swing, micro = mode == "swing", mode == "micro"
    with mp.Pool(4, maxtasksperchild=1) as p:
        rows = [r for x in p.map(job, [d + (script, mode) for d in DATA], chunksize=1) for r in x]
    o = ["# Do LVNs react better than random levels? 1H/5m scalp zones", "",
         "Main columns: BTC, ETH, SOL, XRP, 2025-10-19 to 2026-10-19. 1st / 2nd half and 2024-25 (BTC, ETH, 2024-10-19 to 2025-10-19) show only LVN - random at 1 ATR.",
         "Reaction = price moves 1 or 2 x 5m ATR from the near edge before a 1m close beyond the far edge, within 1 day of the first touch.", ""]
    if swing:
        o[0] = o[0].replace("1H/5m scalp", "4H/15m")
        o[3] = "Reaction = price moves 1 or 2 x 15m ATR from the near edge before a 1m close beyond the far edge, within 3 days of the first touch. No zone widening."
    if micro:
        o[0] = o[0].replace("1H/5m scalp", "15m/1m scalp")
        o[2] = "Main columns: BTC, ETH, SOL, XRP, 2026-07-19 to 2026-10-19. 1st / 2nd half and 2024-25 (BTC, ETH, 2025-07-19 to 2025-10-19) show only LVN - random at 1 ATR. Profiles from 1m bars only (no seconds data)."
        o[3] = "Reaction = price moves 1 or 2 x 1m ATR from the near edge (widened 0.25 x 1m ATR) before a 1m close beyond the far edge, within 4.8 hours of the first touch."
    for tf, tier in ((("15m", 0), ("4H", 1)) if swing else (("1m", 0), ("15m", 1)) if micro else (("5m", 0), ("1H", 1))):
        base = [r for r in rows if r["tier"] == tier]
        o += [f"## {tf} zones", "", HEAD]
        lv, rd = [r for r in base if r["kind"] == "lvn"], [r for r in base if r["kind"] == "rand"]
        o.append(line("All touches", lv, rd))
        if swing:
            st = lambda r: r["t4"]
            o.append(line("4H trend on the zone side", [r for r in lv if st(r)], [r for r in rd if st(r)]))
        else:
            st = lambda r: r["strong"] and (tier or (r["t4"] and r["stop"] >= 0.30))
            hl, cl = ("15m", "1H") if micro else ("1H", "4H")
            o.append(line(f"Script tradable (STRONG {hl}" + ("" if tier else f", {cl}, stop >= 0.30%") + ")", [r for r in lv if st(r)], [r for r in rd if st(r)]))
            if micro and not tier:
                st2 = lambda r: r["strong"] and r["t4"]
                o.append(line("STRONG 15m + 1H, no min stop", [r for r in lv if st2(r)], [r for r in rd if st2(r)]))
        for name, kind, f in FILTERS:
            if tier and name.startswith("Nested"):
                continue
            if swing:
                name = name.replace("1H LVN", "4H LVN")
            if micro:
                name = name.replace("1H LVN", "15m LVN")
            if name.startswith("Depth"):
                o.append(line(name + " (random: all)", [r for r in lv if f(r)], rd))
            else:
                o.append(line(name, [r for r in lv if f(r)], [r for r in rd if f(r)]))
                o.append(line("  not: " + name, [r for r in lv if not f(r)], [r for r in rd if not f(r)]))
        fast, deep = FILTERS[1][2], FILTERS[0][2]
        legok = lambda r: r["bos"] and r["delta"] >= 0.05
        o.append(line("Combined: Fast + Depth (random: Fast)", [r for r in lv if fast(r) and deep(r)], [r for r in rd if fast(r)]))
        o.append(line("Combined: Fast + Depth + BOS + delta (random: Fast + BOS + delta)", [r for r in lv if fast(r) and deep(r) and legok(r)], [r for r in rd if fast(r) and legok(r)]))
        o.append("")
    text = "\n".join(o)
    if script:
        text = text.replace("# Do LVNs", "# Script LVNs (LVN/HVN <= 0.50, time at price <= 0.50): do LVNs", 1)
    out = "backtest_lvn_reaction" + (f"_{mode}" if mode else "") + ("_script" if script else "") + "_report.md"
    with open(out, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
