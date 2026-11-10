#!/usr/bin/env python3
"""Backtest of the Nested LVN Zones logic on any Binance USDT-M perpetual.

Python port of Nested_LVN_Zones.pine. Every first touch of a FRESH zone is one trade:
limit entry at the near edge, stop 0.5 x ATR(5m) beyond the far edge, target 2R.
Layers: 4H context, 1H bias + main zones, 5m entry zones (A+ as in the Pine script).
Zones are only tradable from the bar after they are created. Within a 1m candle the
stop is assumed to hit before the target.

    python backtest.py --symbols BTCUSDT.P ETHUSDT.P SOLUSDT
"""
import argparse
import calendar
import csv
import datetime as dt
import json
import math
import os
import time
import urllib.error
import urllib.request

import numpy as np

MIN = 60_000
CHART = 5 * MIN
HTF = 60 * MIN
CTX = 240 * MIN

# Same defaults as the Pine script
PIV = 3
MIN_ATR = 4.0
MIN_BARS = 2
MAX_BARS = 10
MIN_EFF = 0.30
MIN_VOL_CHART = 1.5
MIN_VOL_HTF = 1.1
MIN_DIR = 0.70
PULLBACK = 0.30
ATR_LEN = 14
VOL_LEN = 20
ROWS = 150
PEAK_W = 2
MAX_LVN = 5
EDGE = 0.10
MAX_RATIO = 0.75
MAX_GAP = 0.0  # chart-TF LVN: max gap from far edge to the leg base S/D near edge (x chart ATR), 0 = off
MAX_TIME = 0.0  # max intrabars at the zone middle row / leg average per row, 0 = off
WEAK_N = 9
FILL_N = 18
BROKE_N = 6
RANGE_N = 120
MIN_ROOM = 2.0
# Leg rule options (off by default): HTF max candles, pullback must also be >= N x ATR, volume baseline = median of N bars
MAX_BARS_HTF = None
PB_ATR = 0.0
VOL_MEDIAN = 0
REQ_BOS = True
# Limit order this many chart ATRs before the near edge, stop unchanged, one trade per zone (0 = at the edge)
ENTRY_BUF = 0.0
# Widen new zones on the entry side by this many chart ATRs, as the scalp Pine script does
ZONE_PAD = 0.0


def ms(day):
    return calendar.timegm(dt.datetime.strptime(day, "%Y-%m-%d").timetuple()) * 1000


def stamp(t):
    return dt.datetime.fromtimestamp(t / 1000, dt.timezone.utc).strftime("%Y-%m-%d %H:%M")


# ───────────────────────── Data ─────────────────────────
def get_json(url):
    for attempt in range(6):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (418, 429):
                time.sleep(60)
            elif e.code >= 500:
                time.sleep(2 ** attempt)
            else:
                raise SystemExit(f"Binance rejected {url}: HTTP {e.code} {e.read().decode()[:200]}")
        except (urllib.error.URLError, TimeoutError):
            time.sleep(2 ** attempt)
    raise SystemExit(f"Download failed: {url}")


def load_1m(symbol, start, end, cache):
    os.makedirs(cache, exist_ok=True)
    path = os.path.join(cache, f"{symbol}_{start}_{end}.npz")
    if os.path.exists(path):
        d = np.load(path)
        if "tb" in d.files:
            return {k: d[k] for k in d.files}
    rows, cur = [], start
    while cur < end:
        url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval=1m&startTime={cur}&endTime={end - 1}&limit=1500"
        chunk = get_json(url)
        if not chunk:
            break
        rows += [(r[0], float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[5]), float(r[9])) for r in chunk]
        cur = chunk[-1][0] + MIN
        if len(rows) % 150000 < 1500:
            print(f"  {symbol}: {len(rows)} candles, at {stamp(cur)}", flush=True)
    if not rows:
        raise SystemExit(f"No data for {symbol}")
    a = np.array(rows)
    d = dict(t=a[:, 0].astype(np.int64), o=a[:, 1], h=a[:, 2], l=a[:, 3], c=a[:, 4], v=a[:, 5], tb=a[:, 6])
    np.savez(path, **d)
    return d


