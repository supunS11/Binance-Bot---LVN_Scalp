# Live bot entry logic, TP/SL backtest with fees

BTC, ETH, SOL, XRP, 2025-10-19 to 2026-10-19; 2024-25 = BTC, ETH, 2024-10-19 to 2025-10-19.
The bot's own Watcher code on replayed data; thresholds = bot config, fixed before the run. Fees 0.05% per side.
Stop first inside one candle; stop to entry + fees at 1.5R. One position per symbol. Win = net R > 0.

| Set | Trades | Per coin per day | Win % | Break-even exits % | Avg net R | 95% range | Total R | Max DD (R) | Median stop % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **A: bot as live (CHoCH + 2 of 5 order flow gates; liq / book not in data)**, 2025-26 | 1 | 0.00 | 100.0 | 100 | +0.000 | +0.000 to +0.000 | +0.0 | 0.0 | 1.10 |
|   1st half | 1 | 0.00 | 100.0 | 100 | +0.000 | +0.000 to +0.000 | +0.0 | 0.0 | 1.10 |
|   2nd half | 0 | | | | | | | | |
|   2024-25 (BTC, ETH) | 0 | | | | | | | | |
| **B: CHoCH only, no order flow gates**, 2025-26 | 2 | 0.00 | 100.0 | 50 | +1.380 | +0.000 to +2.761 | +2.8 | 0.0 | 1.06 |
|   1st half | 1 | 0.00 | 100.0 | 100 | +0.000 | +0.000 to +0.000 | +0.0 | 0.0 | 1.10 |
|   2nd half | 1 | 0.00 | 100.0 | 0 | +2.761 | +2.761 to +2.761 | +2.8 | 0.0 | 1.02 |
|   2024-25 (BTC, ETH) | 1 | 0.00 | 0.0 | 0 | -1.119 | -1.119 to -1.119 | -1.1 | 1.1 | 0.84 |
| **C: limit at the near edge, no confirmation**, 2025-26 | 53 | 0.04 | 30.2 | 25 | -0.165 | -0.638 to +0.374 | -8.8 | 12.3 | 0.44 |
|   1st half | 29 | 0.04 | 34.5 | 31 | -0.334 | -0.825 to +0.263 | -9.7 | 11.8 | 0.48 |
|   2nd half | 24 | 0.03 | 25.0 | 17 | +0.038 | -0.791 to +1.024 | +0.9 | 7.6 | 0.42 |
|   2024-25 (BTC, ETH) | 23 | 0.03 | 26.1 | 22 | -0.253 | -1.045 to +0.977 | -5.8 | 19.5 | 0.44 |
| **D: A without the 4H filter**, 2025-26 | 2 | 0.00 | 100.0 | 50 | +1.535 | +0.000 to +3.070 | +3.1 | 0.0 | 0.77 |
|   1st half | 2 | 0.00 | 100.0 | 50 | +1.535 | +0.000 to +3.070 | +3.1 | 0.0 | 0.77 |
|   2nd half | 0 | | | | | | | | |
|   2024-25 (BTC, ETH) | 2 | 0.00 | 50.0 | 0 | +0.780 | -1.133 to +2.692 | +1.6 | 1.1 | 0.91 |

## Per coin, 2025-26

| Set | Coin | Trades | Avg net R | Total R |
|---|---|---:|---:|---:|
| A | BTCUSDT | 0 | +nan | +0.0 |
| A | ETHUSDT | 0 | +nan | +0.0 |
| A | SOLUSDT | 0 | +nan | +0.0 |
| A | XRPUSDT | 1 | +0.000 | +0.0 |
| B | BTCUSDT | 0 | +nan | +0.0 |
| B | ETHUSDT | 0 | +nan | +0.0 |
| B | SOLUSDT | 0 | +nan | +0.0 |
| B | XRPUSDT | 2 | +1.380 | +2.8 |
| C | BTCUSDT | 6 | -0.328 | -2.0 |
| C | ETHUSDT | 13 | -0.340 | -4.4 |
| C | SOLUSDT | 13 | -0.587 | -7.6 |
| C | XRPUSDT | 21 | +0.250 | +5.3 |
| D | BTCUSDT | 0 | +nan | +0.0 |
| D | ETHUSDT | 0 | +nan | +0.0 |
| D | SOLUSDT | 0 | +nan | +0.0 |
| D | XRPUSDT | 2 | +1.535 | +3.1 |

## Funnel A: bot as live (CHoCH + 2 of 5 order flow gates; liq / book not in data), 2025-26 (all 4 coins)

- Zones armed (unique): 405; arm events 2158 (a zone re-arms after a disarm)
- DISARMED: 1971
  - 1447 zone stop < 0.30% (moves with the 5m ATR)
  - 511 1H trend not STRONG
  - 8 zone removed by the engine
  - 4 against the 1H trend
  - 1 1H trend not STRONG; against the 1H trend
