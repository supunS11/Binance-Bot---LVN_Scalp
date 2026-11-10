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
| **C: limit at the near edge, no confirmation**, 2025-26 | 53 | 0.04 | 30.2 | 25 | -0.163 | -0.636 to +0.377 | -8.6 | 12.2 | 0.44 |
|   1st half | 29 | 0.04 | 34.5 | 31 | -0.329 | -0.817 to +0.271 | -9.5 | 11.7 | 0.49 |
|   2nd half | 24 | 0.03 | 25.0 | 17 | +0.038 | -0.791 to +1.024 | +0.9 | 7.6 | 0.42 |
|   2024-25 (BTC, ETH) | 23 | 0.03 | 26.1 | 22 | -0.253 | -1.045 to +0.977 | -5.8 | 19.5 | 0.44 |
| **E: A with min RR 1.5**, 2025-26 | 1 | 0.00 | 100.0 | 100 | +0.000 | +0.000 to +0.000 | +0.0 | 0.0 | 1.10 |
|   1st half | 1 | 0.00 | 100.0 | 100 | +0.000 | +0.000 to +0.000 | +0.0 | 0.0 | 1.10 |
|   2nd half | 0 | | | | | | | | |
|   2024-25 (BTC, ETH) | 1 | 0.00 | 0.0 | 0 | -1.073 | -1.073 to -1.073 | -1.1 | 1.1 | 1.36 |
| **F: A with the target at the 1.272 extension**, 2025-26 | 1 | 0.00 | 100.0 | 100 | +0.000 | +0.000 to +0.000 | +0.0 | 0.0 | 1.10 |
|   1st half | 1 | 0.00 | 100.0 | 100 | +0.000 | +0.000 to +0.000 | +0.0 | 0.0 | 1.10 |
|   2nd half | 0 | | | | | | | | |
|   2024-25 (BTC, ETH) | 1 | 0.00 | 0.0 | 0 | -1.073 | -1.073 to -1.073 | -1.1 | 1.1 | 1.36 |
| **G: A, retest limit at the CHoCH level when RR at the close < 2**, 2025-26 | 1 | 0.00 | 100.0 | 100 | +0.000 | +0.000 to +0.000 | +0.0 | 0.0 | 1.10 |
|   1st half | 1 | 0.00 | 100.0 | 100 | +0.000 | +0.000 to +0.000 | +0.0 | 0.0 | 1.10 |
|   2nd half | 0 | | | | | | | | |
|   2024-25 (BTC, ETH) | 0 | | | | | | | | |

## Per coin, 2025-26

| Set | Coin | Trades | Avg net R | Total R |
|---|---|---:|---:|---:|
| A | BTCUSDT | 0 | +nan | +0.0 |
| A | ETHUSDT | 0 | +nan | +0.0 |
| A | SOLUSDT | 0 | +nan | +0.0 |
| A | XRPUSDT | 1 | +0.000 | +0.0 |
| C | BTCUSDT | 6 | -0.328 | -2.0 |
| C | ETHUSDT | 13 | -0.329 | -4.3 |
| C | SOLUSDT | 13 | -0.587 | -7.6 |
| C | XRPUSDT | 21 | +0.250 | +5.3 |
| E | BTCUSDT | 0 | +nan | +0.0 |
| E | ETHUSDT | 0 | +nan | +0.0 |
| E | SOLUSDT | 0 | +nan | +0.0 |
| E | XRPUSDT | 1 | +0.000 | +0.0 |
| F | BTCUSDT | 0 | +nan | +0.0 |
| F | ETHUSDT | 0 | +nan | +0.0 |
| F | SOLUSDT | 0 | +nan | +0.0 |
| F | XRPUSDT | 1 | +0.000 | +0.0 |
| G | BTCUSDT | 0 | +nan | +0.0 |
| G | ETHUSDT | 0 | +nan | +0.0 |
| G | SOLUSDT | 0 | +nan | +0.0 |
| G | XRPUSDT | 1 | +0.000 | +0.0 |

## Funnel A: bot as live (CHoCH + 2 of 5 order flow gates; liq / book not in data), 2025-26 (all 4 coins)

- Zones armed (unique): 405; arm events 2158 (a zone re-arms after a disarm)
- DISARMED: 1971
  - 1447 zone stop < 0.30% (moves with the 5m ATR)
  - 511 1H trend not STRONG
  - 8 zone removed by the engine
  - 4 against the 1H trend
  - 1 1H trend not STRONG; against the 1H trend
- TOUCH_SKIP: 116
  - 111 WAIT: zone younger than 2 h
  - 4 1H trend not STRONG
  - 1 SLOW approach (<= 2 ATR in 30 min)
- WATCH_START: 79
- MARK: 38
- CONFIRM_REJECT: 37
  - 33 RR < 2 after fees
  - 1 1H trend not STRONG; RR 1.40 after fees < 2.0
  - 1 1H trend not STRONG; RR 0.94 after fees < 2.0
  - 1 1H trend not STRONG; RR 1.89 after fees < 2.0
  - 1 order flow 0/5 < 2
