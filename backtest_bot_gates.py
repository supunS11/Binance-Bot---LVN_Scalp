#!/usr/bin/env python3
"""TP/SL backtest of the LIVE BOT's own entry logic, with fees. Do the confirmation gates help?

The bot code itself runs here: bot.watch.Watcher (touch, WAIT, SLOW, trend, LVN vs S/D choice, CHoCH / BOS,
absorption, delta shift, structure SL / TP, RR >= 2 after fees). Only the data source is different:
  - backtest.run_symbol runs once over the whole period; after every 5m close its zone state is turned into
    the same snapshot bot.zones.snapshot builds live (zones whose leg started in the last 21 days, the bot's
    data window; S/D freshness and the 1H / 4H trend as known at that close).
  - the Watcher gets the 1m candles one by one, never a candle after the one it is on.

Variants (all thresholds = the bot's config, fixed before the first run):
  A  bot as it runs live: CHoCH + at least 2 of 5 order flow gates. Liquidations and the order book are not in the
     cache, so those two gates always fail here: in the backtest A = 2 of (absorption, delta shift, CVD divergence).
  B  CHoCH only (no order flow gates)
  C  no confirmation: limit at the near edge at the touch (same WAIT / SLOW / trend / zone choice, same SL / TP rules)
  D  A without the 4H trend filter
  RR fixes (each = A with one change, settings fixed before the run):
  E  min RR 1.5 after fees (A: 2.0)
  F  target at the 1.272 extension of the pullback (leg extreme + 0.272 x (leg extreme - reaction extreme)),
     still cut in front of a fresh opposing zone
  G  retest entry: if RR at the CHoCH close is < 2, a limit at the broken CHoCH level instead (RR >= 2 at that
     price), valid 30 1m candles, cancelled if the target trades before the fill. RR >= 2 at the close = as A.
  Confirmation at the zone instead of CHoCH (stop / target as C: far edge + 0.5 ATR, leg extreme; first trigger
  within 30 min of the touch only; entry at the next 1m open, RR >= 2 after fees):
  Arming / touch rules (each = A with one change; M = all three):
  J  no "zone stop >= 0.30%" arming filter: the zone is armed, the plan widens the stop to 0.30%
  K  no WAIT (zones younger than 2 h are traded)
  L  1H trend direction only, STRONG not needed (4H filter kept)
  M  J + K + L
  H  rejection candle: first 1m close back beyond the near edge (long: close > near edge)
  I  order flow candle: a 1m candle inside the zone, close >= open (long), with 2 of 3: absorption on it, its own
     delta / volume >= +0.10, CVD divergence on the approach

    VARIANTS=ACEFG OUT=backtest_rr_fixes_report.md python backtest_bot_gates.py

Execution (= the paper executor): A / B / D fill at the next 1m open after the confirmation close, skipped if
RR at that price is < 2. C fills at the near edge (or the open if it gapped through). Stop first when stop and
target are inside one candle, a gap through the stop fills at the open, stop to entry + fees at 1.5R.
Fees 0.05% per side. One position per symbol per variant. Portfolio limits (max 3, daily loss) not applied.

    python backtest_bot_gates.py
"""
import collections
import multiprocessing as mp
import os
import types

import numpy as np

import backtest as bt
from backtest import MIN, add_indicators, load_1m, ms, resample, summarize
from backtest_lvn_reaction import DATA
from backtest_scalp_1h5m import strength

FIVE, DAY = 5 * MIN, 86_400_000
VARIANTS = tuple(os.environ.get("VARIANTS", "ABCD"))
OUT = os.environ.get("OUT", "backtest_bot_gates_report.md")
RETEST_MIN = 30
NAMES = {"J": "J: A without the zone stop >= 0.30% arming filter", "K": "K: A without WAIT 2 h",
         "L": "L: A with 1H direction only (no STRONG)", "M": "M: A with J + K + L", "H": "H: rejection candle at the zone (1m close back beyond the near edge)",
         "I": "I: order flow candle at the zone (2 of: absorption, delta flip, CVD divergence)", "E": "E: A with min RR 1.5", "F": "F: A with the target at the 1.272 extension",
         "G": "G: A, retest limit at the CHoCH level when RR at the close < 2","A": "A: bot as live (CHoCH + 2 of 5 order flow gates; liq / book not in data)", "B": "B: CHoCH only, no order flow gates",
         "C": "C: limit at the near edge, no confirmation", "D": "D: A without the 4H filter"}