- TOUCH_SKIP: 115
  - 111 WAIT: zone younger than 2 h
  - 3 1H trend not STRONG
  - 1 SLOW approach (<= 2 ATR in 30 min)
- WATCH_START: 80
- MARK: 36
- CONFIRM_REJECT: 35
  - 32 RR < 2 after fees
  - 1 1H trend not STRONG; RR 1.40 after fees < 2.0
  - 1 1H trend not STRONG; RR 0.94 after fees < 2.0
  - 1 order flow 0/5 < 2
- WATCH_END: 80
  - 51 1m close beyond the far edge
  - 13 BOS reached but the confirmation gates failed
  - 9 price reached the leg extreme before a confirmation
  - 5 zone FILLED / removed by the engine
  - 1 zone BROKEN
  - 1 SIGNAL
- ENTRY_SKIP: 0
- Trades: 1 (exits: {'BREAK-EVEN': 1}, median hold 124 min)

## Funnel B: CHoCH only, no order flow gates, 2025-26 (all 4 coins)

- Zones armed (unique): 405; arm events 2158 (a zone re-arms after a disarm)
- DISARMED: 1971
  - 1447 zone stop < 0.30% (moves with the 5m ATR)
  - 511 1H trend not STRONG
  - 8 zone removed by the engine
  - 4 against the 1H trend
  - 1 1H trend not STRONG; against the 1H trend
- TOUCH_SKIP: 115
  - 111 WAIT: zone younger than 2 h
  - 3 1H trend not STRONG
  - 1 SLOW approach (<= 2 ATR in 30 min)
- WATCH_START: 80
- MARK: 35
- CONFIRM_REJECT: 33
  - 31 RR < 2 after fees
  - 1 1H trend not STRONG; RR 1.40 after fees < 2.0
  - 1 1H trend not STRONG; RR 0.94 after fees < 2.0
- WATCH_END: 80
  - 51 1m close beyond the far edge
  - 12 BOS reached but the confirmation gates failed
  - 9 price reached the leg extreme before a confirmation
  - 5 zone FILLED / removed by the engine
  - 2 SIGNAL
  - 1 zone BROKEN
- ENTRY_SKIP: 0
- Trades: 2 (exits: {'BREAK-EVEN': 1, 'TARGET': 1}, median hold 217 min)

## Funnel C: limit at the near edge, no confirmation, 2025-26 (all 4 coins)

- Zones armed (unique): 405; arm events 2158 (a zone re-arms after a disarm)
- DISARMED: 1971
  - 1447 zone stop < 0.30% (moves with the 5m ATR)
  - 511 1H trend not STRONG
  - 8 zone removed by the engine
  - 4 against the 1H trend
  - 1 1H trend not STRONG; against the 1H trend
- TOUCH_SKIP: 112
  - 111 WAIT: zone younger than 2 h
  - 1 SLOW approach (<= 2 ATR in 30 min)
- WATCH_START: 75
- MARK: 0
- CONFIRM_REJECT: 21
  - 21 RR < 2 after fees
- WATCH_END: 75
  - 54 SIGNAL
  - 21 limit
- ENTRY_SKIP: 1
  - 1 position already open on the symbol
- Trades: 53 (exits: {'STOP': 32, 'BREAK-EVEN': 13, 'TARGET': 8}, median hold 26 min)

## Funnel D: A without the 4H filter, 2025-26 (all 4 coins)

- Zones armed (unique): 565; arm events 2773 (a zone re-arms after a disarm)
- DISARMED: 2513
  - 1869 zone stop < 0.30% (moves with the 5m ATR)
  - 626 1H trend not STRONG
  - 10 zone removed by the engine
  - 7 against the 1H trend
  - 1 1H trend not STRONG; against the 1H trend
- TOUCH_SKIP: 160
  - 153 WAIT: zone younger than 2 h
  - 4 SLOW approach (<= 2 ATR in 30 min)
  - 3 1H trend not STRONG
- WATCH_START: 109
- MARK: 48
- CONFIRM_REJECT: 46
  - 37 RR < 2 after fees
  - 2 order flow 0/5 < 2
  - 1 1H trend not STRONG; RR 1.40 after fees < 2.0
  - 1 1H trend not STRONG; RR 0.48 after fees < 2.0
  - 1 1H trend not STRONG; RR 0.94 after fees < 2.0
  - 1 order flow 1/5 < 2
  - 1 1H trend not STRONG; RR 0.82 after fees < 2.0
  - 1 1H trend not STRONG; RR 0.08 after fees < 2.0
- WATCH_END: 109
  - 71 1m close beyond the far edge
  - 16 BOS reached but the confirmation gates failed
  - 12 price reached the leg extreme before a confirmation
  - 6 zone FILLED / removed by the engine
  - 2 zone BROKEN
  - 2 SIGNAL
- ENTRY_SKIP: 0
- Trades: 2 (exits: {'BREAK-EVEN': 1, 'TARGET': 1}, median hold 131 min)