def resample(m, tf):
    key = m["t"] // tf * tf
    t, idx = np.unique(key, return_index=True)
    if m["t"][-1] + MIN < t[-1] + tf:  # drop the unfinished last bar
        t, idx = t[:-1], idx[:-1]
        cut = np.searchsorted(m["t"], key[-1])
    else:
        cut = len(m["t"])
    h = np.maximum.reduceat(m["h"][:cut], idx)
    l = np.minimum.reduceat(m["l"][:cut], idx)
    v = np.add.reduceat(m["v"][:cut], idx)
    tb = np.add.reduceat(m["tb"][:cut], idx)
    last = np.r_[idx[1:], cut] - 1
    return dict(t=t, o=m["o"][idx], h=h, l=l, c=m["c"][last], v=v, tb=tb, tc=t + tf)


def add_indicators(b):
    n = len(b["t"])
    pc = np.r_[b["c"][0], b["c"][:-1]]
    tr = np.maximum.reduce([b["h"] - b["l"], np.abs(b["h"] - pc), np.abs(b["l"] - pc)])
    tr[0] = b["h"][0] - b["l"][0]
    atr = np.full(n, np.nan)
    if n >= ATR_LEN:
        atr[ATR_LEN - 1] = tr[:ATR_LEN].mean()
        for i in range(ATR_LEN, n):
            atr[i] = (atr[i - 1] * (ATR_LEN - 1) + tr[i]) / ATR_LEN
    va = np.full(n, np.nan)
    if n >= VOL_LEN:
        cs = np.cumsum(np.r_[0, b["v"]])
        va[VOL_LEN - 1:] = (cs[VOL_LEN:] - cs[:-VOL_LEN]) / VOL_LEN
    if VOL_MEDIAN and n >= VOL_MEDIAN:
        va = np.full(n, np.nan)
        va[VOL_MEDIAN - 1:] = np.median(np.lib.stride_tricks.sliding_window_view(b["v"], VOL_MEDIAN), axis=1)
    b["atr"], b["va"] = atr, va
    for k in ("o", "h", "l", "c", "v", "tb", "atr", "va"):
        b[k + "L"] = b[k].tolist()
    return b