def job(spec):
    sym, a, z, s0, s1 = spec
    from bot import config as C
    C.apply_script_defaults()
    from bot import journal, plan as P, watch as W, zones as Z
    from bot.zones import STATUS, _overlap, zone_key

    m = load_1m(sym, ms(a), ms(z), "cache")
    t, n = m["t"], len(m["t"])
    b1 = add_indicators(resample(m, 60 * MIN))
    b4 = add_indicators(resample(m, 240 * MIN))
    tr1, st1 = strength(b1)
    tr4, _ = strength(b4)
    window = C.DAYS_1M * DAY

    # ---------------- snapshot = bot.zones.snapshot, from the run_symbol state at this close
    sd_cache = {}

    def sd_state(zz, i_now):
        """(fresh, gone) of the zone's own S/D at i_now, from first-return / first-close-beyond indices."""
        key = id(zz)
        if key not in sd_cache:
            d = zz["dir"]
            top, bot = (float(x) for x in zz["sd"])
            i0 = int(np.searchsorted(t, zz["t0"]))
            i1 = min(n, int(np.searchsorted(t, zz["t0"] + window + DAY)))
            away = (m["l"][i0:i1] > top) if d == 1 else (m["h"][i0:i1] < bot)
            ret = n + 1
            if away.any():
                k = i0 + int(np.argmax(away)) + 1
                back = (m["l"][k:i1] <= top) if d == 1 else (m["h"][k:i1] >= bot)
                if back.any():
                    ret = k + int(np.argmax(back))
            bey = (m["c"][i0:i1] < bot) if d == 1 else (m["c"][i0:i1] > top)
            gone = i0 + int(np.argmax(bey)) if bey.any() else n + 1
            sd_cache[key] = (ret, gone)
        ret, gone = sd_cache[key]
        if gone < i_now:
            return None
        return ret >= i_now

    def snapshot(j, live, bc):
        now = int(bc["t"][j]) + FIVE
        i_now = int(np.searchsorted(t, now))
        px, atr = float(bc["c"][j]), float(bc["atr"][j])
        i1 = int(np.searchsorted(b1["tc"], now, side="right")) - 1
        i4 = int(np.searchsorted(b4["tc"], now, side="right")) - 1
        live = [zz for zz in live if zz["t0"] >= now - window]
        zones, obstacles = [], []
        parents = [o for o in live if o["tier"] == 1 and o["status"] < 3]
        for zz in live:
            d, tier = zz["dir"], zz["tier"]
            near, far = (zz["top"], zz["bot"]) if d == 1 else (zz["bot"], zz["top"])
            sd = sd_fresh = None
            if zz.get("sd") is not None:
                sd_top, sd_bot = (float(x) for x in zz["sd"])
                sd = dict(top=sd_top, bot=sd_bot, near=sd_top if d == 1 else sd_bot, far=sd_bot if d == 1 else sd_top)
                sd_fresh = sd_state(zz, i_now)
            if zz["status"] == 0:
                obstacles.append(dict(dir=d, near=float(near), kind=f"{('5m', '1H', '4H')[tier]} LVN"))
            if sd is not None and sd_fresh:
                obstacles.append(dict(dir=d, near=sd["near"], kind="S/D"))
            if tier == 2:
                continue
            parent = tier == 0 and any(o["dir"] == d and _overlap(zz, o) for o in parents)
            zones.append(dict(
                key=zone_key(sym, zz), sym=sym, tf=("5m", "1H")[tier], tier=tier, side="LONG" if d == 1 else "SHORT", dir=d,
                top=float(zz["top"]), bot=float(zz["bot"]), near=float(near), far=float(far),
                status=STATUS[zz["status"]], status_i=int(zz["status"]), nested=bool(zz["nested"]), parent=bool(parent),
                ratio=float(zz["ratio"]), made=int(zz["made"]), t0=int(zz["t0"]), ext=float(zz["ext"]),
                age_h=(now - zz["made"]) / 3_600_000, gap=None if zz["gap"] is None else float(zz["gap"]),
                sd=sd, sd_fresh=sd_fresh, stop_pct=(zz["top"] - zz["bot"] + C.SL_ATR * atr) / near * 100,
                dist_pct=(px - near) * d / px * 100, dist_atr=(px - near) * d / atr))
        ok = i1 >= 0 and i4 >= 0
        return dict(sym=sym, time=now, close=px, atr5=atr, trend1h=int(tr1[i1]) if ok else 0,
                    strong1h=bool(st1[i1]) if ok else False, trend4h=int(tr4[i4]) if ok else 0,
                    zones=zones, obstacles=obstacles)

    # ---------------- the bot's watch code, with per-variant gates and a journal collector
    events = {v: [] for v in VARIANTS}
    cur = dict(v="A", t=0)
    raw = {v: [] for v in VARIANTS}

    def jw(event, **row):
        events[cur["v"]].append((cur["t"], event, _why(row), (row.get("zone") or {}).get("key")))
        if event == "CONFIRM_REJECT":
            raw[cur["v"]].append((cur["t"], "; ".join(row.get("why") or [])))

    journal.write = jw
    W.now_ms = lambda: 0
    flow = types.SimpleNamespace(liquidations=lambda *a: {"SELL": 0.0, "BUY": 0.0}, imbalance=lambda *a: None)
    orig_trend, orig_abs, orig_shift = Z.trend_ok, W.absorption, W.delta_shift

    def trend_no4h(snap, d):
        return [w for w in orig_trend(snap, d) if "4H" not in w]

    def trend_no_strong(snap, d):
        return [w for w in orig_trend(snap, d) if "STRONG" not in w]

    orig_plan, holder = W.make_plan, dict(level=None)

    def plan_retest(d, entry, *rest):
        p, why = orig_plan(d, entry, *rest)
        lvl = holder["level"]
        if p or lvl is None or not why.startswith("RR"):
            return p, why
        p2, _ = orig_plan(d, lvl, *rest)
        return (dict(p2, retest=True), None) if p2 else (None, why)

    class RetestWatcher(W.Watcher):
        def _confirm(self, w, k, mark):
            holder["level"] = w["react"].level
            try:
                return super()._confirm(w, k, mark)
            finally:
                holder["level"] = None

    gates = dict(A=(orig_trend, orig_abs, orig_shift), E=(orig_trend, orig_abs, orig_shift),
                 F=(orig_trend, orig_abs, orig_shift), G=(orig_trend, orig_abs, orig_shift),
                 H=(orig_trend, orig_abs, orig_shift), I=(orig_trend, orig_abs, orig_shift),
                 J=(orig_trend, orig_abs, orig_shift), K=(orig_trend, orig_abs, orig_shift),
                 L=(trend_no_strong, orig_abs, orig_shift), M=(trend_no_strong, orig_abs, orig_shift),
                 B=(orig_trend, lambda m_, i0, i1, *a: i1, lambda *a: (True, 0.0, 0.0)),
                 C=(orig_trend, orig_abs, orig_shift),
                 D=(trend_no4h, orig_abs, orig_shift))

    class Store:
        pass

    store = Store()
    store.sym = sym
    warm = int(np.searchsorted(t, ms(a) + 2 * DAY))
    store.m = {k: v[:warm] for k, v in m.items()}

    class LimitWatcher(W.Watcher):
        """C: at the touch (after the same WAIT / SLOW / trend / zone choice) a limit at the near edge."""

        def _step(self, w, k):
            mm, d = self.store.m, w["dir"]
            o = float(mm["o"][k])
            entry = min(w["near"], o) if d == 1 else max(w["near"], o)
            plan, why = P.make_plan(d, entry, w["far"], w["far"], self.snap["atr5"], w["leg_ext"], self.snap["obstacles"])
            if why:
                journal.write("CONFIRM_REJECT", why=[why])
                self._end(w, "limit: plan rejected")
                return None
            self._end(w, "SIGNAL")
            return dict(sym=self.sym, dir=d, key=w["key"], kind=w["kind"], t=int(mm["t"][k]) + MIN, k_fill=k, **plan)

    from bot.orderflow import absorption as of_abs, delta_frac

    class ZoneConfirmWatcher(W.Watcher):
        """H / I: a confirmation candle at the zone within 30 min of the touch, no CHoCH."""
        mode = "H"

        def _step(self, w, k):
            mm, d = self.store.m, w["dir"]
            tk, h, l, c, o = int(mm["t"][k]), mm["h"][k], mm["l"][k], mm["c"][k], mm["o"][k]
            if tk - w["t_touch"] >= 30 * MIN:
                self._end(w, "no confirmation within 30 min of the touch")
                return None
            if (c < w["far"]) if d == 1 else (c > w["far"]):
                self._end(w, "1m close beyond the far edge (zone failed)")
                return None
            if (h >= w["leg_ext"]) if d == 1 else (l <= w["leg_ext"]):
                self._end(w, "price reached the leg extreme before a confirmation")
                return None
            if self.mode == "H":
                ok = (c > w["near"]) if d == 1 else (c < w["near"])
            else:
                inside = l <= w["top"] and h >= w["bot"]
                body = (c >= o) if d == 1 else (c <= o)
                votes = [of_abs(mm, k, k, w["top"], w["bot"], d) is not None,
                         d * delta_frac(mm, k) >= C.FLIP_DELTA, bool(w["cvd_div"])]
                ok = inside and body and sum(votes) >= 2
            if not ok or W.trend_ok(self.snap, d):
                return None
            journal.write("MARK", mark=self.mode)
            plan, why = P.make_plan(d, float(c), w["far"], w["far"], self.snap["atr5"], w["leg_ext"], self.snap["obstacles"])
            if why:
                journal.write("CONFIRM_REJECT", why=[why])
                self._end(w, "confirmation candle, plan rejected")
                return None
            self._end(w, "SIGNAL")
            return dict(sym=self.sym, dir=d, key=w["key"], kind=w["kind"], t=tk + MIN, **plan)

    class HWatcher(ZoneConfirmWatcher):
        mode = "H"

    class IWatcher(ZoneConfirmWatcher):
        mode = "I"

    watchers = {}
    for v in VARIANTS:
        cur["v"] = v
        wt = dict(C=LimitWatcher, G=RetestWatcher, H=HWatcher, I=IWatcher).get(v, W.Watcher)(store, flow)
        wt.warmup()
        watchers[v] = wt
    signals = {v: [] for v in VARIANTS}

    of_min, base_rr, base_age = C.OF_MIN_PASS, C.MIN_RR, C.MIN_AGE_H

    def set_gates(v):
        tr, ab, sh = gates[v]
        Z.trend_ok = W.trend_ok = tr
        W.absorption, W.delta_shift = ab, sh
        C.OF_MIN_PASS = 0 if v == "B" else of_min
        C.MIN_RR = 1.5 if v == "E" else base_rr
        C.TP_EXT = 0.272 if v == "F" else 0.0
        C.ARM_MIN_STOP = v not in ("J", "M")
        C.MIN_AGE_H = 0.0 if v in ("K", "M") else base_age
        W.make_plan = plan_retest if v == "G" else orig_plan
        cur["v"] = v

    def on_close(j, live, bc):
        now = int(bc["t"][j]) + FIVE
        if now < t[warm - 1] + MIN or not bc["atr"][j] > 0:
            return
        cur["t"] = now
        snap = snapshot(j, live, bc)
        end = int(np.searchsorted(t, now + FIVE))
        for v in VARIANTS:
            set_gates(v)
            wt = watchers[v]
            store.m = {k: x[:int(np.searchsorted(t, now))] for k, x in m.items()}
            wt.on_snapshot(snap)
            store.m = {k: x[:end] for k, x in m.items()}
            for s in wt.on_candles():
                signals[v].append(s)

    bt.run_symbol(sym, m, types.SimpleNamespace(fee=C.FEE, slip=0.0, rr=2.0, atr_mult=C.SL_ATR), on_close)
    set_gates("A")

    # ---------------- execution (= PaperExecutor rules) and results
    lo, hi, split = ms(s0), ms(s1), (ms(s0) + ms(s1)) // 2
    out = {}
    for v in VARIANTS:
        trades, skips, busy_until = [], collections.Counter(), 0
        for s in sorted(signals[v], key=lambda s: s["t"]):
            if not lo <= s["t"] < hi:
                continue
            if s["t"] < busy_until:
                skips["position already open on the symbol"] += 1
                continue
            d = s["dir"]
            set_gates(v)  # MIN_RR / TP_EXT of this variant for the checks below
            if s.get("retest"):
                k0, k, entry = int(np.searchsorted(t, s["t"])), None, s["entry"]
                for i in range(k0, min(n, k0 + RETEST_MIN)):
                    if (m["l"][i] <= entry) if d == 1 else (m["h"][i] >= entry):
                        k = i
                        break
                    if (m["h"][i] >= s["tp"]) if d == 1 else (m["l"][i] <= s["tp"]):
                        break
                if k is None:
                    skips["retest limit not filled (30 min or target first)"] += 1
                    continue
                o_k = float(m["o"][k])
                entry = min(entry, o_k) if d == 1 else max(entry, o_k)
            elif v == "C":
                k, entry = s["k_fill"], s["entry"]
            else:
                k = int(np.searchsorted(t, s["t"]))  # next candle after the confirmation close
                if k >= n:
                    continue
                entry = float(m["o"][k])
                if (entry - s["sl"]) * d <= 0 or (s["tp"] - entry) * d <= 0 or P.rr_net(entry, s["sl"], s["tp"]) < C.MIN_RR:
                    skips["RR < 2 at the fill price"] += 1
                    continue
            r = exit_sim(m, k, d, entry, s["sl"], s["tp"], C, limit=v == "C" or bool(s.get("retest")))
            if r is None:
                skips["still open at the end of the data"] += 1
                continue
            xk, px, why = r
            risk = abs(entry - s["sl"])
            gross = (px - entry) * d / risk
            net = gross - (entry + px) * C.FEE / risk
            busy_until = int(t[xk]) + MIN
            trades.append(dict(sym=sym, period=s0[:4], late=s["t"] >= split, entry_time=int(t[k]), exit_time=int(t[xk]),
                               net_r=net, gross_r=gross, reason=why, kind=s["kind"], tp_kind=s.get("tp_kind"),
                               retest=bool(s.get("retest")), risk_pct=risk / entry * 100, hold_min=(int(t[xk]) - int(t[k])) / MIN))
        ev = [(e, w, key) for tt, e, w, key in events[v] if lo <= tt < hi]
        out[v] = dict(trades=trades, skips=skips, events=ev, rejects=[w for tt, w in raw[v] if lo <= tt < hi])
    print(sym, s0[:4], {v: len(out[v]["trades"]) for v in VARIANTS}, flush=True)
    return dict(sym=sym, period=s0[:4], days=(hi - lo) / DAY, out=out)


