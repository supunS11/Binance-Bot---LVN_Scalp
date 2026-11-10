"""Logs. Every decision is written with its reason, nothing is skipped silently.

  logs/bot.log            human readable
  logs/decisions.jsonl    zone armed / disarmed, watch started / ended, confirmation passed / rejected, signals
  logs/trades.jsonl       opened / closed trades (live and paper) with R after fees
"""
import datetime as dt
import json
import logging
import os
import threading

from bot import config as C

log = logging.getLogger("bot")
_lock = threading.Lock()


def setup_logging():
    os.makedirs(C.LOGS, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s", "%Y-%m-%d %H:%M:%S")
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    for h in (logging.FileHandler(os.path.join(C.LOGS, "bot.log"), encoding="utf-8"), logging.StreamHandler()):
        h.setFormatter(fmt)
        root.addHandler(h)


def _default(o):
    try:
        return float(o)
    except (TypeError, ValueError):
        return str(o)


def write(event, **row):
    row = dict(at=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), event=event, **row)
    name = "trades.jsonl" if event.startswith("TRADE") else "decisions.jsonl"
    with _lock, open(os.path.join(C.LOGS, name), "a", encoding="utf-8") as f:
        f.write(json.dumps(row, default=_default) + "\n")
