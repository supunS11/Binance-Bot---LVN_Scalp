"""Order flow at the zone, from closed 1m candles (taker buy volume) + live liquidation / order book streams.

Two HARD gates, both needed for an entry (same idea and values as binance_ai_bot_vp's zone watch):
  ABSORPTION  a 1m candle at the zone with big volume (>= 2 x median of the 20 candles before it), where the
              aggressive side was AGAINST the trade (long: taker sells >= 0.20 of volume more than buys) but
              price did not follow (long: close >= open). Sellers hit the zone hard and were absorbed.
  DELTA SHIFT from the reaction extreme (lowest 1m low since the touch, for a long) to the confirmation candle,
              net taker delta is in the trade direction, and the confirmation candle's own delta / volume is
              >= 0.10 in the trade direction. Buyers took over.
Recorded only (logged with every decision, not a gate yet): CVD divergence on the approach, liquidations against
the trade side during the watch, order book imbalance near price at the confirmation.
"""
import collections
import threading

import numpy as np

from bot import config as C


def delta_frac(m, k):
    v = m["v"][k]
    return float((2 * m["tb"][k] - v) / v) if v > 0 else 0.0


def absorption(m, i0, i1, top, bot, d):
    """Latest index in [i0, i1] that shows absorption at the zone [bot, top], or None."""
    for k in range(i1, i0 - 1, -1):
        if k < 20 or not (m["l"][k] <= top and m["h"][k] >= bot):
            continue
        med = float(np.median(m["v"][k - 20:k]))
        if med <= 0 or m["v"][k] < C.ABSORB_VOL_X * med:
            continue
        df = delta_frac(m, k)
        if d == 1 and df <= -C.ABSORB_DELTA and m["c"][k] >= m["o"][k]:
            return k
        if d == -1 and df >= C.ABSORB_DELTA and m["c"][k] <= m["o"][k]:
            return k
    return None


def delta_shift(m, k_ext, k_conf, d):
    """(ok, net delta from the extreme to the confirmation candle, delta / volume of the confirmation candle)."""
    seg = slice(k_ext, k_conf + 1)
    net = float((2 * m["tb"][seg] - m["v"][seg]).sum())
    df = delta_frac(m, k_conf)
    return d * net > 0 and d * df >= C.FLIP_DELTA, net, df


def cvd_divergence(m, k_touch, d, n=12):
    """Approach leg (n 1m candles before the touch): new low (long) on falling volume pressure = CVD higher low."""
    i0 = max(0, k_touch - n)
    if k_touch - i0 < 4:
        return False
    cvd = np.cumsum(2 * m["tb"][i0:k_touch] - m["v"][i0:k_touch])
    half = (k_touch - i0) // 2
    if d == 1:
        lo = m["l"][i0:k_touch]
        a, b = int(np.argmin(lo[:half])), half + int(np.argmin(lo[half:]))
        return bool(lo[b] < lo[a] and cvd[b] > cvd[a])
    hi = m["h"][i0:k_touch]
    a, b = int(np.argmax(hi[:half])), half + int(np.argmax(hi[half:]))
    return bool(hi[b] > hi[a] and cvd[b] < cvd[a])


class LiveFlow:
    """Liquidations (all symbols, !forceOrder@arr) and the latest top-20 order book of watched symbols."""

    def __init__(self):
        self.lock = threading.Lock()
        self.liq = collections.defaultdict(lambda: collections.deque(maxlen=2000))  # sym -> (t, side, usd)
        self.book = {}  # sym -> (t, bids, asks)

    def on_liquidation(self, o):
        with self.lock:
            self.liq[o["s"]].append((int(o["T"]), o["S"], float(o["ap"] or o["p"]) * float(o["z"] or o["q"])))

    def on_depth(self, sym, data):
        with self.lock:
            self.book[sym] = (int(data["E"]), [(float(p), float(q)) for p, q in data["b"]],
                              [(float(p), float(q)) for p, q in data["a"]])

    def liquidations_against(self, sym, d, t0, t1):
        """USD of positions on the losing side liquidated in [t0, t1]. Long trade: longs liquidated (SELL orders)."""
        side = "SELL" if d == 1 else "BUY"
        with self.lock:
            return sum(u for t, s, u in self.liq.get(sym, ()) if s == side and t0 <= t <= t1)

    def imbalance(self, sym, mid, width, now_ms, max_age_ms=5000):
        """(bid qty / ask qty) within `width` of mid, from a book no older than 5 s. None = no fresh book."""
        with self.lock:
            b = self.book.get(sym)
        if b is None or now_ms - b[0] > max_age_ms:
            return None
        bid = sum(q for p, q in b[1] if p >= mid - width)
        ask = sum(q for p, q in b[2] if p <= mid + width)
        return bid / ask if ask > 0 else None