def _why(row):
    w = row.get("why") or row.get("reason") or ""
    if isinstance(w, list):
        w = "; ".join(w)
    w = str(w)
    for cut in (" (", ":"):  # group by the reason, not by the numbers
        if cut in w and not w.startswith("WAIT") and not w.startswith("SLOW"):
            w = w.split(cut)[0]
    if w.startswith("WAIT"):
        w = "WAIT: zone younger than 2 h"
    if w.startswith("SLOW"):
        w = "SLOW approach (<= 2 ATR in 30 min)"
    if w.startswith("zone stop"):
        w = "zone stop < 0.30% (moves with the 5m ATR)"
    if w.startswith("RR "):
        w = "RR < 2 after fees"
    return w


def exit_sim(m, k, d, entry, sl, tp, C, limit=False):
    """PaperExecutor.on_candles from candle k on. Returns (exit index, price, reason) or None.
    limit=True: candle k is the limit fill candle; only its stop counts (its high / low may come before the fill)."""
    be = False
    risk = abs(entry - sl)
    o, h, l = m["o"], m["h"], m["l"]
    for i in range(k, len(m["t"])):
        if (l[i] <= sl) if d == 1 else (h[i] >= sl):
            px = (min(sl, o[i]) if d == 1 else max(sl, o[i])) if i > k else sl
            return i, float(px), "BREAK-EVEN" if be else "STOP"
        if limit and i == k:
            continue
        if (h[i] >= tp) if d == 1 else (l[i] <= tp):
            return i, float(tp), "TARGET"
        if C.BE_AT_R and not be and ((h[i] - entry) if d == 1 else (entry - l[i])) >= C.BE_AT_R * risk:
            sl, be = entry * (1 + d * 2 * C.FEE), True
    return None