# ───────────────────────── Leg engine (same logic as Engine in the Pine script) ─────────────────────────
class Engine:
    def __init__(self, b, min_vol, max_bars=None):
        self.b, self.min_vol = b, min_vol
        self.max_bars = max_bars or MAX_BARS
        self.n = 0
        self.ph, self.pl = [], []
        self.last_sh = self.last_sl = None
        self.sh_broken = self.sl_broken = True
        self.trend = 0
        self.choch = False
        self.last_brk = 0
        self.b_o = self.s_o = None

    def validate(self, d, s, e, lo, hi):
        b = self.b
        bars = e - s + 1
        if s < 1 or bars < MIN_BARS or bars > self.max_bars:
            return None
        o, c, h, l, v = b["oL"], b["cL"], b["hL"], b["lL"], b["vL"]
        path = sum(h[k] - l[k] for k in range(s, e + 1))
        vsum = sum(v[k] for k in range(s, e + 1))
        ndir = sum(1 for k in range(s, e + 1) if d * (c[k] - o[k]) > 0)
        nden = bars - (d * (c[s] - o[s]) <= 0) - (d * (c[e] - o[e]) <= 0)
        net = d * (c[e] - o[s])
        atr, va = b["atrL"][s - 1], b["vaL"][s - 1]
        if not (atr > 0 and va > 0 and path > 0):
            return None
        piv = self.ph if d == 1 else self.pl
        lvl = next((x for i, x in reversed(piv) if i < s), None)
        bos = lvl is not None and (hi > lvl if d == 1 else lo < lvl)
        if (REQ_BOS and not bos) or (hi - lo) / atr < MIN_ATR or net / path < MIN_EFF:
            return None
        if vsum / bars / va < self.min_vol or ndir / max(nden, 1) < MIN_DIR:
            return None
        return dict(dir=d, t0=int(b["t"][s]), t1=int(b["tc"][e]), lo=lo, hi=hi, s=s, e=e)

    def pb_ok(self, dip, i):
        a = self.b["atrL"][i]
        return PB_ATR == 0 or a != a or dip >= PB_ATR * a

    def feed(self):
        b, i = self.b, self.n
        self.n += 1
        h, l, c = b["hL"], b["lL"], b["cL"]
        p = i - PIV
        if p - PIV >= 0:
            rng = [k for k in range(p - PIV, p + PIV + 1) if k != p]
            if all(h[k] < h[p] for k in rng):
                self.ph.append((p, h[p]))
                self.last_sh, self.sh_broken = h[p], False
            if all(l[k] > l[p] for k in rng):
                self.pl.append((p, l[p]))
                self.last_sl, self.sl_broken = l[p], False
        hi, lo, cl = h[i], l[i], c[i]
        if not self.sh_broken and cl > self.last_sh:
            self.sh_broken, self.choch = True, self.trend == -1
            self.trend, self.last_brk = 1, i
        if not self.sl_broken and cl < self.last_sl:
            self.sl_broken, self.choch = True, self.trend == 1
            self.trend, self.last_brk = -1, i

        out = []
        if self.b_o is None:
            self.b_o, self.b_e, self.b_lo, self.b_hi = i, i, lo, hi
        else:
            r = self.b_hi - self.b_lo
            if hi <= self.b_hi and self.b_e > self.b_o and r > 0 and self.b_hi - lo >= PULLBACK * r and self.pb_ok(self.b_hi - lo, i):
                out.append(self.validate(1, self.b_o, self.b_e, self.b_lo, self.b_hi))
                self.b_o, self.b_e, self.b_lo, self.b_hi = i, i, lo, hi
            elif lo < self.b_lo:
                self.b_o, self.b_e, self.b_lo, self.b_hi = i, i, lo, hi
            elif hi > self.b_hi:
                self.b_hi, self.b_e = hi, i
                if i - self.b_o + 1 > self.max_bars:
                    s0 = i - self.max_bars + 1
                    self.b_o = min(range(s0, i + 1), key=lambda k: l[k])
                    self.b_lo = l[self.b_o]
        if self.s_o is None:
            self.s_o, self.s_e, self.s_hi, self.s_lo = i, i, hi, lo
        else:
            r = self.s_hi - self.s_lo
            if lo >= self.s_lo and self.s_e > self.s_o and r > 0 and hi - self.s_lo >= PULLBACK * r and self.pb_ok(hi - self.s_lo, i):
                out.append(self.validate(-1, self.s_o, self.s_e, self.s_lo, self.s_hi))
                self.s_o, self.s_e, self.s_hi, self.s_lo = i, i, hi, lo
            elif hi > self.s_hi:
                self.s_o, self.s_e, self.s_hi, self.s_lo = i, i, hi, lo
            elif lo < self.s_lo:
                self.s_lo, self.s_e = lo, i
                if i - self.s_o + 1 > self.max_bars:
                    s0 = i - self.max_bars + 1
                    self.s_o = max(range(s0, i + 1), key=lambda k: h[k])
                    self.s_hi = h[self.s_o]
        return [g for g in out if g]

    def bias(self):
        if self.trend == 0 or self.n - 1 - self.last_brk > RANGE_N:
            return 0
        return self.trend


