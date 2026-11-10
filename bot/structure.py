"""1m market structure, ported line by line from Scalp_LVN_1H5m.pine (section 3b + f_react).

Swings: zigzag on 1m candles. A swing high is confirmed once price falls 3 x ATR(14, 1m) from the highest high
since the last swing low (and the mirror for lows). ATR = Wilder, first value = average of the first 14 true ranges.

Reaction of one zone (f_react): touch -> CHoCH = 1m close beyond the last confirmed swing (high for a long)
-> BOS = 1m close beyond a swing confirmed after the CHoCH.
"""
from bot import config as C


class LtfSwings:
    """Incremental 1m zigzag for one symbol. Feed every closed 1m candle in order."""

    def __init__(self):
        self.prev = None  # previous close
        self.cnt = 0
        self.sum = 0.0
        self.atr = None
        self.dir = 1
        self.ext = self.ext_t = None
        self.sw_h = self.sw_h_t = None  # last confirmed swing high and its time
        self.sw_l = self.sw_l_t = None

    def feed(self, t, h, l, c):
        tr = h - l if self.prev is None else max(h - l, abs(h - self.prev), abs(l - self.prev))
        self.cnt += 1
        self.prev = c
        if self.cnt <= 14:
            self.sum += tr
            if self.cnt == 14:
                self.atr = self.sum / 14
        else:
            self.atr = (self.atr * 13 + tr) / 14
        if self.ext is None:
            self.ext, self.ext_t = h, t
        elif self.atr is not None:
            x = C.LTF_SWING_ATR * self.atr
            if self.dir == 1:
                if h > self.ext:
                    self.ext, self.ext_t = h, t
                elif self.ext - l >= x:
                    self.sw_h, self.sw_h_t = self.ext, self.ext_t
                    self.dir, self.ext, self.ext_t = -1, l, t
            else:
                if l < self.ext:
                    self.ext, self.ext_t = l, t
                elif h - self.ext >= x:
                    self.sw_l, self.sw_l_t = self.ext, self.ext_t
                    self.dir, self.ext, self.ext_t = 1, h, t


class React:
    """f_react state of one zone. step: 0 = not touched, 1 = touched, 2 = CHoCH, 3 = BOS."""

    def __init__(self, d, top, bot):
        self.d, self.top, self.bot = d, top, bot
        self.step = 0
        self.t_choch = None
        self.level = None  # level of the last CHoCH / BOS

    def to_dict(self):
        return dict(d=self.d, top=self.top, bot=self.bot, step=self.step, t_choch=self.t_choch, level=self.level)

    @classmethod
    def from_dict(cls, x):
        r = cls(x["d"], x["top"], x["bot"])
        r.step, r.t_choch, r.level = x["step"], x["t_choch"], x["level"]
        return r

    def feed(self, t, h, l, c, sw):
        """One closed 1m candle, after sw (LtfSwings) has taken it. Returns 0, 1 (CHoCH) or 2 (BOS)."""
        if self.step == 0 and ((l <= self.top) if self.d == 1 else (h >= self.bot)):
            self.step = 1
        lvl, t_lvl = (sw.sw_h, sw.sw_h_t) if self.d == 1 else (sw.sw_l, sw.sw_l_t)
        if lvl is not None and (self.step == 1 or (self.step == 2 and t_lvl > self.t_choch)) \
                and ((c > lvl) if self.d == 1 else (c < lvl)):
            bos = self.step == 2
            self.step = 3 if bos else 2
            self.t_choch = t
            self.level = lvl
            return 2 if bos else 1
        return 0
