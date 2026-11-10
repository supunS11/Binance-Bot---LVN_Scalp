# 15m/1m scalp: which LVNs break? S/D zones and confirmation entries

BTC, ETH, SOL, XRP, 2026-07-19 to 2026-10-19 (2024-25 = BTC, ETH, 2025-07-19 to 2025-10-19). 1m script LVNs, first touch. Held = 1 x 1m ATR from the near edge
before a 1m close beyond the far edge; Fixed stop = +1 ATR from the near edge before a 1m close 1 ATR beyond the near edge (same for every zone, so width does not matter). Halves and 2024-25 show the set minus all LVNs.

### All touches

| Set | n | Median width (ATR) | Held 1 ATR % | Fixed 1 ATR stop: held % | Held - all LVNs (95%) | 1st half | 2nd half | 2024-25 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| All script LVNs | 1455 | 0.58 | 40.8 | 48.2 | +0.0 (-3.6 to +3.6) | +0.0 | +0.0 | +0.0 |
| Own leg S/D zone (base) instead of the LVN | 3925 | 1.09 | 57.0 | 55.6 | +16.2 (+13.2 to +19.2) | +17.9 | +14.6 | +12.9 |
| Leg has no standard S/D base | 565 | 0.60 | 41.1 | 47.1 | +0.3 (-4.5 to +5.1) | -1.2 | +1.6 | +0.1 |
| Own S/D gap <= 1 ATR | 344 | 0.59 | 46.5 | 54.4 | +5.8 (-0.1 to +11.6) | +3.9 | +7.6 | +10.6 |
| Own S/D gap 1-3 ATR | 381 | 0.56 | 40.7 | 49.9 | -0.1 (-5.6 to +5.5) | -0.1 | -0.1 | -3.7 |
| Own S/D gap > 3 ATR | 165 | 0.56 | 27.9 | 35.8 | -12.9 (-20.2 to -5.6) | -4.0 | -21.2 | -10.5 |
| Fresh 15m S/D within 2 ATR beyond | 9 | 0.47 | 55.6 | 66.7 | +14.8 (-17.8 to +47.4) | +26.4 | +8.8 | -20.6 |
| No fresh 15m S/D within 2 ATR beyond | 1446 | 0.58 | 40.7 | 48.1 | -0.1 (-3.7 to +3.5) | -0.1 | -0.1 | +0.1 |
| Inside a fresh 15m S/D | 3 | 0.71 | 66.7 | 66.7 | +25.9 (-27.5 to +79.3) | +59.8 | -41.2 | -7.3 |
| Approach <= 2 ATR in 30 min | 470 | 0.57 | 26.4 | 31.7 | -14.4 (-19.1 to -9.7) | -12.4 | -16.2 | -14.7 |
| Approach 2-4 ATR in 30 min | 745 | 0.58 | 46.3 | 55.2 | +5.6 (+1.2 to +9.9) | +3.5 | +7.3 | +6.7 |
| Approach > 4 ATR in 30 min | 240 | 0.62 | 51.7 | 59.2 | +10.9 (+4.1 to +17.7) | +13.7 | +8.4 | +5.6 |
| Best: gap <= 1, approach > 2 ATR, age >= 2 h | 104 | 0.60 | 57.7 | 62.5 | +16.9 (+7.1 to +26.8) | +20.9 | +12.8 | +10.9 |
| Age < 2 h | 966 | 0.58 | 35.2 | 43.3 | -5.6 (-9.5 to -1.6) | -5.8 | -5.4 | -3.5 |
| Age 2-12 h | 339 | 0.58 | 48.4 | 56.3 | +7.6 (+1.7 to +13.5) | +7.4 | +7.9 | +1.9 |
| Age >= 12 h | 150 | 0.65 | 59.3 | 62.0 | +18.6 (+10.3 to +26.8) | +19.2 | +18.0 | +15.7 |

Confirmation entry (instead of a limit at the near edge):

| Entry | Touches | Confirmed % | Held after confirm % | Held per touch % |
|---|---:|---:|---:|---:|
| Limit at near edge | 1455 | 100 | 40.8 | 40.8 |
| 1m close back out | 1455 | 58.5 | 57.5 | 33.6 |
| 5m close back out | 1455 | 50.2 | 64.2 | 32.2 |
| S/D zone, limit | 3925 | 100 | 57.0 | 57.0 |
| S/D zone, 5m close back out | 3925 | 63.8 | 70.0 | 44.7 |

