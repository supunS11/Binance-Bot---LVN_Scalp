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
| **C: limit at the near edge, no confirmation**, 2025-26 | 53 | 0.04 | 30.2 | 25 | -0.144 | -0.638 to +0.417 | -7.6 | 13.9 | 0.44 |
|   1st half | 29 | 0.04 | 34.5 | 31 | -0.329 | -0.817 to +0.271 | -9.5 | 11.7 | 0.49 |
|   2nd half | 24 | 0.03 | 25.0 | 17 | +0.081 | -0.764 to +1.070 | +1.9 | 5.1 | 0.40 |
|   2024-25 (BTC, ETH) | 22 | 0.03 | 27.3 | 23 | -0.211 | -1.007 to +0.961 | -4.6 | 18.3 | 0.44 |
| **H: rejection candle at the zone (1m close back beyond the near edge)**, 2025-26 | 35 | 0.02 | 34.3 | 20 | -0.083 | -0.685 to +0.615 | -2.9 | 9.5 | 0.52 |
|   1st half | 24 | 0.03 | 37.5 | 29 | -0.279 | -0.783 to +0.333 | -6.7 | 9.2 | 0.62 |
|   2nd half | 11 | 0.02 | 27.3 | 0 | +0.345 | -1.213 to +2.198 | +3.8 | 3.7 | 0.45 |
|   2024-25 (BTC, ETH) | 18 | 0.02 | 22.2 | 11 | -0.505 | -1.131 to +0.364 | -9.1 | 16.7 | 0.52 |
| **I: order flow candle at the zone (2 of: absorption, delta flip, CVD divergence)**, 2025-26 | 2 | 0.00 | 100.0 | 100 | +0.000 | +0.000 to +0.000 | +0.0 | 0.0 | 0.68 |
|   1st half | 2 | 0.00 | 100.0 | 100 | +0.000 | +0.000 to +0.000 | +0.0 | 0.0 | 0.68 |
|   2nd half | 0 | | | | | | | | |
|   2024-25 (BTC, ETH) | 1 | 0.00 | 0.0 | 0 | -1.192 | -1.192 to -1.192 | -1.2 | 1.2 | 0.52 |

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
| C | XRPUSDT | 21 | +0.298 | +6.3 |
| H | BTCUSDT | 4 | -0.247 | -1.0 |
| H | ETHUSDT | 7 | -0.473 | -3.3 |
| H | SOLUSDT | 9 | -0.303 | -2.7 |
| H | XRPUSDT | 15 | +0.275 | +4.1 |
| I | BTCUSDT | 0 | +nan | +0.0 |
| I | ETHUSDT | 0 | +nan | +0.0 |
| I | SOLUSDT | 0 | +nan | +0.0 |
| I | XRPUSDT | 2 | +0.000 | +0.0 |

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

## Funnel H: rejection candle at the zone (1m close back beyond the near edge), 2025-26 (all 4 coins)

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
- MARK: 63
- CONFIRM_REJECT: 26
  - 26 RR < 2 after fees
- WATCH_END: 75
  - 37 SIGNAL
  - 26 confirmation candle, plan rejected
  - 11 1m close beyond the far edge
  - 1 price reached the leg extreme before a confirmation
- ENTRY_SKIP: 2
  - 1 position already open on the symbol
  - 1 RR < 2 at the fill price
- Trades: 35 (exits: {'STOP': 22, 'TARGET': 6, 'BREAK-EVEN': 7}, median hold 36 min)

## Funnel I: order flow candle at the zone (2 of: absorption, delta flip, CVD divergence), 2025-26 (all 4 coins)

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
- MARK: 6
- CONFIRM_REJECT: 4
  - 4 RR < 2 after fees
- WATCH_END: 75
  - 36 1m close beyond the far edge
  - 26 no confirmation within 30 min of the touch
  - 7 price reached the leg extreme before a confirmation
  - 4 confirmation candle, plan rejected
  - 2 SIGNAL
- ENTRY_SKIP: 0
- Trades: 2 (exits: {'BREAK-EVEN': 2}, median hold 325 min)

## Every CONFIRM_REJECT (all coins, both periods)

