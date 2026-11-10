# 1H/5m scalp: which LVNs break? S/D zones and confirmation entries

BTC, ETH, SOL, XRP, 2025-10-19 to 2026-10-19 (2024-25 = BTC, ETH). 5m script LVNs, first touch. Held = 1 x 5m ATR from the near edge
before a 1m close beyond the far edge; Fixed stop = +1 ATR from the near edge before a 1m close 1 ATR beyond the near edge (same for every zone, so width does not matter). Halves and 2024-25 show the set minus all LVNs.

### All touches

| Set | n | Median width (ATR) | Held 1 ATR % | Fixed 1 ATR stop: held % | Held - all LVNs (95%) | 1st half | 2nd half | 2024-25 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| All script LVNs | 2881 | 0.47 | 38.2 | 50.4 | +0.0 (-2.5 to +2.5) | +0.0 | +0.0 | +0.0 |
| Own leg S/D zone (base) instead of the LVN | 2226 | 1.12 | 58.8 | 56.1 | +20.7 (+18.0 to +23.4) | +21.1 | +20.3 | +19.3 |
| Leg has no standard S/D base | 870 | 0.47 | 36.6 | 49.1 | -1.6 (-5.3 to +2.0) | -0.8 | -2.5 | -1.8 |
| Own S/D gap <= 1 ATR | 1097 | 0.45 | 42.7 | 54.8 | +4.5 (+1.1 to +7.9) | +5.0 | +3.9 | +5.3 |
| Own S/D gap 1-3 ATR | 733 | 0.48 | 37.9 | 51.2 | -0.3 (-4.2 to +3.7) | -1.3 | +0.8 | -1.9 |
| Own S/D gap > 3 ATR | 181 | 0.48 | 19.9 | 26.5 | -18.3 (-24.4 to -12.2) | -19.1 | -17.3 | -9.5 |
| Fresh 1H S/D within 2 ATR beyond | 46 | 0.49 | 50.0 | 63.0 | +11.8 (-2.7 to +26.4) | +8.1 | +17.5 | +2.1 |
| No fresh 1H S/D within 2 ATR beyond | 2835 | 0.47 | 38.0 | 50.2 | -0.2 (-2.7 to +2.3) | -0.2 | -0.2 | -0.0 |
| Inside a fresh 1H S/D | 10 | 0.47 | 60.0 | 60.0 | +21.8 (-8.6 to +52.2) | +1.7 | +41.9 | +14.5 |
| Approach <= 2 ATR in 30 min | 866 | 0.48 | 26.8 | 36.8 | -11.4 (-14.8 to -7.9) | -11.0 | -11.8 | -14.2 |
| Approach 2-4 ATR in 30 min | 1543 | 0.46 | 41.2 | 54.9 | +3.0 (-0.1 to +6.0) | +4.3 | +1.7 | +4.0 |
| Approach > 4 ATR in 30 min | 472 | 0.47 | 49.4 | 60.4 | +11.2 (+6.3 to +16.0) | +6.6 | +15.7 | +12.5 |
| Best: gap <= 1, approach > 2 ATR, age >= 2 h | 328 | 0.45 | 48.8 | 58.8 | +10.6 (+4.9 to +16.3) | +7.4 | +13.8 | +9.0 |
| Age < 2 h | 1919 | 0.47 | 34.3 | 46.2 | -3.9 (-6.7 to -1.1) | -2.5 | -5.3 | -4.4 |
| Age 2-12 h | 666 | 0.48 | 44.7 | 57.5 | +6.6 (+2.4 to +10.7) | +2.9 | +10.3 | +6.3 |
| Age >= 12 h | 296 | 0.45 | 48.6 | 61.1 | +10.5 (+4.5 to +16.4) | +8.8 | +12.3 | +12.6 |

Confirmation entry (instead of a limit at the near edge):

| Entry | Touches | Confirmed % | Held after confirm % | Held per touch % |
|---|---:|---:|---:|---:|
| Limit at near edge | 2881 | 100 | 38.2 | 38.2 |
| 1m close back out | 2881 | 68.0 | 49.2 | 33.5 |
| 5m close back out | 2881 | 60.7 | 52.6 | 31.9 |
| S/D zone, limit | 2226 | 100 | 58.8 | 58.8 |
| S/D zone, 5m close back out | 2226 | 75.7 | 67.0 | 50.8 |

