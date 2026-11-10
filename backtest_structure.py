#!/usr/bin/env python3
"""Python port of Structure_Entry_15m.pine, script defaults only.

Long only when 4H and 15m are both up, short only when both are down (same swing + BOS + protected swing rules).
Swings on 4H, 15m and 1m: a high or low counts once price moved away from it by 3 x that timeframe's ATR(14).

Fixed before running:
- Entry: next 1m open after the first 15m candle closing in the trend direction once the 1m chart confirmed.
- Stop: pullback extreme + 0.1 x ATR(15m). Target the prior extreme (HH / LL). One entry per pullback. Costs 0.05% per side. Within a 1m candle the stop hits first.
- Pass: Avg R > 0 and the low end of its 95% range > 0.

    python backtest_structure.py
    python backtest_structure.py --replay LINKUSDT 2026-10-29 2026-11-02
"""
import argparse

from backtest import MIN, add_indicators, load_1m, ms, resample, simulate_exit, stamp, summarize

HTF = 15 * MIN
SWING_ATR, LTF_ATR, MIN_PB, SL_BUF, COST = 3.0, 3.0, 0.30, 0.10, 0.0005
DATA = (("BTCUSDT", "2025-10-01", "2026-10-31"), ("ETHUSDT", "2025-10-01", "2026-10-31"),
        ("SOLUSDT", "2025-10-01", "2026-10-19"), ("XRPUSDT", "2025-10-01", "2026-10-19"))
START, END = "2025-10-19", "2026-10-19"
MODES = ("BOS after CHoCH", "CHoCH")
# confirmation, one entry per pullback, min RR
VARIANTS = (("BOS after CHoCH", True, 0.0), ("BOS after CHoCH", False, 0.0), ("CHoCH", True, 0.0))


class Direction:
    """Swing + BOS + protected swing trend on closed higher TF bars."""

    def __init__(self, b):
        self.h, self.l, self.c, self.a = b["hL"], b["lL"], b["cL"], b["atrL"]
        self.tc = b["tc"].tolist()
        self.n, self.trend, self.dir, self.ext, self.i = 0, 0, 1, None, 0
        self.sw_h = self.sw_l = self.prot_l = self.prot_h = None
        self.h_i = self.l_i = self.prot_i = 0
        self.h_brk = self.l_brk = True

    def update(self, now):
        h, l = self.h, self.l
        while self.n < len(self.tc) and self.tc[self.n] <= now:
            n, cl, a = self.n, self.c[self.n], self.a[self.n]
            if self.ext is None:
                self.ext, self.i = h[n], n
            elif a == a:
                if self.dir == 1:
                    if h[n] > self.ext:
                        self.ext, self.i = h[n], n
                    elif self.ext - l[n] >= SWING_ATR * a:
                        self.sw_h, self.h_i, self.h_brk = self.ext, self.i, False
                        self.dir, self.ext, self.i = -1, l[n], n
                else:
                    if l[n] < self.ext:
                        self.ext, self.i = l[n], n
                    elif h[n] - self.ext >= SWING_ATR * a:
                        self.sw_l, self.l_i, self.l_brk = self.ext, self.i, False
                        self.dir, self.ext, self.i = 1, h[n], n
            if not self.h_brk and cl > self.sw_h:
                self.h_brk = True
                if self.trend >= 0:
                    self.prot_i = min(range(self.h_i, n + 1), key=lambda k: l[k])
                    self.prot_l, self.trend = l[self.prot_i], 1
            if not self.l_brk and cl < self.sw_l:
                self.l_brk = True
                if self.trend <= 0:
                    self.prot_i = max(range(self.l_i, n + 1), key=lambda k: h[k])
                    self.prot_h, self.trend = h[self.prot_i], -1
            if self.trend == 1 and self.prot_l is not None and cl < self.prot_l:
                self.prot_i = max(range(self.prot_i, n + 1), key=lambda k: h[k])
                self.prot_h, self.trend, self.l_brk = h[self.prot_i], -1, True
            elif self.trend == -1 and self.prot_h is not None and cl > self.prot_h:
                self.prot_i = min(range(self.prot_i, n + 1), key=lambda k: l[k])
                self.prot_l, self.trend, self.h_brk = l[self.prot_i], 1, True
            self.n += 1


