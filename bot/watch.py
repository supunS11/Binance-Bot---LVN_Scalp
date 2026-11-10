"""Zone watch: from a valid FRESH LVN to an entry signal. One Watcher per symbol.

ARMED     after each 5m close, a 5m LVN is armed when it passes every script filter (bot.zones.entry_zone_why):
          FRESH, NESTED in a live 1H LVN, 1H trend STRONG in its direction, 4H on the same side, zone stop
          >= 0.30%, price still on the entry side. LVNs > 3 ATR from their own S/D are already dropped by the engine.
TOUCH     first 1m candle that reaches the near edge. The zone is used up from here (tested zones are never
          used again), whatever happens next. At the touch:
            - WAIT: zone younger than 2 h -> no trade.
            - SLOW: price travelled <= 2 ATR toward the zone in the last 30 min -> no trade (held 26.8% vs 38.2%).
            - Which zone (point of interest, POI):
                LVN far edge within 1 x 5m ATR of its fresh S/D zone (or overlapping) -> ONE merged zone, from the
                  LVN near edge to the S/D distal line. A probe through the LVN into the S/D is not a failure.
                S/D further away -> the LVN alone. If it fails, its fresh S/D is watched next (fallback).
WATCH     every closed 1m candle, until one of:
            - 1m close beyond the POI far edge -> failed (the "broke" rule of the tests).
            - price reaches the leg extreme first -> the move left without us.
            - the engine marks the zone FILLED / BROKEN / LEG INVALID.
            - CONFIRMATION (CHoCH by default, see bot.structure) -> gates:
                trend still OK, ABSORPTION at the zone, DELTA SHIFT (bot.orderflow), RR >= 2 after fees (bot.plan).
              All pass -> SIGNAL. Any fails -> logged, keep watching for the next mark (BOS); after BOS -> ended.
"""
import logging
import time

import numpy as np

from bot import config as C
from bot import journal
from bot.config import MIN
from bot.market import now_ms
from bot.orderflow import absorption, cvd_divergence, delta_shift
from bot.plan import make_plan
from bot.structure import LtfSwings, React
from bot.zones import entry_zone_why, trend_ok

log = logging.getLogger("bot.watch")
NEED = {"CHOCH": 1, "BOS": 2}


def _px(x):
    return float(f"{x:.6g}")


