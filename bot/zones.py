"""Zone snapshot of one symbol: backtest.run_symbol (= Scalp_LVN_1H5m.pine rules) + trend + S/D state.

Called after every 5m close. Everything here is known at that close, nothing looks ahead.
"""
import types

import numpy as np

import backtest as bt
from backtest import add_indicators, came_back
from backtest_scalp_1h5m import strength
from bot import config as C
from bot.config import MIN

STATUS = ("FRESH", "TESTED", "WEAK", "FILLED", "BROKEN", "LEG INVALID")
_ARGS = types.SimpleNamespace(fee=C.FEE, slip=0.0, rr=2.0, atr_mult=C.SL_ATR)


def zone_key(sym, z):
    return f"{sym}|{('5m', '1H', '4H')[z['tier']]}|{z['dir']}|{z['made']}|{z['bot']:.10g}|{z['top']:.10g}"


def _overlap(a, b):
    return a["top"] >= b["bot"] and a["bot"] <= b["top"]


def snapshot(store):
    """State after the last closed 5m candle of the stored 1m data."""
    sym, m = store.sym, store.m
    _, st = bt.run_symbol(sym, m, _ARGS)
    tr1, strong1 = strength(add_indicators(dict(store.h1)))
    tr4, _ = strength(add_indicators(dict(store.h4)))
    trend, is_strong, t4 = int(tr1[-1]), bool(strong1[-1]), int(tr4[-1])
    px, atr = st["close"], st["atr"]
    now = int(m["t"][-1]) + MIN
    live = st["live"]
    zones, obstacles = [], []
    for z in live:
        d, tier = z["dir"], z["tier"]
        near, far = (z["top"], z["bot"]) if d == 1 else (z["bot"], z["top"])
        sd = sd_fresh = None
        if z.get("sd") is not None:
            sd_top, sd_bot = (float(x) for x in z["sd"])
            sd = dict(top=sd_top, bot=sd_bot, near=sd_top if d == 1 else sd_bot, far=sd_bot if d == 1 else sd_top)
            sd_fresh = not came_back(m, z["t0"], now, d, sd_top, sd_bot)
            # a 1m close beyond the distal line = the S/D zone is gone (Pine removes it on a close beyond)
            i0 = int(np.searchsorted(m["t"], z["t0"]))
            beyond = (m["c"][i0:] < sd_bot) if d == 1 else (m["c"][i0:] > sd_top)
            if beyond.any():
                sd_fresh = None
        # opposing zones block a target: fresh opposite LVNs (any TF) and fresh opposite S/D zones
        if z["status"] == 0:
            obstacles.append(dict(dir=d, near=float(near), kind=f"{('5m', '1H', '4H')[tier]} LVN"))
        if sd is not None and sd_fresh:
            obstacles.append(dict(dir=d, near=sd["near"], kind="S/D"))
        if tier == 2:
            continue
        parent = tier == 0 and any(o["tier"] == 1 and o["status"] < 3 and o["dir"] == d and _overlap(z, o) for o in live)
        stop_pct = (z["top"] - z["bot"] + C.SL_ATR * atr) / near * 100
        zones.append(dict(
            key=zone_key(sym, z), sym=sym, tf=("5m", "1H")[tier], tier=tier, side="LONG" if d == 1 else "SHORT", dir=d,
            top=float(z["top"]), bot=float(z["bot"]), near=float(near), far=float(far),
            status=STATUS[z["status"]], status_i=int(z["status"]), nested=bool(z["nested"]), parent=bool(parent),
            ratio=float(z["ratio"]), made=int(z["made"]), t0=int(z["t0"]), ext=float(z["ext"]),
            age_h=(now - z["made"]) / 3_600_000, gap=None if z["gap"] is None else float(z["gap"]),
            sd=sd, sd_fresh=sd_fresh, stop_pct=stop_pct,
            dist_pct=(px - near) * d / px * 100, dist_atr=(px - near) * d / atr))
    zones.sort(key=lambda z: abs(z["dist_pct"]))
    return dict(sym=sym, time=now, close=px, atr5=atr, trend1h=trend, strong1h=is_strong, trend4h=t4,
                zones=zones, obstacles=obstacles)


def trend_ok(snap, d):
    """Script trade filter, trend part: 1H STRONG in the zone direction and 4H trend on the same side."""
    why = []
    if not snap["strong1h"]:
        why.append("1H trend not STRONG")
    if snap["trend1h"] != d:
        why.append("against the 1H trend")
    if snap["trend4h"] != d:
        why.append("4H trend on the other side")
    return why


def entry_zone_why(snap, z):
    """Why this zone cannot be an entry zone (empty list = it can). Checked at every 5m close."""
    why = []
    if z["tier"] != 0:
        why.append("1H LVN (context only, entries are on 5m LVNs)")
    if z["status_i"] != 0:
        why.append(z["status"])
    if C.REQUIRE_NESTED and not (z["nested"] and z["parent"]):
        why.append("not NESTED in a live 1H LVN")
    if z["stop_pct"] < C.MIN_STOP:
        why.append(f"zone stop {z['stop_pct']:.3f}% < {C.MIN_STOP}%")
    if z["dist_atr"] <= 0:
        why.append("price already past the near edge")
    return why + trend_ok(snap, z["dir"])