### STRONG 1H + 4H trend on the zone side

| Set | n | Median width (ATR) | Held 1 ATR % | Fixed 1 ATR stop: held % | Held - all LVNs (95%) | 1st half | 2nd half | 2024-25 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| All script LVNs | 467 | 0.47 | 40.5 | 52.2 | +0.0 (-6.3 to +6.3) | +0.0 | +0.0 | +0.0 |
| Own leg S/D zone (base) instead of the LVN | 370 | 1.01 | 57.8 | 56.2 | +17.4 (+10.6 to +24.1) | +21.5 | +14.0 | +23.0 |
| Leg has no standard S/D base | 119 | 0.46 | 30.3 | 42.0 | -10.2 (-19.6 to -0.8) | -12.7 | -8.4 | -3.9 |
| Own S/D gap <= 1 ATR | 175 | 0.44 | 47.4 | 57.1 | +7.0 (-1.7 to +15.6) | +8.4 | +5.5 | +4.7 |
| Own S/D gap 1-3 ATR | 140 | 0.49 | 42.9 | 58.6 | +2.4 (-6.9 to +11.7) | +2.0 | +3.0 | +0.5 |
| Own S/D gap > 3 ATR | 33 | 0.48 | 30.3 | 36.4 | -10.2 (-26.5 to +6.1) | -7.3 | -14.5 | -0.7 |
| Fresh 1H S/D within 2 ATR beyond | 9 | 0.54 | 22.2 | 55.6 | -18.2 (-45.8 to +9.3) | -10.6 | -41.8 | +32.4 |
| No fresh 1H S/D within 2 ATR beyond | 458 | 0.46 | 40.8 | 52.2 | +0.4 (-6.0 to +6.7) | +0.3 | +0.4 | -0.5 |
| Inside a fresh 1H S/D | 2 | 0.40 | 50.0 | 50.0 | +9.5 (-59.9 to +79.0) | -39.1 | +58.2 | - |
| Approach <= 2 ATR in 30 min | 124 | 0.48 | 33.1 | 43.5 | -7.4 (-16.8 to +2.0) | -13.3 | -1.4 | -10.6 |
| Approach 2-4 ATR in 30 min | 249 | 0.46 | 39.8 | 51.8 | -0.7 (-8.2 to +6.8) | +6.2 | -7.9 | -1.7 |
| Approach > 4 ATR in 30 min | 94 | 0.48 | 52.1 | 64.9 | +11.7 (+0.6 to +22.7) | +0.9 | +19.3 | +20.1 |
| Best: gap <= 1, approach > 2 ATR, age >= 2 h | 61 | 0.46 | 50.8 | 54.1 | +10.3 (-3.0 to +23.7) | +7.0 | +12.5 | +11.5 |
| Age < 2 h | 292 | 0.46 | 36.0 | 48.6 | -4.5 (-11.6 to +2.6) | -0.7 | -8.4 | -7.4 |
| Age 2-12 h | 145 | 0.47 | 46.9 | 57.9 | +6.4 (-2.8 to +15.7) | +1.2 | +10.8 | +8.8 |
| Age >= 12 h | 30 | 0.46 | 53.3 | 60.0 | +12.9 (-5.5 to +31.3) | +2.5 | +19.3 | +20.3 |

Confirmation entry (instead of a limit at the near edge):

| Entry | Touches | Confirmed % | Held after confirm % | Held per touch % |
|---|---:|---:|---:|---:|
| Limit at near edge | 467 | 100 | 40.5 | 40.5 |
| 1m close back out | 467 | 71.3 | 52.0 | 37.0 |
| 5m close back out | 467 | 63.4 | 55.7 | 35.3 |
| S/D zone, limit | 370 | 100 | 57.8 | 57.8 |
| S/D zone, 5m close back out | 370 | 76.5 | 68.2 | 52.2 |
