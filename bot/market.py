"""Binance USD-M public data: REST backfill + 1m candle store per symbol."""
import os
import threading
import time

import numpy as np

from bot import config as C
from bot.config import MIN
from bot.exchange.rest import RestClient

KEYS = ("t", "o", "h", "l", "c", "v", "tb")
# Market data always from mainnet, no keys: zones must be built on real prices and volume
public = RestClient(api_key="", api_secret="", testnet=False)


_clock = dict(offset=0, synced=0.0)


def now_ms():
    """Binance server time in ms. The local clock can be seconds off (this PC: +6.5 s on 2026-11-09), and a
    candle must never be taken as closed before Binance closes it. Re-synced every 10 minutes."""
    if time.time() - _clock["synced"] > 600:
        try:
            _clock["offset"] = public.sync_time()
        except Exception:  # keep the last offset; retried on the next call
            pass
        _clock["synced"] = time.time()
    return int(time.time() * 1000) + _clock["offset"]


def top_symbols(n):
    info = public.exchange_info()["symbols"]
    ok = {s["symbol"] for s in info if s["contractType"] == "PERPETUAL" and s["status"] == "TRADING"
          and s["quoteAsset"] == "USDT" and s["symbol"].isascii() and s["symbol"] not in C.SYMBOL_DENYLIST}
    rows = [r for r in public.ticker_24hr() if r["symbol"] in ok and float(r["quoteVolume"]) >= C.MIN_QUOTE_VOLUME]
    rows.sort(key=lambda r: float(r["quoteVolume"]), reverse=True)
    return [r["symbol"] for r in rows[:n]]


def klines(sym, interval, start=None, end=None, limit=1500):
    return public.klines(sym, interval, start, end, limit)


def to_bars(rows, now):
    """Closed klines -> bar dict like backtest.resample() returns."""
    rows = [r for r in rows if r[6] < now]  # closeTime < now = closed
    a = np.array([(r[0], float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[5]), float(r[9]), r[6] + 1) for r in rows])
    return dict(t=a[:, 0].astype(np.int64), o=a[:, 1], h=a[:, 2], l=a[:, 3], c=a[:, 4], v=a[:, 5], tb=a[:, 6], tc=a[:, 7].astype(np.int64))


class Store:
    """Closed 1m candles of one symbol (last DAYS_1M days) + native 1H / 4H candles for the trend filters."""

    def __init__(self, sym):
        self.sym = sym
        self.path = os.path.join(C.CACHE, sym + ".npz")
        self.m = None
        self.h1 = self.h4 = None
        self.lock = threading.Lock()  # WebSocket adds and REST backfills can run at the same time

    def last(self):
        return int(self.m["t"][-1]) if self.m is not None and len(self.m["t"]) else None

    def load(self):
        os.makedirs(C.CACHE, exist_ok=True)
        if os.path.exists(self.path):
            d = np.load(self.path)
            self.m = {k: d[k] for k in KEYS}
        self.backfill()
        self.refresh_htf(force=True)

    def backfill(self):
        """Download every closed 1m candle after the last stored one."""
        now = now_ms()
        start = now // MIN * MIN - C.DAYS_1M * 1440 * MIN
        cur = self.last() + MIN if self.last() and self.last() >= start else start
        if self.last() is None or self.last() < start:
            self.m = None
        rows = []
        while cur < now // MIN * MIN:
            chunk = klines(self.sym, "1m", cur, now // MIN * MIN - 1)
            chunk = [r for r in chunk if r[6] < now]
            if not chunk:
                break
            rows += [(r[0], float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[5]), float(r[9])) for r in chunk]
            cur = chunk[-1][0] + MIN
        if rows:
            self._append(np.array(rows))
        self._trim(start)
        return len(rows)

    def add(self, k):
        """Closed 1m candle from the WebSocket. Returns False if there is a gap (caller backfills)."""
        t = int(k["t"])
        last = self.last()
        if last is not None and t <= last:
            return True
        if last is not None and t != last + MIN:
            return False
        self._append(np.array([(t, float(k["o"]), float(k["h"]), float(k["l"]), float(k["c"]), float(k["v"]), float(k["V"]))]))
        return True

    def _append(self, a):
        with self.lock:
            self._append_locked(a)

    def _append_locked(self, a):
        new = dict(t=a[:, 0].astype(np.int64), o=a[:, 1], h=a[:, 2], l=a[:, 3], c=a[:, 4], v=a[:, 5], tb=a[:, 6])
        if self.m is None:
            self.m = new
        else:
            keep = new["t"] > self.last()
            self.m = {k: np.r_[self.m[k], new[k][keep]] for k in KEYS}

    def _trim(self, start):
        keep = self.m["t"] >= start
        if not keep.all():
            self.m = {k: v[keep] for k, v in self.m.items()}

    def save(self):
        np.savez(self.path, **self.m)

    def refresh_htf(self, force=False):
        """Re-download 1H / 4H candles once a new 1H candle has closed."""
        now = now_ms()
        if not force and self.h1 is not None and self.h1["tc"][-1] >= now // (60 * MIN) * (60 * MIN):
            return
        self.h1 = to_bars(klines(self.sym, "1h", limit=C.HTF_BARS + 1), now)
        self.h4 = to_bars(klines(self.sym, "4h", limit=C.CTX_BARS + 1), now)