def find_lvns(m, leg, with_ratio=False):
    """1m volume profile of the leg -> [(top, bot), ...], deepest LVNs first."""
    lo, hi = leg["lo"], leg["hi"]
    step = (hi - lo) / ROWS
    if step <= 0:
        return []
    i0, i1 = np.searchsorted(m["t"], [leg["t0"], leg["t1"]])
    prof = np.zeros(ROWS + 1)
    bl = np.maximum(m["l"][i0:i1], lo)
    bh = np.minimum(m["h"][i0:i1], hi)
    vv = m["v"][i0:i1]
    keep = (bh >= bl) & (vv > 0)
    bl, bh, vv = bl[keep], bh[keep], vv[keep]
    r0 = np.clip(np.floor((bl - lo) / step).astype(int), 0, ROWS - 1)
    r1 = np.clip(np.floor((bh - lo) / step).astype(int), 0, ROWS - 1)
    share = vv / (r1 - r0 + 1)
    np.add.at(prof, r0, share)
    np.add.at(prof, r1 + 1, -share)
    prof = np.cumsum(prof)[:ROWS]
    tp = np.zeros(ROWS + 1)
    np.add.at(tp, r0, 1)
    np.add.at(tp, r1 + 1, -1)
    tp = np.cumsum(tp)[:ROWS]
    t_avg = (r1 - r0 + 1).sum() / ROWS
    sm = np.convolve(prof, np.ones(3), "same")
    sm[1:-1] /= 3
    sm[0] /= 2
    sm[-1] /= 2
    sm = sm.tolist()
    pk = [r for r in range(ROWS) if sm[r] > 0
          and all(sm[q] <= sm[r] for q in range(max(0, r - PEAK_W), r))
          and all(sm[q] < sm[r] for q in range(r + 1, min(ROWS, r + PEAK_W + 1)))]
    in0 = math.ceil(ROWS * EDGE)
    in1 = ROWS - 1 - in0
    res = []
    for a, c in zip(pk, pk[1:]):
        if c - a < 2:
            continue
        v = min(range(a + 1, c), key=lambda r: sm[r])
        ref = min(sm[a], sm[c])
        ratio = sm[v] / ref if ref > 0 else 1.0
        if in0 <= v <= in1 and ratio <= MAX_RATIO:
            lim = sm[v] + 0.30 * (ref - sm[v])
            z0 = z1 = v
            while z0 - 1 > a and z0 - 1 >= in0 and sm[z0 - 1] <= lim:
                z0 -= 1
            while z1 + 1 < c and z1 + 1 <= in1 and sm[z1 + 1] <= lim:
                z1 += 1
            if MAX_TIME and (t_avg <= 0 or tp[min(z1, (z0 + z1 + 1) // 2)] / t_avg > MAX_TIME):
                continue
            res.append((ratio, lo + (z1 + 1) * step, lo + z0 * step))
    res.sort()
    if with_ratio:
        return [(t, b, r) for r, t, b in res[:MAX_LVN]]
    return [(t, b) for _, t, b in res[:MAX_LVN]]


# ───────────────────────── Trade simulation ─────────────────────────
def simulate_exit(m, i, d, entry, sl, tp):
    """Walks 1m candles from the fill candle i. Stop wins ties. None = still open at end of data."""
    n = len(m["t"])
    chunk = 2000
    k0 = i
    while k0 < n:
        k1 = min(n, k0 + chunk)
        lows, highs = m["l"][k0:k1], m["h"][k0:k1]
        stop_hit = lows <= sl if d == 1 else highs >= sl
        tp_hit = highs >= tp if d == 1 else lows <= tp
        if k0 == i:
            tp_hit[0] = False  # the fill candle can stop out, but never counts as a target
        s = int(np.argmax(stop_hit)) if stop_hit.any() else None
        t = int(np.argmax(tp_hit)) if tp_hit.any() else None
        if s is not None and (t is None or s <= t):
            op = m["o"][k0 + s]
            px = sl
            if k0 + s > i:  # a gap through the stop fills at the open
                px = min(sl, op) if d == 1 else max(sl, op)
            return k0 + s, px, "SL"
        if t is not None:
            return k0 + t, tp, "TP"
        k0 = k1
        chunk *= 2
    return None


def came_back(m, t0, t1, d, top, bot):
    """Did price return to the zone after the impulse first left it fully behind?"""
    i0, i1 = np.searchsorted(m["t"], [t0, t1])
    away = m["l"][i0:i1] > top if d == 1 else m["h"][i0:i1] < bot
    if not away.any():
        return False
    k = i0 + int(np.argmax(away)) + 1
    return bool((m["l"][k:i1] <= top).any() if d == 1 else (m["h"][k:i1] >= bot).any())


def confluence(b, leg, top, bot, fib_a=0.5, fib_b=0.786, ob_look=3):
    """(fib, fvg, ob) overlap of a zone with its own leg, same rules as the Pine script."""
    d, s, e, lo, hi = leg["dir"], leg["s"], leg["e"], leg["lo"], leg["hi"]
    o, h, l, c = b["oL"], b["hL"], b["lL"], b["cL"]
    rng = hi - lo
    a1, a2 = (hi - fib_a * rng, hi - fib_b * rng) if d == 1 else (lo + fib_a * rng, lo + fib_b * rng)
    fib = top >= min(a1, a2) and bot <= max(a1, a2)
    fvg = False
    for k in range(s + 1, e):
        g_b, g_t = (h[k - 1], l[k + 1]) if d == 1 else (h[k + 1], l[k - 1])
        if g_t > g_b and top >= g_b and bot <= g_t:
            fvg = True
            break
    ob = False
    for k in range(s - 1, e):
        if d * (c[k] - o[k]) < 0 and top >= l[k] and bot <= h[k]:
            if any((c[q] > h[k]) if d == 1 else (c[q] < l[k]) for q in range(k + 1, min(k + ob_look, e) + 1)):
                ob = True
                break
    return fib, fvg, ob


def run_symbol(symbol, m, args, on_close=None):
    """on_close(j, zones, bc): optional hook called after every 5m bar j is fully processed (the zone state a
    live snapshot taken at that bar's close would see). It does not change anything here."""
    bc = add_indicators(resample(m, CHART))
    bh = add_indicators(resample(m, HTF))
    bx = add_indicators(resample(m, CTX))
    ec, eh, ex = Engine(bc, MIN_VOL_CHART), Engine(bh, MIN_VOL_HTF, MAX_BARS_HTF), Engine(bx, MIN_VOL_HTF, MAX_BARS_HTF)
    zones, trades = [], []
    stats = dict(zones_4h=0, zones_1h=0, zones_5m=0, legs_4h=0, legs_1h=0, legs_5m=0, pretouched=0, bad_risk=0, open_end=0)
    cost = args.fee + args.slip
    strong_h = strong_l = room = None
    hi_x = hi_h = 0
    lT = m["t"]

    def make_zones(leg, tier, now_end, j, t):
        d = leg["dir"]
        gap_ref = bz = None
        if tier == 0:  # standard S/D proximal line of the leg (base candles), None if the leg has no base
            from backtest_lvn_break import base_zone
            bz = base_zone(bc, leg)
            gap_ref = None if bz is None else (bz[0] if d == 1 else bz[1])
        for top, bot, ratio in find_lvns(m, leg, True):
            gap = None
            a0 = bc["atr"][j]
            if gap_ref is not None and a0 > 0:
                gap = ((bot - gap_ref) if d == 1 else (gap_ref - top)) / a0
                if MAX_GAP and gap > MAX_GAP:
                    continue
            if ZONE_PAD:
                pad = ZONE_PAD * np.nan_to_num(bc["atr"][max(j - 1, 0) if tier else j])
                top, bot = (top + pad, bot) if d == 1 else (top, bot - pad)
            z = dict(top=top, bot=bot, ratio=ratio, dir=d, tier=tier, origin=leg["lo"] if d == 1 else leg["hi"],
                     status=0, inside=0, beyond=0, nested=False, parent_fresh=False, born=j, made=t, gap=gap, sd=bz, t0=leg["t0"], ext=leg["hi"] if d == 1 else leg["lo"])
            z["fib"], z["fvg"], z["ob"] = confluence((bc, bh, bx)[tier], leg, top, bot)
            if came_back(m, leg["t0"], now_end, d, top, bot):
                z["status"] = 1
                stats["pretouched"] += 1
            if tier < 2:
                for oz in zones:
                    if oz["tier"] < 2 and oz["status"] < 3 and oz["tier"] != tier and oz["dir"] == d and top >= oz["bot"] and bot <= oz["top"]:
                        if tier == 1:
                            oz["nested"] = True
                            oz["parent_fresh"] = oz["parent_fresh"] or z["status"] == 0
                        else:
                            z["nested"] = True
                            z["parent_fresh"] = z["parent_fresh"] or oz["status"] == 0
            zones.append(z)
            stats[("zones_5m", "zones_1h", "zones_4h")[tier]] += 1

    def blocked(z):
        entry = z["top"] if z["dir"] == 1 else z["bot"]
        if room is not None and room == room:
            if z["dir"] == 1 and strong_h is not None and entry < strong_h < entry + MIN_ROOM * room:
                return True
            if z["dir"] == -1 and strong_l is not None and entry - MIN_ROOM * room < strong_l < entry:
                return True
        return any(o["tier"] == 2 and o["status"] == 0 and o["dir"] != z["dir"] and z["top"] >= o["bot"] and z["bot"] <= o["top"] for o in zones)

    def has_parent(z):
        return any(o["tier"] == 1 and o["status"] < 3 and o["dir"] == z["dir"] and z["top"] >= o["bot"] and z["bot"] <= o["top"] for o in zones)

    for j in range(len(bc["t"])):
        t = int(bc["t"][j])
        cl, hi, lo = bc["cL"][j], bc["hL"][j], bc["lL"][j]

        # higher-TF bars that closed at or before this bar's open are known now
        while hi_x < len(bx["t"]) and bx["tc"][hi_x] <= t:
            xc = bx["cL"][hi_x]
            if strong_h is not None and xc > strong_h:
                strong_h = None
            if strong_l is not None and xc < strong_l:
                strong_l = None
            for z in zones:
                if z["tier"] == 2 and z["status"] < 3 and bx["tc"][hi_x] > z["made"] and (xc < z["bot"] if z["dir"] == 1 else xc > z["top"]):
                    z["status"] = 4
            for leg in ex.feed():
                stats["legs_4h"] += 1
                if leg["dir"] == 1:
                    strong_l = leg["lo"]
                else:
                    strong_h = leg["hi"]
                make_zones(leg, 2, t, j, t)
            hi_x += 1
        while hi_h < len(bh["t"]) and bh["tc"][hi_h] <= t:
            hc = bh["cL"][hi_h]
            room = bh["atrL"][hi_h]
            for z in zones:
                if z["tier"] < 2 and z["status"] < 3 and bh["tc"][hi_h] > z["made"] and (hc < z["bot"] if z["dir"] == 1 else hc > z["top"]):
                    z["status"] = 4
            for leg in eh.feed():
                stats["legs_1h"] += 1
                make_zones(leg, 1, t, j, t)
            hi_h += 1
        bias = eh.bias()

        i0, i1 = np.searchsorted(lT, [t, t + CHART])
        # touches first, on the state known before this bar's close
        for z in zones:
            d = z["dir"]
            if z["tier"] == 2 or z["status"] != 0 or z["born"] >= j or z.get("traded"):
                continue
            if j == 0 or np.isnan(bc["atr"][j - 1]):
                continue
            edge = z["top"] if d == 1 else z["bot"]
            level = edge + d * ENTRY_BUF * bc["atr"][j - 1]
            if not (lo <= level if d == 1 else hi >= level):
                continue
            z["traded"] = True
            seg = m["l"][i0:i1] <= level if d == 1 else m["h"][i0:i1] >= level
            k = i0 + int(np.argmax(seg))
            op = m["o"][k]
            entry = min(level, op) if d == 1 else max(level, op)
            pad = args.atr_mult * bc["atr"][j - 1]
            sl = z["bot"] - pad if d == 1 else z["top"] + pad
            risk = (entry - sl) * d
            if risk <= 0:
                stats["bad_risk"] += 1
                continue
            ex_ = simulate_exit(m, k, d, entry, sl, entry + d * args.rr * risk)
            if ex_ is None:
                stats["open_end"] += 1
                continue
            xi, px, why = ex_
            reached = bool((m["l"][k:xi + 1] <= edge).any() if d == 1 else (m["h"][k:xi + 1] >= edge).any())
            tp_px = entry + d * args.rr * risk
            clear = not any(o["tier"] >= 1 and o["status"] < 3 and o["dir"] != d and o["top"] >= min(entry, tp_px) and o["bot"] <= max(entry, tp_px) for o in zones)
            approach = sum(bc["vL"][j - 6:j]) / 6 / bc["vaL"][j - 1] if j >= 6 else float("nan")
            gross = (px - entry) * d / risk
            net = gross - (entry + px) * cost / risk
            aligned = bias == 0 or bias == d
            block = blocked(z)
            if z["tier"] == 1:
                group = "1H"
            elif z["parent_fresh"] and aligned and not block and has_parent(z):
                group = "5m A+"
            elif z["nested"]:
                group = "5m nested (not A+)"
            else:
                group = "5m non-nested"
            trades.append(dict(symbol=symbol, group=group, dir="long" if d == 1 else "short", aligned=aligned,
                               blocked=block, bias=bias, entry_time=int(lT[k]), exit_time=int(lT[xi]), entry=entry,
                               sl=sl, tp=entry + d * args.rr * risk, exit=px, reason=why, gross_r=gross, net_r=net,
                               risk_pct=risk / entry * 100, d=d, top=z["top"], bot=z["bot"], j=j, k=k, atr5=float(bc["atr"][j - 1]), atr1h=room, ext=z["ext"], fib=z["fib"], fvg=z["fvg"], ob=z["ob"], reached=reached, ratio=z["ratio"], clear=clear, approach=approach))

        alive = []
        for z in zones:
            if z["status"] >= 3:
                continue
            alive.append(z)
            if z["born"] >= j:
                continue
            d = z["dir"]
            touched = lo <= z["top"] if d == 1 else hi >= z["bot"]
            invalid = cl < z["origin"] if d == 1 else cl > z["origin"]
            if z["tier"] == 2:
                if invalid:
                    z["status"] = 5
                elif touched and z["status"] == 0:
                    z["status"] = 1
                continue
            z["inside"] += z["bot"] <= cl <= z["top"]
            beyond = cl < z["bot"] if d == 1 else cl > z["top"]
            z["beyond"] = z["beyond"] + 1 if beyond else 0
            if invalid:
                z["status"] = 5
            elif z["beyond"] >= BROKE_N:
                z["status"] = 4
            elif z["inside"] >= FILL_N:
                z["status"] = 3
            elif z["tier"] == 1 and z["inside"] >= WEAK_N:
                z["status"] = 2
            elif touched and z["status"] == 0:
                z["status"] = 1
        zones[:] = alive  # dead zones can't trade or nest any more

        for leg in ec.feed():
            stats["legs_5m"] += 1
            make_zones(leg, 0, t + CHART, j, t)
        if on_close is not None:
            on_close(j, zones, bc)
    stats["live"] = zones
    stats["atr"] = float(bc["atr"][-1])
    stats["close"] = float(bc["c"][-1])
    return trades, stats


# ───────────────────────── Reporting ─────────────────────────
def one_at_a_time(rows):
    out, busy = [], {}
    for r in sorted(rows, key=lambda x: x["entry_time"]):
        if r["entry_time"] >= busy.get(r["symbol"], 0):
            out.append(r)
            busy[r["symbol"]] = r["exit_time"]
    return out


def summarize(rows, boot=2000):
    if not rows:
        return None
    rows = sorted(rows, key=lambda x: x["exit_time"])
    r = np.array([x["net_r"] for x in rows])
    eq = np.cumsum(r)
    dd = float((np.maximum.accumulate(np.r_[0, eq]) - np.r_[0, eq]).max())
    gain, loss = r[r > 0].sum(), -r[r < 0].sum()
    rng = np.random.default_rng(7)
    means = r[rng.integers(0, len(r), (boot, len(r)))].mean(axis=1)
    return dict(n=len(r), win=float((r > 0).mean() * 100), avg=float(r.mean()), total=float(r.sum()),
                pf=float(gain / loss) if loss > 0 else float("inf"), dd=dd,
                lo=float(np.percentile(means, 2.5)), hi=float(np.percentile(means, 97.5)),
                risk=float(np.median([x["risk_pct"] for x in rows])))


HEAD = "| Set | Trades | Win % | Avg R | 95% range of Avg R | Total R | PF | Max DD (R) | Median stop % |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|"


def line(name, rows):
    s = summarize(rows)
    if not s:
        return f"| {name} | 0 | | | | | | | |"
    return (f"| {name} | {s['n']} | {s['win']:.1f} | {s['avg']:+.3f} | {s['lo']:+.3f} to {s['hi']:+.3f} | "
            f"{s['total']:+.1f} | {s['pf']:.2f} | {s['dd']:.1f} | {s['risk']:.2f} |")


def report(trades, stats, args):
    split, end = ms(args.split), ms(args.test_end)
    groups = ["5m A+", "5m nested (not A+)", "5m non-nested", "1H"]
    use = [x for x in trades if ms(args.trade_start) <= x["entry_time"] < end]
    train = [x for x in use if x["entry_time"] < split]
    test = [x for x in use if x["entry_time"] >= split]
    o = [f"# Nested LVN backtest: {', '.join(args.symbols)}", "",
         f"Train {args.trade_start} to {args.split}, test {args.split} to {args.test_end}. "
         f"Entry first touch of a FRESH zone, stop {args.atr_mult} x ATR beyond zone, target {args.rr}R, "
         f"cost {args.fee * 100:.3f}% fee + {args.slip * 100:.3f}% slippage per side. R is net of costs.", ""]
    for title, rows, f in (("All trades, bias-aligned", use, lambda x: x["aligned"]),
                           ("Train, bias-aligned", train, lambda x: x["aligned"]),
                           ("Test, bias-aligned", test, lambda x: x["aligned"]),
                           ("All trades, no bias filter", use, lambda x: True)):
        o += [f"## {title}", "", HEAD]
        for g in groups:
            o.append(line(g, [x for x in rows if f(x) and x["group"] == g]))
        o.append("")
    o += ["## Bias-aligned, one open trade at a time per symbol + set", "", HEAD]
    for g in groups:
        o.append(line(g, one_at_a_time([x for x in use if x["aligned"] and x["group"] == g])))
    o += ["", "## Bias-aligned breakdown", "", HEAD]
    for s in args.symbols:
        for g in groups:
            o.append(line(f"{s} {g}", [x for x in use if x["aligned"] and x["symbol"] == s and x["group"] == g]))
    for g in groups:
        for d in ("long", "short"):
            o.append(line(f"{g} {d}", [x for x in use if x["aligned"] and x["group"] == g and x["dir"] == d]))
    o += ["", "## Bias-aligned, 4H context filter", "", HEAD]
    for g in ("5m nested (not A+)", "5m non-nested", "1H"):
        for b, name in ((False, "not blocked"), (True, "blocked")):
            o.append(line(f"{g}, {name}", [x for x in use if x["aligned"] and x["group"] == g and x["blocked"] == b]))
    o += ["", "## Engine counts", ""]
    for s in args.symbols:
        o.append(f"- {s}: {stats[s]}")
    return "\n".join(o) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--symbols", nargs="+", default=["BTCUSDT", "ETHUSDT"], help="Binance perps, with or without .P")
    ap.add_argument("--data-start", default="2025-10-01", help="includes warm-up")
    ap.add_argument("--trade-start", default="2025-10-19")
    ap.add_argument("--split", default="2026-04-19")
    ap.add_argument("--test-end", default="2026-10-19", help="settings were tuned on ETH after this date")
    ap.add_argument("--data-end", default="2026-10-31")
    ap.add_argument("--rr", type=float, default=2.0)
    ap.add_argument("--atr-mult", type=float, default=0.5)
    ap.add_argument("--fee", type=float, default=0.0004)
    ap.add_argument("--slip", type=float, default=0.0001)
    ap.add_argument("--cache", default="cache")
    ap.add_argument("--out", default="backtest_1h5m")
    args = ap.parse_args()
    args.symbols = [s.upper().removesuffix(".P") for s in args.symbols]

    trades, stats = [], {}
    for s in args.symbols:
        print(f"{s}: loading", flush=True)
        m = load_1m(s, ms(args.data_start), ms(args.data_end), args.cache)
        print(f"{s}: {len(m['t'])} candles {stamp(m['t'][0])} to {stamp(m['t'][-1])}", flush=True)
        tr, st = run_symbol(s, m, args)
        trades += tr
        stats[s] = st
        print(f"{s}: {len(tr)} trades {st}", flush=True)

    trades.sort(key=lambda x: x["entry_time"])
    with open(args.out + "_trades.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["symbol", "group", "dir", "aligned", "entry_time", "exit_time", "entry", "sl", "tp", "exit", "reason", "gross_r", "net_r", "risk_pct"])
        for x in trades:
            w.writerow([x["symbol"], x["group"], x["dir"], x["aligned"], stamp(x["entry_time"]), stamp(x["exit_time"]),
                        x["entry"], x["sl"], x["tp"], x["exit"], x["reason"], round(x["gross_r"], 4), round(x["net_r"], 4), round(x["risk_pct"], 4)])
    text = report(trades, stats, args)
    with open(args.out + "_report.md", "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