class Side:
    def __init__(self, mode, one=True):
        self.mode, self.ext, self.t_ext, self.pb, self.pend, self.dead = mode, None, 0, None, None, False
        self.one, self.entered = one, False
        self.clear()

    def clear(self):
        self.lh = self.ref = self.last = self.bos = self.sig_pb = None
        self.t_lh = self.t_last = self.t_choch = 0
        self.fired = self.choch = False

    def step(self, active, t, hi, lo, cl, ph, t_ph, pl, t_pl, prot):
        if not active:
            self.ext = self.pb = self.pend = None
            self.dead = self.entered = False
            self.clear()
            return None
        if self.ext is None or hi > self.ext:
            self.ext, self.t_ext, self.pb, self.dead = hi, t, None, False
            self.pend, self.entered = None, False
            self.clear()
            return None
        self.pb = lo if self.pb is None else min(self.pb, lo)
        if self.fired and lo < self.sig_pb and not (self.one and self.entered):
            self.fired, self.choch, self.t_choch, self.bos = False, False, 0, None
        if pl is not None and t_pl > self.t_ext:
            self.last, self.t_last = pl, t_pl
        if ph is not None and t_ph > self.t_ext and ph < self.ext:
            self.lh, self.t_lh, self.ref = ph, t_ph, self.last
            if self.choch and t_ph > self.t_choch:
                self.bos = ph
        if prot is None:
            self.dead = True
        if self.dead or self.fired:
            return None
        sig = None
        if self.choch:
            if self.bos is not None and cl > self.bos:
                sig = self.pb
        elif (self.ext - self.pb) / (self.ext - prot) >= MIN_PB and self.lh is not None and self.last is not None \
                and self.t_last > self.t_lh and (self.ref is None or self.last < self.ref) and cl > self.lh:
            if self.mode == "CHoCH":
                sig = self.pb
            else:
                self.choch, self.t_choch = True, t
        if sig is not None:
            self.fired, self.sig_pb = True, sig
        return sig


def run(sym, m, mode, log=None, one=True, min_rr=0.0):
    b = add_indicators(resample(m, HTF))
    ctx = Direction(add_indicators(resample(m, 240 * MIN)))
    ctx_last = 0
    hH, hL, hC, hA, hTc = b["hL"], b["lL"], b["cL"], b["atrL"], b["tc"].tolist()
    t, o, h, l, c = m["t"].tolist(), m["o"].tolist(), m["h"].tolist(), m["l"].tolist(), m["c"].tolist()
    long_s, short_s = Side(mode, one), Side(mode, one)
    trend, sw_h, sw_l, h_i, l_i, h_brk, l_brk, prot_l, prot_h, prot_i, atr, n = 0, None, None, 0, 0, True, True, None, None, 0, None, 0
    zz_dir, zz_ext, zz_i = 1, None, 0
    lz_dir, lz_ext, lz_t, l_atr, l_sum = 1, None, 0, None, 0.0
    out = []

    def note(i, text):
        if log is not None:
            log.append((t[i], text))

    for i in range(len(t)):
        ctx.update(t[i])
        if ctx.trend != ctx_last:
            ctx_last = ctx.trend
            note(i, f"4H trend {'UP' if ctx_last == 1 else 'DOWN'}")
        while n < len(hTc) and hTc[n] <= t[i]:
            cl, a_now = hC[n], hA[n]
            if zz_ext is None:
                zz_ext, zz_i = hH[n], n
            elif a_now == a_now:
                if zz_dir == 1:
                    if hH[n] > zz_ext:
                        zz_ext, zz_i = hH[n], n
                    elif zz_ext - hL[n] >= SWING_ATR * a_now:
                        note(i, f"15m swing high {zz_ext}")
                        sw_h, h_i, h_brk = zz_ext, zz_i, False
                        zz_dir, zz_ext, zz_i = -1, hL[n], n
                else:
                    if hL[n] < zz_ext:
                        zz_ext, zz_i = hL[n], n
                    elif hH[n] - zz_ext >= SWING_ATR * a_now:
                        note(i, f"15m swing low {zz_ext}")
                        sw_l, l_i, l_brk = zz_ext, zz_i, False
                        zz_dir, zz_ext, zz_i = 1, hH[n], n
            if not h_brk and cl > sw_h:
                h_brk = True
                if trend >= 0:
                    prot_i = min(range(h_i, n + 1), key=lambda k: hL[k])
                    prot_l, trend = hL[prot_i], 1
                    note(i, f"15m BOS up, protected low {prot_l}")
            if not l_brk and cl < sw_l:
                l_brk = True
                if trend <= 0:
                    prot_i = max(range(l_i, n + 1), key=lambda k: hH[k])
                    prot_h, trend = hH[prot_i], -1
                    note(i, f"15m BOS down, protected high {prot_h}")
            if trend == 1 and prot_l is not None and cl < prot_l:
                prot_i = max(range(prot_i, n + 1), key=lambda k: hH[k])
                prot_h, trend, l_brk = hH[prot_i], -1, True
                note(i, f"TREND DOWN, protected high {prot_h}")
            elif trend == -1 and prot_h is not None and cl > prot_h:
                prot_i = min(range(prot_i, n + 1), key=lambda k: hL[k])
                prot_l, trend, h_brk = hL[prot_i], 1, True
                note(i, f"TREND UP, protected low {prot_l}")
            atr = hA[n]
            n += 1
        tr = h[i] - l[i] if i == 0 else max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))
        if i < 14:
            l_sum += tr
            if i == 13:
                l_atr = l_sum / 14
        else:
            l_atr = (l_atr * 13 + tr) / 14
        ph = pl = None
        tp = 0
        if lz_ext is None:
            lz_ext, lz_t = h[i], t[i]
        elif l_atr is not None:
            if lz_dir == 1:
                if h[i] > lz_ext:
                    lz_ext, lz_t = h[i], t[i]
                elif lz_ext - l[i] >= LTF_ATR * l_atr:
                    ph, tp = lz_ext, lz_t
                    lz_dir, lz_ext, lz_t = -1, l[i], t[i]
            else:
                if l[i] < lz_ext:
                    lz_ext, lz_t = l[i], t[i]
                elif h[i] - lz_ext >= LTF_ATR * l_atr:
                    pl, tp = lz_ext, lz_t
                    lz_dir, lz_ext, lz_t = 1, h[i], t[i]
        s_l = long_s.step(trend == 1 and ctx.trend == 1, t[i], h[i], l[i], c[i], ph, tp, pl, tp, prot_l)
        s_s = short_s.step(trend == -1 and ctx.trend == -1, t[i], -l[i], -h[i], -c[i], None if pl is None else -pl, tp, None if ph is None else -ph, tp, None if prot_h is None else -prot_h)
        htf_end = (t[i] + MIN) % HTF == 0
        cur_open = o[next(k for k in range(i, -1, -1) if t[k] % HTF == 0 or k == 0)] if htf_end else None
        for d, side, sig, lo, cl in ((1, long_s, s_l, l[i], c[i]), (-1, short_s, s_s, -h[i], -c[i])):
            if side.pend is not None and lo < side.pend:
                side.pend = None
            if sig is not None:
                side.pend = sig
                note(i, f"{'long' if d == 1 else 'short'} 1m {mode} confirmed, close {c[i]}")
            if side.pend is None or not htf_end or cl <= d * cur_open:
                continue
            pend, side.pend = side.pend, None
            if atr is None or atr != atr or i + 1 >= len(t):
                continue
            sl, tgt = d * (pend - SL_BUF * atr), d * side.ext
            if (c[i] - sl) * d <= 0 or (tgt - c[i]) * d <= 0 or (tgt - c[i]) * d < min_rr * (c[i] - sl) * d:
                continue
            side.entered = True
            note(i, f"{'LONG' if d == 1 else 'SHORT'} entry on 15m close {c[i]}, SL {sl:.3f}, TP {tgt}")
            entry = o[i + 1]
            risk = (entry - sl) * d
            if risk <= 0 or (tgt - entry) * d <= 0:
                continue
            ex = simulate_exit(m, i + 1, d, entry, sl, tgt)
            if ex is None:
                continue
            xi, px, _ = ex
            out.append(dict(symbol=sym, dir=d, entry_time=t[i + 1], exit_time=t[xi], risk_pct=risk / entry * 100,
                            gross=(px - entry) * d / risk, net_r=(px - entry) * d / risk - (entry + px) * COST / risk))
    return out


