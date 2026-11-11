"""Bot settings. Zone rules = Scalp_LVN_1H5m.pine defaults (same values scan_zones.py uses)."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import backtest as bt  # noqa: E402
from backtest import MIN  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(ROOT, ".env"))


def env_str(name, default):
    v = os.getenv(name)
    return default if v is None or v.strip() == "" else v.strip()


def env_bool(name, default):
    return env_str(name, default).lower() in ("1", "true", "yes", "on")


def env_float(name, default):
    return float(env_str(name, str(default)))


# ------------------------------------------------------------ Binance account (.env)
# Keys come only from .env / environment variables, never from code. Use a trade-only key
# (no withdrawal) with an IP whitelist, ideally on a sub-account used only by this bot.
BINANCE_API_KEY = env_str("BINANCE_API_KEY", "")
BINANCE_API_SECRET = env_str("BINANCE_API_SECRET", "")
# Safe defaults: testnet ON, trading OFF. Real orders need BOTH changed on purpose.
USE_TESTNET = env_bool("USE_TESTNET", "true")
TRADING_ENABLED = env_bool("TRADING_ENABLED", "false")
KILL_SWITCH_FILE = os.path.join(ROOT, env_str("KILL_SWITCH_FILE", "KILL_SWITCH"))

# REST client settings (same as binance_ai_bot_vp)
REST_THROTTLE_SECONDS = env_float("REST_THROTTLE_SECONDS", 0.15)
OWN_WEIGHT_PER_MIN = env_float("OWN_WEIGHT_PER_MIN", 500)  # this bot's REST weight per minute (IP limit 2400 is shared)
REST_MAX_RETRIES = int(env_float("REST_MAX_RETRIES", 4))
REST_TIMEOUT_SECONDS = int(env_float("REST_TIMEOUT_SECONDS", 15))
UNIVERSE_QUOTE_ASSET = "USDT"
SYMBOL_DENYLIST = [x.strip().upper() for x in env_str("SYMBOL_DENYLIST", "").split(",") if x.strip()]

# Zones are always computed from MAINNET market data (testnet prices and volume are not real).
# Binance moved USD-M market streams to /market (the old /stream URL times out from here, tested 2026-11-09)
WS = "wss://fstream.binance.com/market/stream?streams="

DAYS_1M = 21  # 1m history for legs + volume profiles (Pine keeps 30,000 1m intrabars, about 20.8 days)
HTF_BARS = 1000  # 1H candles for the trend / ADX / EMA 50 (long warm-up, like the backtest)
CTX_BARS = 500  # 4H candles for the 4H trend filter

# Trade filter + LVN quality (Pine inputs minStop, slAtr, minAge, slowX)
MIN_STOP = 0.30  # % : 5m zone, entry at the near edge, stop 0.5 ATR beyond the far edge
ARM_MIN_STOP = env_bool("ARM_MIN_STOP", "true")  # true: a 5m LVN whose zone stop is < MIN_STOP is not armed; false: armed, the plan widens the stop to MIN_STOP
SL_ATR = 0.50
MIN_AGE_H = 2.0  # WAIT: no entry in the first 2 h (5m zones)
SLOW_X = 2.0  # SLOW: price travelled <= 2 ATR toward the zone in the last 30 min
SLOW_MIN = 30

WS_PUBLIC = "wss://fstream.binance.com/public/stream?streams="  # order book streams live here (binance_ai_bot_vp)

# ------------------------------------------------------------ strategy (bot/watch.py)
REQUIRE_NESTED = env_bool("REQUIRE_NESTED", "false")  # false = all FRESH 5m LVNs; true = only those inside a live same-direction 1H LVN
SKIP_SLOW = env_bool("SKIP_SLOW", "true")  # slow drift into the zone (<= 2 ATR in 30 min) held 26.8% -> skip
NEAR_SD_ATR = env_float("NEAR_SD_ATR", 1.0)  # LVN far edge within this many 5m ATR of its S/D -> one merged zone
SD_FALLBACK = env_bool("SD_FALLBACK", "true")  # LVN failed and its S/D is further away and fresh -> watch the S/D
CONFIRM = env_str("CONFIRM", "CHOCH").upper()  # script reaction marks on 1m: CHOCH (first) or BOS (second)
LTF_SWING_ATR = 3.0  # Pine "Intrabar swing size": 1m swings of 3 x ATR(14, 1m)

# Order flow at the zone (1m taker buy / sell volume). Same values as binance_ai_bot_vp's zone watch.
ABSORB_VOL_X = env_float("ABSORB_VOL_X", 2.0)  # absorption bar volume >= 2 x median of the 20 bars before it
ABSORB_DELTA = env_float("ABSORB_DELTA", 0.20)  # ... with taker sells (long) >= 20% more than buys: delta / volume <= -0.20
FLIP_DELTA = env_float("FLIP_DELTA", 0.10)  # confirmation candle: delta / volume >= +0.10 in the trade direction
LIQ_DOMINANCE = env_float("LIQ_DOMINANCE", 2.0)  # liquidation flush: losing-side liquidations >= 2 x the other side (and > 0)
BOOK_IMB = env_float("BOOK_IMB", 0.20)  # book imbalance (bid - ask) / (bid + ask) within 1 x 5m ATR of price, in the trade direction
OF_MIN_PASS = int(env_float("OF_MIN_PASS", 2))  # order flow: signal when at least this many of the 5 gates pass (0 = off)

# Stop / target
SL_BUFFER_ATR = env_float("SL_BUFFER_ATR", 0.50)  # beyond the zone far edge and the reaction low (Pine slAtr)
TP_EXT = env_float("TP_EXT", 0.0)  # 0 = target at the leg extreme; 0.272 = 1.272 Fib extension of the pullback (leg extreme to reaction extreme)
TP_FRONT_ATR = env_float("TP_FRONT_ATR", 0.05)  # target sits this far before the liquidity / opposing zone
MIN_RR = env_float("MIN_RR", 2.0)  # after fees
FEE = env_float("FEE", 0.0005)  # taker, per side
MAX_SPREAD_BPS = env_float("MAX_SPREAD_BPS", 6.0)
BE_AT_R = env_float("BE_AT_R", 1.5)  # stop to break-even (+ fees) once price reaches this many R (user: 1.5R), 0 = off

# ------------------------------------------------------------ risk (bot/risk.py)
RISK_PCT = env_float("RISK_PCT", 0.25)  # % of equity lost if the stop is hit
MARGIN_USDT = env_float("MARGIN_USDT", 10.0)  # live: fixed margin per trade (USDT); leverage = the symbol's max
LIQ_BUFFER = env_float("LIQ_BUFFER", 0.25)  # liquidation must be >= stop distance x (1 + this) away, else lower leverage
MARGIN_TYPE = env_str("MARGIN_TYPE", "ISOLATED")
MAX_POSITIONS = int(env_float("MAX_POSITIONS", 3))
DAILY_LOSS_LIMIT_R = env_float("DAILY_LOSS_LIMIT_R", 3.0)  # no new entries for the rest of the UTC day
CONSECUTIVE_LOSS_LIMIT = int(env_float("CONSECUTIVE_LOSS_LIMIT", 4))
COOLDOWN_H = env_float("COOLDOWN_H", 6.0)
PAPER_EQUITY = env_float("PAPER_EQUITY", 1000.0)
STOP_WORKING_TYPE = env_str("STOP_WORKING_TYPE", "MARK_PRICE")
STOP_PRICE_PROTECT = env_bool("STOP_PRICE_PROTECT", "true")

# ------------------------------------------------------------ universe
UNIVERSE_SIZE = int(env_float("UNIVERSE_SIZE", 200))  # highest 24h volume USDT perps
MIN_QUOTE_VOLUME = env_float("MIN_QUOTE_VOLUME", 2_000_000)
SCAN_SYMBOLS = [x.strip().upper() for x in env_str("SCAN_SYMBOLS", "").split(",") if x.strip()]  # fixed list

CACHE = os.path.join(ROOT, "bot_cache")
LIVE = os.path.join(ROOT, "live")
LOGS = os.path.join(ROOT, "logs")
STATE = os.path.join(ROOT, "live", "state.json")


def apply_script_defaults():
    bt.CHART, bt.HTF, bt.CTX = 5 * MIN, 60 * MIN, 240 * MIN
    bt.MIN_ATR, bt.MIN_VOL_CHART, bt.MIN_VOL_HTF, bt.MIN_DIR, bt.PULLBACK = 4.0, 1.5, 1.1, 0.70, 0.30
    bt.REQ_BOS, bt.MIN_EFF, bt.MAX_BARS, bt.MAX_BARS_HTF, bt.PB_ATR, bt.VOL_MEDIAN = False, 0.15, 30, 16, 2.0, 100
    bt.ROWS, bt.PEAK_W, bt.MAX_LVN, bt.EDGE = 150, 2, 5, 0.10
    bt.MAX_RATIO, bt.MAX_TIME, bt.MAX_GAP, bt.ZONE_PAD = 0.50, 0.50, 3.0, 0.25
    bt.WEAK_N, bt.FILL_N, bt.BROKE_N = 9, 18, 6