- WATCH_END: 79
  - 49 1m close beyond the far edge
  - 14 BOS reached but the confirmation gates failed
  - 9 price reached the leg extreme before a confirmation
  - 5 zone FILLED / removed by the engine
  - 1 zone BROKEN
  - 1 SIGNAL
- ENTRY_SKIP: 0
- Trades: 1 (exits: {'BREAK-EVEN': 1}, median hold 124 min)

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

## Funnel E: A with min RR 1.5, 2025-26 (all 4 coins)

- Zones armed (unique): 405; arm events 2158 (a zone re-arms after a disarm)
- DISARMED: 1971
  - 1447 zone stop < 0.30% (moves with the 5m ATR)
  - 511 1H trend not STRONG
  - 8 zone removed by the engine
  - 4 against the 1H trend
  - 1 1H trend not STRONG; against the 1H trend
- TOUCH_SKIP: 116
  - 111 WAIT: zone younger than 2 h
  - 4 1H trend not STRONG
  - 1 SLOW approach (<= 2 ATR in 30 min)
- WATCH_START: 79
- MARK: 38
- CONFIRM_REJECT: 37
  - 31 RR < 2 after fees
  - 2 order flow 0/5 < 2
  - 1 order flow 1/5 < 2
  - 1 1H trend not STRONG; RR 1.40 after fees < 1.5
  - 1 1H trend not STRONG; RR 0.94 after fees < 1.5
  - 1 1H trend not STRONG; order flow 1/5 < 2
- WATCH_END: 79
  - 49 1m close beyond the far edge
  - 14 BOS reached but the confirmation gates failed
  - 9 price reached the leg extreme before a confirmation
  - 5 zone FILLED / removed by the engine
  - 1 zone BROKEN
  - 1 SIGNAL
- ENTRY_SKIP: 0
- Trades: 1 (exits: {'BREAK-EVEN': 1}, median hold 124 min)

## Funnel F: A with the target at the 1.272 extension, 2025-26 (all 4 coins)

- Zones armed (unique): 405; arm events 2158 (a zone re-arms after a disarm)
- DISARMED: 1971
  - 1447 zone stop < 0.30% (moves with the 5m ATR)
  - 511 1H trend not STRONG
  - 8 zone removed by the engine
  - 4 against the 1H trend
  - 1 1H trend not STRONG; against the 1H trend
- TOUCH_SKIP: 116
  - 111 WAIT: zone younger than 2 h
  - 4 1H trend not STRONG
  - 1 SLOW approach (<= 2 ATR in 30 min)
- WATCH_START: 79
- MARK: 38
- CONFIRM_REJECT: 37
  - 31 RR < 2 after fees
  - 2 order flow 0/5 < 2
  - 1 order flow 1/5 < 2
  - 1 1H trend not STRONG; RR 1.96 after fees < 2.0
  - 1 1H trend not STRONG; RR 1.33 after fees < 2.0
  - 1 1H trend not STRONG; order flow 1/5 < 2
- WATCH_END: 79
  - 49 1m close beyond the far edge
  - 14 BOS reached but the confirmation gates failed
  - 9 price reached the leg extreme before a confirmation
  - 5 zone FILLED / removed by the engine
  - 1 zone BROKEN
  - 1 SIGNAL
- ENTRY_SKIP: 0
- Trades: 1 (exits: {'BREAK-EVEN': 1}, median hold 124 min)

## Funnel G: A, retest limit at the CHoCH level when RR at the close < 2, 2025-26 (all 4 coins)

- Zones armed (unique): 405; arm events 2158 (a zone re-arms after a disarm)
- DISARMED: 1971
  - 1447 zone stop < 0.30% (moves with the 5m ATR)
  - 511 1H trend not STRONG
  - 8 zone removed by the engine
  - 4 against the 1H trend
  - 1 1H trend not STRONG; against the 1H trend
- TOUCH_SKIP: 116
  - 111 WAIT: zone younger than 2 h
  - 4 1H trend not STRONG
  - 1 SLOW approach (<= 2 ATR in 30 min)
- WATCH_START: 79
- MARK: 38
- CONFIRM_REJECT: 36
  - 32 RR < 2 after fees
  - 1 1H trend not STRONG; RR 1.40 after fees < 2.0
  - 1 1H trend not STRONG; RR 0.94 after fees < 2.0
  - 1 1H trend not STRONG; RR 1.89 after fees < 2.0
  - 1 order flow 0/5 < 2
- WATCH_END: 79
  - 48 1m close beyond the far edge
  - 14 BOS reached but the confirmation gates failed
  - 9 price reached the leg extreme before a confirmation
  - 5 zone FILLED / removed by the engine
  - 2 SIGNAL
  - 1 zone BROKEN
- ENTRY_SKIP: 1
  - 1 retest limit not filled (30 min or target first)
- Trades: 1 (exits: {'BREAK-EVEN': 1}, median hold 124 min)
