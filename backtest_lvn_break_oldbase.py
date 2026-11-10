#!/usr/bin/env python3
"""1H/5m scalp: which script LVNs break, and do supply/demand zones or a confirmation entry help? No TP/SL.

Zones: 5m LVNs as the script finds them (LVN/HVN <= 0.50, time at price <= 0.50), widened 0.25 x 5m ATR, first touch.
Held = price moves 1 x 5m ATR from the near edge before a 1m close beyond the far edge (within 1 day).
Broke = a 1m close beyond the far edge within 1 day (whatever came first).

Supply/demand zone (S/D) of a leg = its base: last opposite candle in the 3 bars before the leg start (or the bar before the leg),
from the leg extreme to that candle's body (demand for up legs, supply for down legs). 1H S/D the same from 1H legs.
A 1H S/D counts while no 1m bar has touched it since it was made.

Confirmation entries, both measured from the entry price with the same 1 ATR / far-edge rule:
  1m confirm: first 1m close back outside the zone (entry side) after the touch, before any close beyond the far edge.
  5m confirm: the same with 5m closes.
All buckets fixed before the first run.

    python backtest_lvn_break.py
"""
import datetime as dt
import multiprocessing as mp
import sys

import numpy as np

import backtest as bt
from backtest import MIN, Engine, add_indicators, came_back, find_lvns, load_1m, ms, resample
from backtest_lvn_reaction import DATA, HOLD, PAD, WAIT, cell, diff, half, react
from backtest_scalp_1h5m import strength


def base_zone(b, leg):
    """(top, bot) of the leg's S/D base, top/bot as prices; for a down leg top is the far side."""
    d, s = leg["dir"], leg["s"]
    o, c = b["oL"], b["cL"]
    k = next((q for q in range(s, max(0, s - 4), -1) if d * (c[q] - o[q]) < 0), max(0, s - 1))
    if d == 1:
        return max(o[k], c[k]), min(leg["lo"], b["lL"][k])
    return max(leg["hi"], b["hL"][k]), min(o[k], c[k])


def from_entry(m, d, j, entry, far, atr, end):
    """Hit 1 ATR from entry (from bar j+1) before a 1m close beyond far, up to index end."""
    c = m["c"][j + 1:end]
    fail = c < far if d == 1 else c > far
    f = int(np.argmax(fail)) if fail.any() else len(c)
    lvl = entry + d * atr
    w = m["h"][j + 1:j + 1 + f] >= lvl if d == 1 else m["l"][j + 1:j + 1 + f] <= lvl
    return bool(w.any())


