# Nested LVN backtest: BTCUSDT, ETHUSDT

Train 2025-10-19 to 2026-04-19, test 2026-04-19 to 2026-10-19. Entry first touch of a FRESH zone, stop 0.5 x ATR beyond zone, target 2.0R, cost 0.040% fee + 0.010% slippage per side. R is net of costs.

## All trades, bias-aligned

| Set | Trades | Win % | Avg R | 95% range of Avg R | Total R | PF | Max DD (R) | Median stop % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 15m nested | 31 | 45.2 | +0.076 | -0.435 to +0.649 | +2.4 | 1.11 | 5.8 | 0.34 |
| 15m non-nested | 1536 | 32.7 | -0.527 | -0.601 to -0.455 | -808.7 | 0.48 | 808.7 | 0.22 |
| 4H | 90 | 44.4 | +0.051 | -0.246 to +0.352 | +4.6 | 1.07 | 18.7 | 0.37 |

## Train, bias-aligned

| Set | Trades | Win % | Avg R | 95% range of Avg R | Total R | PF | Max DD (R) | Median stop % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 15m nested | 20 | 45.0 | +0.093 | -0.523 to +0.698 | +1.9 | 1.14 | 5.8 | 0.38 |
| 15m non-nested | 698 | 33.8 | -0.399 | -0.505 to -0.288 | -278.7 | 0.57 | 289.6 | 0.27 |
| 4H | 49 | 53.1 | +0.354 | -0.068 to +0.772 | +17.4 | 1.63 | 6.2 | 0.48 |

## Test, bias-aligned

| Set | Trades | Win % | Avg R | 95% range of Avg R | Total R | PF | Max DD (R) | Median stop % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 15m nested | 11 | 45.5 | +0.045 | -0.815 to +0.912 | +0.5 | 1.06 | 4.9 | 0.31 |
| 15m non-nested | 838 | 31.7 | -0.632 | -0.725 to -0.534 | -530.0 | 0.42 | 530.0 | 0.19 |
| 4H | 41 | 34.1 | -0.311 | -0.726 to +0.130 | -12.8 | 0.65 | 16.5 | 0.30 |

## All trades, no bias filter

| Set | Trades | Win % | Avg R | 95% range of Avg R | Total R | PF | Max DD (R) | Median stop % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 15m nested | 60 | 36.7 | -0.243 | -0.613 to +0.136 | -14.6 | 0.72 | 16.5 | 0.33 |
| 15m non-nested | 2528 | 33.1 | -0.513 | -0.572 to -0.457 | -1297.1 | 0.49 | 1297.1 | 0.22 |
| 4H | 168 | 37.5 | -0.163 | -0.390 to +0.063 | -27.3 | 0.80 | 44.6 | 0.37 |

## Bias-aligned, one open trade at a time per symbol + set

| Set | Trades | Win % | Avg R | 95% range of Avg R | Total R | PF | Max DD (R) | Median stop % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 15m nested | 30 | 46.7 | +0.124 | -0.402 to +0.661 | +3.7 | 1.18 | 5.8 | 0.35 |
| 15m non-nested | 1276 | 32.4 | -0.527 | -0.603 to -0.449 | -672.4 | 0.48 | 672.4 | 0.23 |
| 4H | 89 | 44.9 | +0.066 | -0.240 to +0.367 | +5.9 | 1.09 | 17.4 | 0.37 |

## Bias-aligned breakdown

| Set | Trades | Win % | Avg R | 95% range of Avg R | Total R | PF | Max DD (R) | Median stop % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT 15m nested | 15 | 40.0 | -0.133 | -0.913 to +0.650 | -2.0 | 0.83 | 5.9 | 0.30 |
| BTCUSDT 15m non-nested | 790 | 34.2 | -0.555 | -0.659 to -0.452 | -438.4 | 0.47 | 438.4 | 0.19 |
| BTCUSDT 4H | 46 | 54.3 | +0.293 | -0.128 to +0.713 | +13.5 | 1.49 | 11.2 | 0.31 |
| ETHUSDT 15m nested | 16 | 50.0 | +0.272 | -0.457 to +1.027 | +4.4 | 1.45 | 4.6 | 0.53 |
| ETHUSDT 15m non-nested | 746 | 31.1 | -0.496 | -0.594 to -0.398 | -370.3 | 0.49 | 374.3 | 0.26 |
| ETHUSDT 4H | 44 | 34.1 | -0.202 | -0.622 to +0.211 | -8.9 | 0.75 | 13.1 | 0.50 |
| 15m nested long | 15 | 40.0 | -0.105 | -0.912 to +0.706 | -1.6 | 0.87 | 5.8 | 0.32 |
| 15m nested short | 16 | 50.0 | +0.246 | -0.482 to +0.974 | +3.9 | 1.40 | 5.8 | 0.44 |
| 15m non-nested long | 747 | 33.7 | -0.512 | -0.609 to -0.407 | -382.6 | 0.49 | 384.6 | 0.22 |
| 15m non-nested short | 789 | 31.7 | -0.540 | -0.637 to -0.437 | -426.1 | 0.47 | 432.5 | 0.23 |
| 4H long | 40 | 45.0 | +0.109 | -0.341 to +0.595 | +4.4 | 1.16 | 6.2 | 0.40 |
| 4H short | 50 | 44.0 | +0.005 | -0.395 to +0.426 | +0.2 | 1.01 | 19.2 | 0.35 |

## Engine counts

- BTCUSDT: {'z4': 158, 'z15': 2199, 'legs4': 34, 'legs15': 555, 'pretouched': 777, 'bad_risk': 0, 'open_end': 0}
- ETHUSDT: {'z4': 147, 'z15': 2100, 'legs4': 33, 'legs15': 573, 'pretouched': 748, 'bad_risk': 0, 'open_end': 0}