### STRONG 15m + 1H trend on the zone side

| Set | n | Median width (ATR) | Held 1 ATR % | Fixed 1 ATR stop: held % | Held - all LVNs (95%) | 1st half | 2nd half | 2024-25 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| All script LVNs | 223 | 0.61 | 47.1 | 56.1 | +0.0 (-9.3 to +9.3) | +0.0 | +0.0 | +0.0 |
| Own leg S/D zone (base) instead of the LVN | 624 | 0.96 | 56.9 | 57.4 | +9.8 (+2.2 to +17.4) | +12.0 | +7.3 | +12.7 |
| Leg has no standard S/D base | 89 | 0.61 | 48.3 | 53.9 | +1.2 (-11.0 to +13.5) | +1.5 | +0.8 | -0.2 |
| Own S/D gap <= 1 ATR | 59 | 0.61 | 44.1 | 54.2 | -3.0 (-17.3 to +11.2) | -6.6 | +0.6 | +5.9 |
| Own S/D gap 1-3 ATR | 59 | 0.58 | 50.8 | 64.4 | +3.8 (-10.6 to +18.1) | +6.5 | +2.9 | -7.2 |
| Own S/D gap > 3 ATR | 16 | 0.61 | 37.5 | 43.8 | -9.6 (-34.2 to +15.0) | +1.5 | -20.8 | +4.2 |
| Fresh 15m S/D within 2 ATR beyond | 1 | 0.61 | 100.0 | 100.0 | +52.9 (+46.4 to +59.5) | +51.5 | - | -39.6 |
| No fresh 15m S/D within 2 ATR beyond | 222 | 0.61 | 46.8 | 55.9 | -0.2 (-9.5 to +9.0) | -0.5 | +0.0 | +0.3 |
| Inside a fresh 15m S/D | 0 | nan | - | - | - | - | - | - |
| Approach <= 2 ATR in 30 min | 65 | 0.60 | 26.2 | 36.9 | -20.9 (-33.5 to -8.4) | -25.5 | -17.6 | -7.1 |
| Approach 2-4 ATR in 30 min | 116 | 0.60 | 50.9 | 59.5 | +3.8 (-7.4 to +15.0) | +6.5 | +0.6 | +3.8 |
| Approach > 4 ATR in 30 min | 42 | 0.62 | 69.0 | 76.2 | +22.0 (+6.5 to +37.4) | +16.2 | +26.2 | -0.2 |
| Best: gap <= 1, approach > 2 ATR, age >= 2 h | 16 | 0.54 | 75.0 | 87.5 | +27.9 (+5.7 to +50.1) | +21.5 | +37.5 | +3.3 |
| Age < 2 h | 135 | 0.60 | 36.3 | 46.7 | -10.8 (-21.2 to -0.4) | -2.6 | -17.5 | -1.5 |
| Age 2-12 h | 61 | 0.62 | 55.7 | 62.3 | +8.7 (-5.4 to +22.7) | -0.1 | +18.5 | +2.4 |
| Age >= 12 h | 27 | 0.50 | 81.5 | 88.9 | +34.4 (+18.3 to +50.4) | +18.1 | +43.1 | +0.4 |

Confirmation entry (instead of a limit at the near edge):

| Entry | Touches | Confirmed % | Held after confirm % | Held per touch % |
|---|---:|---:|---:|---:|
| Limit at near edge | 223 | 100 | 47.1 | 47.1 |
| 1m close back out | 223 | 66.4 | 61.5 | 40.8 |
| 5m close back out | 223 | 57.4 | 71.1 | 40.8 |
| S/D zone, limit | 624 | 100 | 56.9 | 56.9 |
| S/D zone, 5m close back out | 624 | 65.1 | 70.7 | 46.0 |


1m chart: every time window is / 5. Approach = last 6 min (rows say 30 min). Age is in units of 12 min (rows say h: 2 h = 24 min, 12 h = 2.4 h). Reaction within 4.8 h of the first touch.