- A BTCUSDT 2025: RR 1.50 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.00%, reward 1.75%); order flow 1/5 < 2 (passed: delta_shift)
- A BTCUSDT 2025: RR 0.99 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.94%, reward 1.13%); order flow 1/5 < 2 (passed: delta_shift)
- A BTCUSDT 2025: RR 0.61 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.18%, reward 0.88%); order flow 1/5 < 2 (passed: delta_shift)
- A ETHUSDT 2025: RR 1.10 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.84%, reward 1.13%); order flow 0/5 < 2 (passed: none)
- A ETHUSDT 2025: 1H trend not STRONG; RR 1.40 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.71%, reward 1.23%); order flow 1/5 < 2 (passed: delta_shift)
- A ETHUSDT 2025: RR 0.66 after fees < 2.0 (target: leg extreme (swing liquidity); risk 2.71%, reward 1.95%); order flow 1/5 < 2 (passed: delta_shift)
- A ETHUSDT 2025: RR 0.23 after fees < 2.0 (target: leg extreme (swing liquidity); risk 3.69%, reward 0.98%); order flow 1/5 < 2 (passed: delta_shift)
- A ETHUSDT 2025: RR 0.40 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.54%, reward 0.75%); order flow 1/5 < 2 (passed: delta_shift)
- A ETHUSDT 2025: 1H trend not STRONG; RR 0.94 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.93%, reward 2.00%); order flow 1/5 < 2 (passed: delta_shift)
- A ETHUSDT 2025: 1H trend not STRONG; RR 1.89 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.24%, reward 2.63%); order flow 1/5 < 2 (passed: delta_shift)
- A ETHUSDT 2025: RR 1.87 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.24%, reward 2.61%); order flow 0/5 < 2 (passed: none)
- A ETHUSDT 2025: RR 0.25 after fees < 2.0 (target: in front of opposing S/D; risk 1.12%, reward 0.40%)
- A ETHUSDT 2025: RR -0.05 after fees < 2.0 (target: in front of opposing S/D; risk 1.51%, reward 0.02%)
- A ETHUSDT 2025: RR 0.16 after fees < 2.0 (target: in front of opposing S/D; risk 1.43%, reward 0.35%); order flow 1/5 < 2 (passed: delta_shift)
- A ETHUSDT 2025: RR 0.08 after fees < 2.0 (target: in front of opposing S/D; risk 1.54%, reward 0.24%); order flow 1/5 < 2 (passed: delta_shift)
- A ETHUSDT 2025: RR 0.28 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.11%, reward 0.44%); order flow 1/5 < 2 (passed: delta_shift)
- A SOLUSDT 2025: RR 1.02 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.84%, reward 2.09%)
- A SOLUSDT 2025: RR 0.47 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.17%, reward 0.69%); order flow 1/5 < 2 (passed: delta_shift)
- A SOLUSDT 2025: RR 0.88 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.29%, reward 1.32%)
- A SOLUSDT 2025: RR 0.44 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.71%, reward 0.91%)
- A XRPUSDT 2025: RR 1.13 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.43%, reward 1.82%); order flow 1/5 < 2 (passed: cvd_divergence)
- A XRPUSDT 2025: RR 1.00 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.54%, reward 1.73%)
- A XRPUSDT 2025: RR 1.24 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.39%, reward 1.94%); order flow 1/5 < 2 (passed: cvd_divergence)
- A XRPUSDT 2025: RR 0.08 after fees < 2.0 (target: leg extreme (swing liquidity); risk 2.52%, reward 0.32%)
- A XRPUSDT 2025: RR 0.34 after fees < 2.0 (target: leg extreme (swing liquidity); risk 2.01%, reward 0.81%)
- A XRPUSDT 2025: RR 0.36 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.12%, reward 0.54%); order flow 1/5 < 2 (passed: delta_shift)
- A XRPUSDT 2025: RR 0.24 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.23%, reward 0.42%); order flow 1/5 < 2 (passed: delta_shift)
- A XRPUSDT 2025: RR 0.38 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.43%, reward 0.68%)
- A XRPUSDT 2025: RR 0.81 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.02%, reward 1.01%); order flow 1/5 < 2 (passed: delta_shift)
- A XRPUSDT 2025: RR 0.50 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.26%, reward 0.78%); order flow 1/5 < 2 (passed: delta_shift)
- A XRPUSDT 2025: RR 0.10 after fees < 2.0 (target: leg extreme (swing liquidity); risk 3.43%, reward 0.44%); order flow 1/5 < 2 (passed: delta_shift)
- A XRPUSDT 2025: order flow 0/5 < 2 (passed: none)
- A XRPUSDT 2025: RR 0.94 after fees < 2.0 (target: in front of opposing S/D; risk 1.94%, reward 2.01%); order flow 0/5 < 2 (passed: none)
- A XRPUSDT 2025: RR 0.38 after fees < 2.0 (target: in front of opposing 5m LVN; risk 1.02%, reward 0.52%); order flow 1/5 < 2 (passed: delta_shift)
- A XRPUSDT 2025: RR 0.38 after fees < 2.0 (target: in front of opposing 5m LVN; risk 1.02%, reward 0.52%); order flow 1/5 < 2 (passed: delta_shift)
- A XRPUSDT 2025: RR 0.99 after fees < 2.0 (target: in front of opposing S/D; risk 0.79%, reward 0.98%); order flow 1/5 < 2 (passed: delta_shift)
- A XRPUSDT 2025: RR 0.99 after fees < 2.0 (target: in front of opposing S/D; risk 0.79%, reward 0.98%); order flow 1/5 < 2 (passed: delta_shift)
- A BTCUSDT 2024: RR 1.59 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.36%, reward 2.43%)
- A BTCUSDT 2024: RR 0.94 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.84%, reward 1.92%); order flow 1/5 < 2 (passed: absorption)
- A BTCUSDT 2024: RR 0.70 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.75%, reward 1.39%); order flow 1/5 < 2 (passed: delta_shift)
- A BTCUSDT 2024: RR 0.25 after fees < 2.0 (target: in front of opposing 5m LVN; risk 2.27%, reward 0.69%); order flow 0/5 < 2 (passed: none)
- A BTCUSDT 2024: RR 0.51 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.94%, reward 1.15%); order flow 1/5 < 2 (passed: delta_shift)
- A BTCUSDT 2024: RR 0.70 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.66%, reward 1.33%); order flow 1/5 < 2 (passed: delta_shift)
- A ETHUSDT 2024: RR -0.05 after fees < 2.0 (target: in front of opposing S/D; risk 1.43%, reward 0.03%); order flow 0/5 < 2 (passed: none)
- A ETHUSDT 2024: RR 0.52 after fees < 2.0 (target: leg extreme (swing liquidity); risk 2.66%, reward 1.54%); order flow 1/5 < 2 (passed: delta_shift)
- A ETHUSDT 2024: RR 1.45 after fees < 2.0 (target: in front of opposing 5m LVN; risk 2.34%, reward 3.65%); order flow 0/5 < 2 (passed: none)
- A ETHUSDT 2024: RR 0.65 after fees < 2.0 (target: leg extreme (swing liquidity); risk 3.20%, reward 2.26%); order flow 1/5 < 2 (passed: delta_shift)
- A ETHUSDT 2024: RR 1.50 after fees < 2.0 (target: leg extreme (swing liquidity); risk 2.05%, reward 3.32%); order flow 1/5 < 2 (passed: delta_shift)
- A ETHUSDT 2024: RR 1.50 after fees < 2.0 (target: leg extreme (swing liquidity); risk 2.05%, reward 3.32%); order flow 1/5 < 2 (passed: delta_shift)
- A ETHUSDT 2024: RR 0.83 after fees < 2.0 (target: leg extreme (swing liquidity); risk 2.81%, reward 2.52%); order flow 1/5 < 2 (passed: delta_shift)
- A ETHUSDT 2024: 1H trend not STRONG; RR 0.21 after fees < 2.0 (target: in front of opposing 5m LVN; risk 1.31%, reward 0.40%); order flow 1/5 < 2 (passed: delta_shift)
- A ETHUSDT 2024: 1H trend not STRONG; RR 0.21 after fees < 2.0 (target: in front of opposing S/D; risk 1.79%, reward 0.50%); order flow 1/5 < 2 (passed: delta_shift)
- A ETHUSDT 2024: RR 1.14 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.13%, reward 1.49%); order flow 1/5 < 2 (passed: delta_shift)
- A ETHUSDT 2024: RR 0.81 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.34%, reward 1.27%); order flow 1/5 < 2 (passed: delta_shift)
- A ETHUSDT 2024: RR 1.25 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.67%, reward 2.31%); order flow 0/5 < 2 (passed: none)
- A ETHUSDT 2024: RR 1.61 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.41%, reward 2.54%); order flow 1/5 < 2 (passed: delta_shift)
- A ETHUSDT 2024: RR 0.15 after fees < 2.0 (target: in front of opposing 5m LVN; risk 1.42%, reward 0.32%); order flow 0/5 < 2 (passed: none)
- A ETHUSDT 2024: RR 0.01 after fees < 2.0 (target: in front of opposing 5m LVN; risk 1.62%, reward 0.11%); order flow 0/5 < 2 (passed: none)
- A ETHUSDT 2024: RR 0.40 after fees < 2.0 (target: leg extreme (swing liquidity); risk 3.67%, reward 1.62%); order flow 1/5 < 2 (passed: delta_shift)
- A ETHUSDT 2024: RR 0.31 after fees < 2.0 (target: leg extreme (swing liquidity); risk 3.90%, reward 1.36%); order flow 1/5 < 2 (passed: delta_shift)
- A ETHUSDT 2024: 1H trend not STRONG; RR 0.95 after fees < 2.0 (target: leg extreme (swing liquidity); risk 2.50%, reward 2.57%); order flow 1/5 < 2 (passed: delta_shift)
- A ETHUSDT 2024: 1H trend not STRONG; RR 0.42 after fees < 2.0 (target: leg extreme (swing liquidity); risk 3.40%, reward 1.57%); order flow 1/5 < 2 (passed: delta_shift)
- A ETHUSDT 2024: RR 0.37 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.75%, reward 0.78%); order flow 0/5 < 2 (passed: none)
- A ETHUSDT 2024: RR 0.10 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.49%, reward 0.26%); order flow 0/5 < 2 (passed: none)
- C BTCUSDT 2025: RR 1.25 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.38%, reward 0.70%)
- C BTCUSDT 2025: RR 1.66 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.63%, reward 1.32%)
- C ETHUSDT 2025: RR 1.05 after fees < 2.0 (target: leg extreme (swing liquidity); risk 2.17%, reward 2.48%)
- C ETHUSDT 2025: RR 1.68 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.64%, reward 3.01%)
- C ETHUSDT 2025: RR 1.60 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.86%, reward 1.64%)
- C ETHUSDT 2025: RR 1.19 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.72%, reward 2.27%)
- C ETHUSDT 2025: RR 1.00 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.43%, reward 0.63%)
- C SOLUSDT 2025: RR 1.71 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.42%, reward 0.99%)
- C SOLUSDT 2025: RR 1.71 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.41%, reward 0.97%)
- C SOLUSDT 2025: RR 1.95 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.80%, reward 1.86%)
- C SOLUSDT 2025: RR 1.53 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.93%, reward 1.68%)
- C SOLUSDT 2025: RR 0.78 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.77%, reward 0.78%)
- C XRPUSDT 2025: RR 0.99 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.00%, reward 1.19%)
- C XRPUSDT 2025: RR 2.00 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.87%, reward 2.03%)
- C XRPUSDT 2025: RR 0.74 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.64%, reward 0.65%)
- C XRPUSDT 2025: RR 0.67 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.28%, reward 1.03%)
- C XRPUSDT 2025: RR 1.31 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.81%, reward 1.30%)
- C XRPUSDT 2025: RR 1.23 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.65%, reward 2.25%)
- C XRPUSDT 2025: RR 1.78 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.48%, reward 1.13%)
- C XRPUSDT 2025: RR 1.16 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.65%, reward 0.97%)
- C XRPUSDT 2025: RR 1.74 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.53%, reward 1.19%)
- C BTCUSDT 2024: RR 1.76 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.42%, reward 1.02%)
- C BTCUSDT 2024: RR 1.79 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.28%, reward 2.57%)
- C BTCUSDT 2024: RR 1.71 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.42%, reward 0.99%)
- C ETHUSDT 2024: RR 1.69 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.43%, reward 1.00%)
- C ETHUSDT 2024: RR 1.84 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.44%, reward 1.09%)
- C ETHUSDT 2024: RR 1.14 after fees < 2.0 (target: leg extreme (swing liquidity); risk 2.44%, reward 2.99%)
- C ETHUSDT 2024: RR 2.00 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.49%, reward 1.28%)
- C ETHUSDT 2024: RR 1.69 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.37%, reward 2.59%)
- C ETHUSDT 2024: RR 1.32 after fees < 2.0 (target: leg extreme (swing liquidity); risk 2.24%, reward 3.19%)
- H BTCUSDT 2025: RR 1.53 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.67%, reward 1.28%)
- H ETHUSDT 2025: RR 1.88 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.41%, reward 1.06%)
- H ETHUSDT 2025: RR 0.84 after fees < 2.0 (target: leg extreme (swing liquidity); risk 2.43%, reward 2.23%)
- H ETHUSDT 2025: RR 1.58 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.71%, reward 2.95%)
- H ETHUSDT 2025: RR 0.80 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.30%, reward 1.22%)
- H ETHUSDT 2025: RR 1.10 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.79%, reward 2.19%)
- H ETHUSDT 2025: RR 0.98 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.44%, reward 0.62%)
- H ETHUSDT 2025: RR 1.19 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.54%, reward 0.86%)
- H ETHUSDT 2025: RR 1.24 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.65%, reward 1.03%)
- H SOLUSDT 2025: RR 1.54 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.45%, reward 0.95%)
- H SOLUSDT 2025: RR 1.37 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.48%, reward 0.90%)
- H SOLUSDT 2025: RR 1.82 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.84%, reward 1.81%)
- H SOLUSDT 2025: RR 1.39 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.99%, reward 1.62%)
- H SOLUSDT 2025: RR 1.70 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.53%, reward 1.17%)
- H SOLUSDT 2025: RR 0.53 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.91%, reward 0.64%)
- H XRPUSDT 2025: RR 1.62 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.00%, reward 1.89%)
- H XRPUSDT 2025: RR 1.43 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.61%, reward 1.11%)
- H XRPUSDT 2025: RR 0.70 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.65%, reward 0.63%)
- H XRPUSDT 2025: RR 0.48 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.45%, reward 0.85%)
- H XRPUSDT 2025: RR 1.19 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.87%, reward 1.25%)
- H XRPUSDT 2025: RR 1.16 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.70%, reward 2.20%)
- H XRPUSDT 2025: RR 1.52 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.54%, reward 1.07%)
- H XRPUSDT 2025: RR 1.66 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.37%, reward 0.89%)
- H XRPUSDT 2025: RR 1.28 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.94%, reward 1.42%)
- H XRPUSDT 2025: RR 1.08 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.68%, reward 0.94%)
- H XRPUSDT 2025: RR 1.32 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.64%, reward 1.07%)
- H BTCUSDT 2024: RR 1.69 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.44%, reward 1.01%)
- H BTCUSDT 2024: RR 1.31 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.56%, reward 2.28%)
- H BTCUSDT 2024: RR 1.27 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.52%, reward 0.89%)
- H ETHUSDT 2024: RR 1.73 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.46%, reward 1.07%)
- H ETHUSDT 2024: RR 1.00 after fees < 2.0 (target: leg extreme (swing liquidity); risk 2.62%, reward 2.81%)
- H ETHUSDT 2024: RR 1.79 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.83%, reward 3.55%)
- H ETHUSDT 2024: RR 1.81 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.53%, reward 1.25%)
- H ETHUSDT 2024: RR 1.66 after fees < 2.0 (target: leg extreme (swing liquidity); risk 1.39%, reward 2.58%)
- H ETHUSDT 2024: RR 1.23 after fees < 2.0 (target: leg extreme (swing liquidity); risk 2.33%, reward 3.09%)
- I XRPUSDT 2025: RR 0.70 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.65%, reward 0.63%)
- I XRPUSDT 2025: RR 1.19 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.87%, reward 1.25%)
- I XRPUSDT 2025: RR 1.66 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.37%, reward 0.89%)
- I XRPUSDT 2025: RR 1.07 after fees < 2.0 (target: leg extreme (swing liquidity); risk 0.73%, reward 0.99%)
