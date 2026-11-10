# Nested LVN backtest: BTCUSDT, ETHUSDT

Train 2025-10-19 to 2026-04-19, test 2026-04-19 to 2026-10-19. Entry first touch of a FRESH zone, stop 0.5 x ATR beyond zone, target 2.0R, cost 0.040% fee + 0.010% slippage per side. R is net of costs.

## All trades, bias-aligned

| Set | Trades | Win % | Avg R | 95% range of Avg R | Total R | PF | Max DD (R) | Median stop % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 5m A+ | 172 | 26.2 | -0.840 | -1.048 to -0.628 | -144.4 | 0.31 | 146.0 | 0.18 |
| 5m nested (not A+) | 16 | 43.8 | -0.268 | -1.013 to +0.493 | -4.3 | 0.70 | 9.3 | 0.17 |
| 5m non-nested | 3890 | 30.1 | -0.974 | -1.025 to -0.927 | -3789.7 | 0.27 | 3789.7 | 0.13 |
| 1H | 436 | 28.0 | -0.757 | -0.889 to -0.626 | -330.0 | 0.34 | 330.4 | 0.19 |

## Train, bias-aligned

| Set | Trades | Win % | Avg R | 95% range of Avg R | Total R | PF | Max DD (R) | Median stop % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 5m A+ | 83 | 28.9 | -0.577 | -0.868 to -0.258 | -47.9 | 0.44 | 49.5 | 0.23 |
| 5m nested (not A+) | 8 | 50.0 | +0.024 | -1.090 to +1.097 | +0.2 | 1.03 | 2.9 | 0.28 |
| 5m non-nested | 1805 | 31.9 | -0.780 | -0.851 to -0.707 | -1407.0 | 0.35 | 1407.0 | 0.16 |
| 1H | 211 | 28.0 | -0.651 | -0.835 to -0.467 | -137.4 | 0.39 | 137.8 | 0.24 |

## Test, bias-aligned

| Set | Trades | Win % | Avg R | 95% range of Avg R | Total R | PF | Max DD (R) | Median stop % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 5m A+ | 89 | 23.6 | -1.085 | -1.349 to -0.799 | -96.5 | 0.21 | 101.9 | 0.14 |
| 5m nested (not A+) | 8 | 37.5 | -0.560 | -1.391 to +0.483 | -4.5 | 0.45 | 7.1 | 0.16 |
| 5m non-nested | 2085 | 28.6 | -1.143 | -1.212 to -1.071 | -2382.7 | 0.22 | 2382.7 | 0.11 |
| 1H | 225 | 28.0 | -0.856 | -1.036 to -0.670 | -192.6 | 0.30 | 194.6 | 0.16 |

## All trades, no bias filter

| Set | Trades | Win % | Avg R | 95% range of Avg R | Total R | PF | Max DD (R) | Median stop % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 5m A+ | 172 | 26.2 | -0.840 | -1.048 to -0.628 | -144.4 | 0.31 | 146.0 | 0.18 |
| 5m nested (not A+) | 136 | 36.0 | -0.519 | -0.773 to -0.270 | -70.6 | 0.50 | 76.5 | 0.19 |
| 5m non-nested | 6565 | 30.0 | -0.979 | -1.014 to -0.940 | -6425.9 | 0.27 | 6426.3 | 0.13 |
| 1H | 776 | 31.2 | -0.615 | -0.710 to -0.513 | -477.3 | 0.42 | 477.7 | 0.20 |

## Bias-aligned, one open trade at a time per symbol + set

| Set | Trades | Win % | Avg R | 95% range of Avg R | Total R | PF | Max DD (R) | Median stop % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 5m A+ | 164 | 26.8 | -0.801 | -0.998 to -0.580 | -131.4 | 0.32 | 133.0 | 0.18 |
| 5m nested (not A+) | 15 | 40.0 | -0.404 | -1.143 to +0.424 | -6.1 | 0.58 | 9.3 | 0.16 |
| 5m non-nested | 3351 | 30.2 | -0.956 | -1.008 to -0.904 | -3204.0 | 0.28 | 3204.0 | 0.13 |
| 1H | 421 | 28.0 | -0.756 | -0.889 to -0.626 | -318.2 | 0.34 | 318.6 | 0.19 |

## Bias-aligned breakdown

