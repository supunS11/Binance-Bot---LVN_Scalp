"""Fixed margin sizing with the symbol's max leverage.

Binance leverage brackets (GET /fapi/v1/leverageBracket) give, per notional band:
initialLeverage (max leverage in that band), notionalFloor / notionalCap, maintMarginRatio, cum.
With a fixed margin M, leverage L gives notional M x L. L is allowed when the band that holds
M x L allows at least L.

Liquidation check (ISOLATED, one position, one-way mode, Binance formula):
    LP = (WB + cum - s * qty * EP) / (qty * MMR - s * qty)      s = +1 long, -1 short, WB = M
The stop must be hit before liquidation: the liquidation price must be beyond the stop by at
least LIQ_BUFFER x stop distance. If the max leverage fails that, the leverage is lowered one
step at a time until it passes (the margin stays fixed, so the position gets smaller).
"""


def bracket_for(brackets, notional):
    for b in sorted(brackets, key=lambda b: float(b["notionalFloor"])):
        if float(b["notionalFloor"]) <= notional < float(b["notionalCap"]):
            return b
    return None


def liq_price(d, entry, qty, margin, mmr, cum):
    return (margin + cum - d * qty * entry) / (qty * mmr - d * qty)


def pick_leverage(brackets, margin, entry, sl, d, liq_buffer):
    """Returns (dict(lev, notional, qty, liq, max_lev), None) or (None, reason)."""
    max_lev = max(int(b["initialLeverage"]) for b in brackets)
    stop_dist = abs(entry - sl)
    for lev in range(max_lev, 0, -1):
        notional = margin * lev
        b = bracket_for(brackets, notional)
        if b is None or int(b["initialLeverage"]) < lev:
            continue
        qty = notional / entry
        lp = liq_price(d, entry, qty, margin, float(b["maintMarginRatio"]), float(b["cum"]))
        if (entry - lp) * d >= stop_dist * (1 + liq_buffer):
            return dict(lev=lev, notional=notional, qty=qty, liq=lp, max_lev=max_lev), None
    return None, f"no leverage keeps liquidation beyond the stop (stop {stop_dist / entry * 100:.2f}%)"
