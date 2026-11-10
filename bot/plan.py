"""Stop, target and RR from market structure.

STOP (long; short is the mirror): below BOTH the zone's far edge and the reaction low (the lowest 1m low since
the touch = the swing the CHoCH protects), plus 0.5 x 5m ATR (Pine slAtr). If that is closer than 0.30% of
price (Pine minStop: fees would eat the trade), the stop is moved out to 0.30%.

TARGET: the leg extreme the pullback came from (the swing high whose liquidity the continuation goes for),
moved 0.05 ATR in front. TP_EXT > 0: that many pullback lengths beyond the leg extreme (0.272 = 1.272 extension). If a FRESH opposing zone (opposite LVN of any TF, or fresh opposite S/D) sits
between entry and that level, the target is moved in front of the nearest one instead.

RR is measured after fees (taker both sides): (reward - fees) / (risk + fees). Below 2.0 = no trade.
"""
from bot import config as C


def make_plan(d, entry, poi_far, react_ext, atr5, leg_ext, obstacles):
    """Returns (plan, None) or (None, reason)."""
    buf = C.SL_BUFFER_ATR * atr5
    sl = min(poi_far, react_ext) - buf if d == 1 else max(poi_far, react_ext) + buf
    min_risk = entry * C.MIN_STOP / 100
    if (entry - sl) * d < min_risk:
        sl = entry - d * min_risk
    risk = (entry - sl) * d
    if (leg_ext - entry) * d <= 0:
        return None, "price is already at / beyond the leg extreme (no room to the target)"
    front = C.TP_FRONT_ATR * atr5
    goal = leg_ext + C.TP_EXT * (leg_ext - react_ext)  # TP_EXT 0 = the leg extreme itself
    tp, tp_kind = goal - d * front, "leg extreme (swing liquidity)" if not C.TP_EXT else f"{1 + C.TP_EXT:g} extension of the pullback"
    block = [o for o in obstacles if o["dir"] == -d and 0 < (o["near"] - entry) * d < (goal - entry) * d]
    if block:
        o = min(block, key=lambda o: (o["near"] - entry) * d)
        tp, tp_kind = o["near"] - d * front, f"in front of opposing {o['kind']}"
    reward = (tp - entry) * d
    if reward <= 0:
        return None, f"no room: {tp_kind} is at the entry"
    rr = rr_net(entry, sl, tp)
    plan = dict(entry=entry, sl=sl, tp=tp, tp_kind=tp_kind, risk=risk, risk_pct=risk / entry * 100,
                rr=rr, rr_gross=reward / risk)
    if rr < C.MIN_RR:
        return None, (f"RR {rr:.2f} after fees < {C.MIN_RR} (target: {tp_kind}; risk {risk / entry * 100:.2f}%, "
                      f"reward {reward / entry * 100:.2f}%)")
    return plan, None


def rr_net(entry, sl, tp):
    risk, reward = abs(entry - sl), abs(tp - entry)
    return (reward - (entry + tp) * C.FEE) / (risk + (entry + sl) * C.FEE)