def confirm(m, d, k, near, far, atr, step, HOLD=HOLD):
    """(confirmed, held after confirm). step = 1 for 1m closes, 5 for 5m closes (bars aligned to 5m)."""
    n = len(m["t"])
    end = min(n, k + HOLD)
    j = k
    if step > 1:  # first 5m close at or after the touch bar
        j = k + (step - 1 - (int(m["t"][k]) // MIN) % step)
    while j < end:
        cl = m["c"][j]
        if (cl < far) if d == 1 else (cl > far):
            return False, False
        if (cl > near) if d == 1 else (cl < near):
            return True, from_entry(m, d, j, cl, far, atr, end)
        # a 1m close beyond far between 5m closes also kills it
        nxt = min(end, j + step)
        if step > 1:
            cc = m["c"][j + 1:nxt]
            if ((cc < far) if d == 1 else (cc > far)).any():
                return False, False
        j = nxt
    return False, False


def job(d):
    sym, a, z, s0, s1, micro = d
    period = s0[:4]
    f = 5 if micro else 1  # 1m chart: every time window / 5
    wait, hold = WAIT // f, HOLD // f
    bt.MIN_ATR, bt.MIN_VOL_CHART, bt.MIN_DIR, bt.PULLBACK = 4.0, 1.5, 0.70, 0.30
    bt.MAX_RATIO, bt.MAX_TIME = 0.50, 0.50
    bt.REQ_BOS, bt.MIN_EFF, bt.MAX_BARS, bt.MAX_BARS_HTF, bt.PB_ATR, bt.VOL_MEDIAN = False, 0.15, 30, 16, 2.0, 100
    m = load_1m(sym, ms(a), ms(z), "cache")
    if micro:  # last 3 months, 1 week warm-up (same as backtest_lvn_reaction --micro)
        s0 = (dt.datetime.strptime(s1, "%Y-%m-%d") - dt.timedelta(days=92)).strftime("%Y-%m-%d")
        keep = m["t"] >= ms(s0) - 7 * 86400000
        m = {k: v[keep] for k, v in m.items()}
    b5, b1, b4 = (add_indicators(resample(m, tf * MIN)) for tf in ((1, 15, 60) if micro else (5, 60, 240)))
    tr1, st1 = strength(b1)
    tr4, _ = strength(b4)
    split = (ms(s0) + ms(s1)) // 2
    # 1H S/D zones: (born, dir, top, bot)
    hsd = []
    e1 = Engine(b1, bt.MIN_VOL_HTF, bt.MAX_BARS_HTF)
    for j in range(len(b1["t"])):
        for leg in e1.feed():
            t, bo = base_zone(b1, leg)
            hsd.append((int(b1["tc"][j]), leg["dir"], t, bo))
    rows = []
    e5 = Engine(b5, bt.MIN_VOL_CHART)
    for j in range(len(b5["t"])):
        for leg in e5.feed():
            born = int(b5["tc"][j])
            atr = b5["atr"][j]
            if not atr > 0:
                continue
            lv = find_lvns(m, leg, True)
            dd = leg["dir"]
            st_, sb_ = base_zone(b5, leg)
            cands = [("lvn", t, bo) for t, bo, _ in lv] + [("sd", st_, sb_)]
            for kind, top, bot in cands:
                pt, pb = (top + PAD * atr, bot) if dd == 1 else (top, bot - PAD * atr)
                if came_back(m, leg["t0"], born, dd, pt, pb):
                    continue
                r = react(m, dd, pt, pb, born, atr, wait, hold)
                if r is None:
                    continue
                k, h1, _ = r
                tt = int(m["t"][k])
                if not ms(s0) <= tt < ms(s1):
                    continue
                i = int(np.searchsorted(b1["tc"], tt, side="right")) - 1
                q = int(np.searchsorted(b4["tc"], tt, side="right")) - 1
                if i < 0 or q < 0:
                    continue
                near, far = (pt, pb) if dd == 1 else (pb, pt)
                kend = min(len(m["t"]), k + hold)
                cc = m["c"][k:kend]
                broke = bool(((cc < far) if dd == 1 else (cc > far)).any())
                # gap from zone far edge to own leg S/D near edge, in 5m ATR
                gap = (far - st_) / atr if dd == 1 else (sb_ - far) / atr
                # nearest fresh 1H S/D beyond the far edge (same side), and overlap with a fresh 1H S/D
                hgap, hover = float("inf"), False
                for hb, hd, ht, hbo in hsd:
                    if hd != dd or hb >= tt or tt - hb > 10 * 86400000 // f:
                        continue
                    i0, i1 = np.searchsorted(m["t"], [hb, tt])
                    seg_l, seg_h = m["l"][i0:i1], m["h"][i0:i1]
                    fresh = not ((seg_l <= ht).any() if dd == 1 else (seg_h >= hbo).any())
                    if not fresh:
                        continue
                    if pb <= ht and pt >= hbo:
                        hover = True
                    g = (far - ht) / atr if dd == 1 else (hbo - far) / atr
                    if g >= 0:
                        hgap = min(hgap, g)
                # approach: how far price travelled toward the zone in the 30 min before the touch
                w0 = max(0, k - 30 // f)
                speed = (m["h"][w0:k + 1].max() - near) / atr if dd == 1 else (near - m["l"][w0:k + 1].min()) / atr
                # same geometry for every zone: +1 ATR from the near edge before a 1m close 1 ATR beyond the near edge
                fx = from_entry(m, dd, k, near, near - dd * atr, atr, kend)
                c1, c1h = confirm(m, dd, k, near, far, atr, 1, hold)
                c5, c5h = confirm(m, dd, k, near, far, atr, 5, hold)
                rows.append(dict(sym=sym, kind=kind, h1=h1, broke=broke, late=tt >= split, period=period,
                                 strong=bool(tr1[i] == dd and st1[i] and tr4[q] == dd), gap=gap, hgap=hgap, hover=hover,
                                 speed=speed, fx=fx, width=abs(pt - pb) / atr, age=(tt - born) / 3600000 * f, c1=c1, c1h=c1h, c5=c5, c5h=c5h,
                                 c1w=c1 and c1h, c5w=c5 and c5h))
    print(sym, a, len(rows), flush=True)
    return rows


BUCKETS = (("Own S/D gap <= 1 ATR", lambda r: r["gap"] <= 1), ("Own S/D gap 1-3 ATR", lambda r: 1 < r["gap"] <= 3),
           ("Own S/D gap > 3 ATR", lambda r: r["gap"] > 3),
           ("Fresh 1H S/D within 2 ATR beyond", lambda r: r["hgap"] <= 2), ("No fresh 1H S/D within 2 ATR beyond", lambda r: r["hgap"] > 2),
           ("Inside a fresh 1H S/D", lambda r: r["hover"]),
           ("Approach <= 2 ATR in 30 min", lambda r: r["speed"] <= 2), ("Approach 2-4 ATR in 30 min", lambda r: 2 < r["speed"] <= 4),
           ("Approach > 4 ATR in 30 min", lambda r: r["speed"] > 4),
           ("Best: gap <= 1, approach > 2 ATR, age >= 2 h", lambda r: r["gap"] <= 1 and r["speed"] > 2 and r["age"] >= 2),
           ("Age < 2 h", lambda r: r["age"] < 2), ("Age 2-12 h", lambda r: 2 <= r["age"] < 12), ("Age >= 12 h", lambda r: r["age"] >= 12))


def pct(rows, key):
    return f"{100 * sum(r[key] for r in rows) / len(rows):.1f}" if rows else "-"


def tab(rows, title):
    new = [r for r in rows if r["period"] == "2025"]
    old = [r for r in rows if r["period"] == "2024"]
    lv = [r for r in new if r["kind"] == "lvn"]
    allv = lambda f: [r for r in lv if f(r)]
    o = [f"### {title}", "",
         "| Set | n | Median width (ATR) | Held 1 ATR % | Fixed 1 ATR stop: held % | Held - all LVNs (95%) | 1st half | 2nd half | 2024-25 |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]

    def ln(name, f, kind="lvn"):
        s = [r for r in new if r["kind"] == kind and f(r)]
        h1 = [r for r in s if not r["late"]], [r for r in lv if not r["late"]]
        h2 = [r for r in s if r["late"]], [r for r in lv if r["late"]]
        ol = [r for r in old if r["kind"] == kind and f(r)], [r for r in old if r["kind"] == "lvn"]
        return f"| {name} | {len(s)} | {np.median([r['width'] for r in s]) if s else float('nan'):.2f} | {pct(s, 'h1')} | {pct(s, 'fx')} | {diff(s, lv, 'h1')} | {half(*h1, 'h1')} | {half(*h2, 'h1')} | {half(*ol, 'h1')} |"

    o.append(ln("All script LVNs", lambda r: True))
    o.append(ln("Own leg S/D zone (base) instead of the LVN", lambda r: True, "sd"))
    o += [ln(n, f) for n, f in BUCKETS]
    o += ["", "Confirmation entry (instead of a limit at the near edge):", "",
          "| Entry | Touches | Confirmed % | Held after confirm % | Held per touch % |", "|---|---:|---:|---:|---:|",
          f"| Limit at near edge | {len(lv)} | 100 | {pct(lv, 'h1')} | {pct(lv, 'h1')} |"]
    for name, c, h, w in (("1m close back out", "c1", "c1h", "c1w"), ("5m close back out", "c5", "c5h", "c5w")):
        cf = [r for r in lv if r[c]]
        o.append(f"| {name} | {len(lv)} | {pct(lv, c)} | {pct(cf, h)} | {pct(lv, w)} |")
    sd = [r for r in new if r["kind"] == "sd"]
    for name, c, h in (("S/D zone, limit", None, "h1"), ("S/D zone, 5m close back out", "c5", "c5h")):
        cf = [r for r in sd if not c or r[c]]
        o.append(f"| {name} | {len(sd)} | {pct(sd, c) if c else '100'} | {pct(cf, h)} | {pct(sd, 'c5w') if c else pct(sd, 'h1')} |")
    return o + [""]


def main():
    micro = "--micro" in sys.argv
    with mp.Pool(4, maxtasksperchild=1) as p:
        rows = [r for x in p.map(job, [d + (micro,) for d in DATA], chunksize=1) for r in x]
    o = ["# 1H/5m scalp: which LVNs break? S/D zones and confirmation entries", "",
         "BTC, ETH, SOL, XRP, 2025-10-19 to 2026-10-19 (2024-25 = BTC, ETH). 5m script LVNs, first touch. Held = 1 x 5m ATR from the near edge",
         "before a 1m close beyond the far edge; Fixed stop = +1 ATR from the near edge before a 1m close 1 ATR beyond the near edge (same for every zone, so width does not matter). Halves and 2024-25 show the set minus all LVNs.", ""]
    o += tab(rows, "All touches")
    o += tab([r for r in rows if r["strong"]], "STRONG 1H + 4H trend on the zone side")
    text = "\n".join(o)
    if micro:
        for x, y in (("# 1H/5m scalp", "# 15m/1m scalp"), ("2025-10-19 to 2026-10-19 (2024-25 = BTC, ETH)", "2026-07-19 to 2026-10-19 (2024-25 = BTC, ETH, 2025-07-19 to 2025-10-19)"),
                     ("5m script LVNs", "1m script LVNs"), ("5m ATR", "1m ATR"), ("STRONG 1H + 4H", "STRONG 15m + 1H"), ("1H S/D", "15m S/D")):
            text = text.replace(x, y)
        text += (chr(10) * 2 + "1m chart: every time window is / 5. Approach = last 6 min (rows say 30 min). Age is in units of 12 min (rows say h: 2 h = 24 min, 12 h = 2.4 h). "
                 "Reaction within 4.8 h of the first touch.")
    with open("backtest_lvn_break" + ("_micro" if micro else "") + "_report.md", "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