class Watcher:
    def __init__(self, store, flow):
        self.store, self.flow = store, flow
        self.sym = store.sym
        self.swings = LtfSwings()
        self.t_last = None  # open time of the last 1m candle processed
        self.snap = None
        self.armed = {}  # zone key -> zone (from the last snapshot)
        self.watches = {}  # watch key -> watch dict
        self.pending = {}  # fallback S/D zones waiting for their touch: key -> poi dict
        self.done = set()  # keys of zones / POIs already used (touched once)

    # ------------------------------------------------------------ state
    def warmup(self):
        """Builds the 1m swings over all stored candles (the Pine script does the same over its intrabars)."""
        m = self.store.m
        for k in range(len(m["t"])):
            self.swings.feed(int(m["t"][k]), m["h"][k], m["l"][k], m["c"][k])
        self.t_last = int(m["t"][-1])

    def to_state(self):
        ws = []
        for w in self.watches.values():
            x = dict(w)
            x["react"] = w["react"].to_dict()
            ws.append(x)
        return dict(done=sorted(self.done), watches=ws, pending=list(self.pending.values()))

    def load_state(self, s):
        cut = int(time.time() * 1000) - 40 * 86_400_000
        self.done = {k for k in s.get("done", []) if int(k.split("|")[3]) >= cut}
        for x in s.get("watches", []):
            x["react"] = React.from_dict(x["react"])
            self.watches[x["key"]] = x
        self.pending = {p["key"]: p for p in s.get("pending", [])}

    # ------------------------------------------------------------ 5m close
    def on_snapshot(self, snap):
        self.snap = snap
        new = {}
        by_key = {z["key"]: z for z in snap["zones"]}
        for z in snap["zones"]:
            k = z["key"]
            if k in self.done or k in self.watches or z["tier"] != 0:
                continue
            why = entry_zone_why(snap, z)
            if not why:
                new[k] = z
                if k not in self.armed:
                    log.info("%s ARMED %s %s %s-%s nested=%s", self.sym, z["side"], z["tf"], _px(z["bot"]), _px(z["top"]), z["nested"])
                    journal.write("ARMED", sym=self.sym, zone=_zone_row(z))
            elif k in self.armed:
                journal.write("DISARMED", sym=self.sym, zone=_zone_row(z), why=why)
        for k in self.armed:
            if k not in new and k not in by_key and k not in self.watches and k not in self.done:
                journal.write("DISARMED", sym=self.sym, key=k, why=["zone removed by the engine"])
        self.armed = new
        for w in list(self.watches.values()):
            if w["kind"] == "S/D":
                continue
            z = by_key.get(w["zone_key"])
            if z is None:
                self._end(w, "zone FILLED / removed by the engine")
            elif z["status_i"] >= 4:
                self._end(w, f"zone {z['status']}")
        now = snap["time"]
        for k, p in list(self.pending.items()):
            if now - p["since"] > 24 * 3_600_000:
                self.pending.pop(k)
                self.done.add(k)
                journal.write("WATCH_END", sym=self.sym, key=k, kind="S/D", why="fallback S/D not reached within 24 h")

    # ------------------------------------------------------------ 1m close
    def on_candles(self):
        """Processes every closed 1m candle not seen yet. Returns the entry signals."""
        m = self.store.m
        t = m["t"]
        k0 = int(np.searchsorted(t, self.t_last, side="right")) if self.t_last is not None else len(t) - 1
        out = []
        for k in range(k0, len(t)):
            self.swings.feed(int(t[k]), m["h"][k], m["l"][k], m["c"][k])
            self.t_last = int(t[k])
            if self.snap is None:
                continue
            for w in list(self.watches.values()):
                s = self._step(w, k)
                if s:
                    out.append(s)
            for key, z in list(self.armed.items()):
                if (m["l"][k] <= z["near"]) if z["dir"] == 1 else (m["h"][k] >= z["near"]):
                    self.armed.pop(key)
                    s = self._touch(z, k)
                    if s:
                        out.append(s)
            for key, p in list(self.pending.items()):
                s = self._pending_step(p, k)
                if s:
                    out.append(s)
        return out

    def _touch(self, z, k):
        m, d, snap = self.store.m, z["dir"], self.snap
        t_close = int(m["t"][k]) + MIN
        self.done.add(z["key"])
        atr5 = snap["atr5"]
        age_h = (t_close - z["made"]) / 3_600_000
        w30 = slice(max(0, k - C.SLOW_MIN + 1), k + 1)
        appr = ((m["h"][w30].max() - z["near"]) if d == 1 else (z["near"] - m["l"][w30].min())) / atr5
        base = dict(sym=self.sym, zone=_zone_row(z), age_h=round(age_h, 2), approach_atr=round(float(appr), 2))
        if age_h < C.MIN_AGE_H:
            journal.write("TOUCH_SKIP", why=f"WAIT: zone only {age_h:.1f} h old (< {C.MIN_AGE_H} h)", **base)
            return None
        if C.SKIP_SLOW and appr <= C.SLOW_X:
            journal.write("TOUCH_SKIP", why=f"SLOW approach: {appr:.1f} ATR in 30 min (<= {C.SLOW_X})", **base)
            return None
        why = trend_ok(snap, d)
        if why:
            journal.write("TOUCH_SKIP", why="; ".join(why), **base)
            return None
        sd = z["sd"] if z["sd_fresh"] else None
        fallback = None
        if sd and z["gap"] is not None and z["gap"] <= C.NEAR_SD_ATR:
            top, bot = (z["top"], min(z["bot"], sd["bot"])) if d == 1 else (max(z["top"], sd["top"]), z["bot"])
            kind = "LVN+S/D"
        else:
            top, bot, kind = z["top"], z["bot"], "LVN"
            if sd and C.SD_FALLBACK and (sd["near"] - z["far"]) * d < 0:
                fallback = dict(sd)
        w = self._new_watch(z["key"], z["key"], kind, d, top, bot, z["ext"], k, fallback, z)
        w["approach_atr"] = round(float(appr), 2)
        journal.write("WATCH_START", **base, poi=dict(kind=kind, top=top, bot=bot), fallback_sd=fallback,
                      cvd_divergence=w["cvd_div"])
        log.info("%s WATCH %s %s %s-%s (%s)", self.sym, z["side"], kind, _px(bot), _px(top), "touch")
        return self._step(w, k)

    def _new_watch(self, key, zone_key, kind, d, top, bot, leg_ext, k, fallback, z):
        m = self.store.m
        w = dict(key=key, zone_key=zone_key, sym=self.sym, kind=kind, dir=d, side="LONG" if d == 1 else "SHORT",
                 top=float(top), bot=float(bot), near=float(top if d == 1 else bot), far=float(bot if d == 1 else top),
                 leg_ext=float(leg_ext), t_touch=int(m["t"][k]),
                 t_ext=int(m["t"][k]), ext_px=float(m["l"][k] if d == 1 else m["h"][k]),
                 react=React(d, float(top), float(bot)), fallback=fallback, made=int(z["made"]), nested=z["nested"],
                 cvd_div=cvd_divergence(m, k, d), last_reject=None)
        self.watches[key] = w
        return w

    def _pending_step(self, p, k):
        m, d = self.store.m, p["dir"]
        if (m["l"][k] <= p["near"]) if d == 1 else (m["h"][k] >= p["near"]):
            self.pending.pop(p["key"])
            self.done.add(p["key"])
            why = trend_ok(self.snap, d)
            if why:
                journal.write("TOUCH_SKIP", sym=self.sym, key=p["key"], kind="S/D", why="; ".join(why))
                return None
            w = self._new_watch(p["key"], p["zone_key"], "S/D", d, p["top"], p["bot"], p["leg_ext"], k, None, p)
            journal.write("WATCH_START", sym=self.sym, key=p["key"], poi=dict(kind="S/D", top=p["top"], bot=p["bot"]))
            log.info("%s WATCH %s S/D %s-%s (fallback)", self.sym, w["side"], _px(p["bot"]), _px(p["top"]))
            return self._step(w, k)
        if (m["c"][k] < p["far"]) if d == 1 else (m["c"][k] > p["far"]):
            self.pending.pop(p["key"])
            self.done.add(p["key"])
            journal.write("WATCH_END", sym=self.sym, key=p["key"], kind="S/D", why="1m close beyond the S/D distal line before a touch")
        return None

    def _step(self, w, k):
        m, d = self.store.m, w["dir"]
        t, h, l, c = int(m["t"][k]), m["h"][k], m["l"][k], m["c"][k]
        if (l < w["ext_px"]) if d == 1 else (h > w["ext_px"]):
            w["ext_px"], w["t_ext"] = float(l if d == 1 else h), t
        if (c < w["far"]) if d == 1 else (c > w["far"]):
            self._end(w, "1m close beyond the far edge (zone failed)")
            fb = w.get("fallback")
            if fb:
                p = dict(key=w["key"] + "|SD", zone_key=w["zone_key"], dir=d, top=fb["top"], bot=fb["bot"],
                         near=fb["near"], far=fb["far"], leg_ext=w["leg_ext"], made=w["made"], nested=w["nested"],
                         since=t + MIN)
                journal.write("FALLBACK", sym=self.sym, key=p["key"], sd=fb)
                self.pending[p["key"]] = p
                return self._pending_step(p, k)
            return None
        if (h >= w["leg_ext"]) if d == 1 else (l <= w["leg_ext"]):
            self._end(w, "price reached the leg extreme before a confirmation")
            return None
        rc = w["react"].feed(t, h, l, c, self.swings)
        if not rc:
            return None
        mark = "BOS" if rc == 2 else "CHoCH"
        journal.write("MARK", sym=self.sym, key=w["key"], mark=mark, level=w["react"].level, close=c)
        if rc < NEED.get(C.CONFIRM, 1):
            return None
        return self._confirm(w, k, mark)

    def _confirm(self, w, k, mark):
        m, d, snap = self.store.m, w["dir"], self.snap
        t, c = int(m["t"][k]), float(m["c"][k])
        why = trend_ok(snap, d)
        i_touch = int(np.searchsorted(m["t"], w["t_touch"]))
        i_ext = int(np.searchsorted(m["t"], w["t_ext"]))
        ab = absorption(m, i_touch, k, w["top"], w["bot"], d)
        if ab is None:
            why.append("no ABSORPTION at the zone (big volume with the other side aggressive, price held)")
        ok, net, df = delta_shift(m, i_ext, k, d)
        if not ok:
            why.append(f"no DELTA SHIFT (net delta from the extreme {net:+.4g}, confirm candle {df:+.2f})")
        plan, pwhy = make_plan(d, c, w["far"], w["ext_px"], snap["atr5"], w["leg_ext"], snap["obstacles"])
        if pwhy:
            why.append(pwhy)
        now = t + MIN
        mods = dict(cvd_divergence=w["cvd_div"],
                    liq_against_usd=round(self.flow.liquidations_against(self.sym, d, w["t_touch"], now)),
                    book_imbalance=self.flow.imbalance(self.sym, c, snap["atr5"], now_ms()))
        row = dict(sym=self.sym, key=w["key"], kind=w["kind"], side=w["side"], mark=mark, close=c,
                   absorption_at=None if ab is None else int(m["t"][ab]), net_delta=net, confirm_delta=df,
                   plan=plan, modifiers=mods)
        if why:
            journal.write("CONFIRM_REJECT", why=why, **row)
            log.info("%s %s at %s rejected: %s", self.sym, mark, w["kind"], "; ".join(why))
            if w["react"].step == 3:
                self._end(w, "BOS reached but the confirmation gates failed")
            return None
        self._end(w, "SIGNAL")
        journal.write("SIGNAL", **row)
        log.info("%s SIGNAL %s %s entry %s sl %s tp %s RR %.2f", self.sym, w["side"], w["kind"],
                 _px(c), _px(plan["sl"]), _px(plan["tp"]), plan["rr"])
        return dict(sym=self.sym, dir=d, side=w["side"], key=w["key"], kind=w["kind"], t=now, **plan,
                    atr5=snap["atr5"], modifiers=mods, mark=mark)

    def _end(self, w, why):
        self.watches.pop(w["key"], None)
        self.done.add(w["key"])
        journal.write("WATCH_END", sym=self.sym, key=w["key"], kind=w["kind"], why=why)
        if why != "SIGNAL":
            log.info("%s watch ended %s %s: %s", self.sym, w["side"], w["kind"], why)


def _zone_row(z):
    return dict(key=z["key"], side=z["side"], tf=z["tf"], top=z["top"], bot=z["bot"], nested=z["nested"],
                parent=z["parent"], gap=z["gap"], sd=z["sd"], sd_fresh=z["sd_fresh"], ext=z["ext"],
                made=z["made"], ratio=z["ratio"])