| Set | Trades | Win % | Avg R | 95% range of Avg R | Total R | PF | Max DD (R) | Median stop % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT 5m A+ | 84 | 26.2 | -0.908 | -1.211 to -0.600 | -76.3 | 0.27 | 76.3 | 0.15 |
| BTCUSDT 5m nested (not A+) | 5 | 0.0 | -1.648 | -1.832 to -1.382 | -8.2 | 0.00 | 8.2 | 0.14 |
| BTCUSDT 5m non-nested | 2014 | 28.6 | -1.157 | -1.228 to -1.086 | -2329.5 | 0.21 | 2329.5 | 0.11 |
| BTCUSDT 1H | 217 | 32.7 | -0.732 | -0.931 to -0.520 | -158.8 | 0.37 | 159.2 | 0.16 |
| ETHUSDT 5m A+ | 88 | 26.1 | -0.775 | -1.052 to -0.467 | -68.2 | 0.34 | 69.8 | 0.21 |
| ETHUSDT 5m nested (not A+) | 11 | 63.6 | +0.359 | -0.483 to +1.213 | +3.9 | 1.64 | 5.1 | 0.18 |
| ETHUSDT 5m non-nested | 1876 | 31.7 | -0.778 | -0.847 to -0.708 | -1460.3 | 0.35 | 1462.5 | 0.16 |
| ETHUSDT 1H | 219 | 23.3 | -0.782 | -0.938 to -0.607 | -171.2 | 0.31 | 171.2 | 0.23 |
| 5m A+ long | 72 | 31.9 | -0.682 | -1.018 to -0.320 | -49.1 | 0.39 | 50.7 | 0.20 |
| 5m A+ short | 100 | 22.0 | -0.953 | -1.205 to -0.677 | -95.3 | 0.25 | 95.3 | 0.17 |
| 5m nested (not A+) long | 5 | 40.0 | -0.419 | -1.604 to +0.810 | -2.1 | 0.56 | 3.6 | 0.16 |
| 5m nested (not A+) short | 11 | 45.5 | -0.200 | -1.098 to +0.735 | -2.2 | 0.77 | 5.7 | 0.18 |
| 5m non-nested long | 1891 | 29.0 | -1.046 | -1.117 to -0.972 | -1977.3 | 0.24 | 1977.3 | 0.12 |
| 5m non-nested short | 1999 | 31.2 | -0.907 | -0.976 to -0.839 | -1812.4 | 0.30 | 1813.7 | 0.14 |
| 1H long | 217 | 24.9 | -0.852 | -1.031 to -0.669 | -184.9 | 0.28 | 184.9 | 0.19 |
| 1H short | 219 | 31.1 | -0.662 | -0.857 to -0.476 | -145.1 | 0.40 | 146.1 | 0.19 |

## Bias-aligned, 4H context filter

| Set | Trades | Win % | Avg R | 95% range of Avg R | Total R | PF | Max DD (R) | Median stop % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 5m nested (not A+), not blocked | 16 | 43.8 | -0.268 | -1.013 to +0.493 | -4.3 | 0.70 | 9.3 | 0.17 |
| 5m nested (not A+), blocked | 0 | | | | | | | |
| 5m non-nested, not blocked | 3821 | 30.0 | -0.979 | -1.028 to -0.932 | -3742.0 | 0.27 | 3742.0 | 0.13 |
| 5m non-nested, blocked | 69 | 36.2 | -0.692 | -1.049 to -0.334 | -47.7 | 0.40 | 50.5 | 0.13 |
| 1H, not blocked | 435 | 27.8 | -0.761 | -0.890 to -0.636 | -331.2 | 0.34 | 331.6 | 0.19 |
| 1H, blocked | 1 | 100.0 | +1.209 | +1.209 to +1.209 | +1.2 | inf | 0.0 | 0.13 |

## Engine counts

- BTCUSDT: {'zones_4h': 158, 'zones_1h': 753, 'zones_5m': 5714, 'legs_4h': 34, 'legs_1h': 174, 'legs_5m': 1703, 'pretouched': 2197, 'bad_risk': 1, 'open_end': 0}
- ETHUSDT: {'zones_4h': 147, 'zones_1h': 641, 'zones_5m': 5286, 'legs_4h': 33, 'legs_1h': 155, 'legs_5m': 1695, 'pretouched': 1879, 'bad_risk': 1, 'open_end': 1}