HEAD = "| Confirmation | Set | Trades | Win % | Avg R | 95% range | Total R | Max DD (R) | Median stop % | Avg R before costs |\n|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"


def row(mode, name, rows):
    s = summarize(rows)
    if not s:
        return f"| {mode} | {name} | 0 | | | | | | | |"
    gross = sum(r["gross"] for r in rows) / len(rows)
    return f"| {mode} | {name} | {s['n']} | {s['win']:.1f} | {s['avg']:+.3f} | {s['lo']:+.3f} to {s['hi']:+.3f} | {s['total']:+.1f} | {s['dd']:.1f} | {s['risk']:.2f} | {gross:+.3f} |"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cache", default="cache")
    ap.add_argument("--out", default="backtest_structure_report.md")
    ap.add_argument("--replay", nargs=3, metavar=("SYMBOL", "FROM", "TO"), help="print the event log for one symbol")
    ap.add_argument("--replay-tail", type=int, default=30)
    args = ap.parse_args()
    if args.replay:
        sym, a, z = args.replay
        m = load_1m(sym, ms(a), ms(z), args.cache)
        for mode in MODES:
            log = []
            run(sym, m, mode, log)
            print("==", mode, "data to", stamp(m["t"][-1]))
            for when, text in log[-args.replay_tail:]:
                print(stamp(when), text)
        return
    o = [f"# Structure entry 15m/1m, {START} to {END}", "", HEAD]
    for mode, one, min_rr in VARIANTS:
        rows = []
        for sym, a, z in DATA:
            m = load_1m(sym, ms(a), ms(z), args.cache)
            rows += [r for r in run(sym, m, mode, None, one, min_rr) if ms(START) <= r["entry_time"] < ms(END)]
            print(mode, one, min_rr, sym, len(rows), flush=True)
        name = f"{mode}, {'one entry' if one else 'repeat entries'}, min RR {min_rr}"
        o.append(row(name, "all", rows))
        for sym, _, _ in DATA:
            o.append(row(name, sym, [r for r in rows if r["symbol"] == sym]))
    text = "\n".join(o) + "\n"
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