def row(name, tr, days_coin):
    s = summarize(tr)
    if not s:
        return f"| {name} | 0 | | | | | | | | |"
    be = sum(x["reason"] == "BREAK-EVEN" for x in tr) / len(tr) * 100
    return (f"| {name} | {s['n']} | {s['n'] / days_coin:.2f} | {s['win']:.1f} | {be:.0f} | {s['avg']:+.3f} | "
            f"{s['lo']:+.3f} to {s['hi']:+.3f} | {s['total']:+.1f} | {s['dd']:.1f} | {s['risk']:.2f} |")


def main():
    with mp.Pool(4, maxtasksperchild=1) as p:
        res = p.map(job, DATA, chunksize=1)
    new = [r for r in res if r["period"] == "2025"]
    old = [r for r in res if r["period"] == "2024"]
    dn, do = sum(r["days"] for r in new), sum(r["days"] for r in old)
    o = ["# Live bot entry logic, TP/SL backtest with fees", "",
         "BTC, ETH, SOL, XRP, 2025-10-19 to 2026-10-19; 2024-25 = BTC, ETH, 2024-10-19 to 2025-10-19.",
         "The bot's own Watcher code on replayed data; thresholds = bot config, fixed before the run. Fees 0.05% per side.",
         "Stop first inside one candle; stop to entry + fees at 1.5R. One position per symbol. Win = net R > 0.", "",
         "| Set | Trades | Per coin per day | Win % | Break-even exits % | Avg net R | 95% range | Total R | Max DD (R) | Median stop % |",
         "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for v in VARIANTS:
        tn = [x for r in new for x in r["out"][v]["trades"]]
        to = [x for r in old for x in r["out"][v]["trades"]]
        o.append(row(f"**{NAMES[v]}**, 2025-26", tn, dn))
        o.append(row("  1st half", [x for x in tn if not x["late"]], dn / 2))
        o.append(row("  2nd half", [x for x in tn if x["late"]], dn / 2))
        o.append(row("  2024-25 (BTC, ETH)", to, do))
    o += ["", "## Per coin, 2025-26", "", "| Set | Coin | Trades | Avg net R | Total R |", "|---|---|---:|---:|---:|"]
    for v in VARIANTS:
        for r in new:
            tr = r["out"][v]["trades"]
            o.append(f"| {v} | {r['sym']} | {len(tr)} | {np.mean([x['net_r'] for x in tr]) if tr else float('nan'):+.3f} | "
                     f"{sum(x['net_r'] for x in tr):+.1f} |")
    for v in VARIANTS:
        o += ["", f"## Funnel {NAMES[v]}, 2025-26 (all 4 coins)", ""]
        c, keys = collections.Counter(), set()
        for r in new:
            for e, w, key in r["out"][v]["events"]:
                if e == "ARMED":
                    keys.add(key)
                c[(e, w)] += 1
            for w, k in r["out"][v]["skips"].items():
                c[("ENTRY_SKIP", w)] += k
        o.append(f"- Zones armed (unique): {len(keys)}; arm events {c[('ARMED', '')]} (a zone re-arms after a disarm)")
        for e in ("DISARMED", "TOUCH_SKIP", "WATCH_START", "MARK", "CONFIRM_REJECT", "WATCH_END", "ENTRY_SKIP"):
            items = sorted(((w, k) for (ee, w), k in c.items() if ee == e), key=lambda x: -x[1])
            tot = sum(k for _, k in items)
            o.append(f"- {e}: {tot}")
            for w, k in items[:8]:
                if w:
                    o.append(f"  - {k} {w}")
        tn = [x for r in new for x in r["out"][v]["trades"]]
        o.append(f"- Trades: {len(tn)} (exits: {dict(collections.Counter(x['reason'] for x in tn))}, "
                 f"median hold {np.median([x['hold_min'] for x in tn]) if tn else float('nan'):.0f} min)")
    o += ["", "## Every CONFIRM_REJECT (all coins, both periods)", ""]
    for v in VARIANTS:
        for r in res:
            for w in r["out"][v]["rejects"]:
                o.append(f"- {v} {r['sym']} {r['period']}: {w}")
    text = "\n".join(o) + "\n"
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
