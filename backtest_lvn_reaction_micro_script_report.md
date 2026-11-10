# Script LVNs (LVN/HVN <= 0.50, time at price <= 0.50): do LVNs react better than random levels? 15m/1m scalp zones

Main columns: BTC, ETH, SOL, XRP, 2026-07-19 to 2026-10-19. 1st / 2nd half and 2024-25 (BTC, ETH, 2025-07-19 to 2025-10-19) show only LVN - random at 1 ATR. Profiles from 1m bars only (no seconds data).
Reaction = price moves 1 or 2 x 1m ATR from the near edge (widened 0.25 x 1m ATR) before a 1m close beyond the far edge, within 4.8 hours of the first touch.

## 1m zones

| Set | LVN n | LVN 1 ATR % | LVN 2 ATR % | Random n | Random 1 ATR % | Random 2 ATR % | LVN - random, 1 ATR (95%) | 1st half | 2nd half | 2024-25 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| All touches | 1455 | 40.8 | 27.9 | 3274 | 35.2 | 25.0 | +5.6 (+2.6 to +8.6) | +4.9 | +6.2 | +4.8 |
| Script tradable (STRONG 15m, 1H, stop >= 0.30%) | 18 | 50.0 | 27.8 | 55 | 41.8 | 30.9 | +8.2 (-18.3 to +34.7) | +40.6 | -11.5 | +50.6 |
| STRONG 15m + 1H, no min stop | 223 | 47.1 | 33.6 | 524 | 35.7 | 24.4 | +11.4 (+3.7 to +19.1) | +14.1 | +9.1 | +3.7 |
| Depth: LVN/HVN <= 0.50 (random: all) | 1455 | 40.8 | 27.9 | 3274 | 35.2 | 25.0 | +5.6 (+2.6 to +8.6) | +4.9 | +6.2 | +4.8 |
| Fast: time at price <= 0.5 x leg average | 1209 | 40.9 | 28.2 | 467 | 30.8 | 20.1 | +10.0 (+5.0 to +15.0) | +13.0 | +7.5 | +9.9 |
|   not: Fast: time at price <= 0.5 x leg average | 246 | 40.2 | 26.4 | 2807 | 35.9 | 25.8 | +4.3 (-2.0 to +10.7) | -0.7 | +8.2 | +6.3 |
| Middle: 38-62% of the leg | 511 | 43.6 | 30.1 | 855 | 43.3 | 30.4 | +0.4 (-5.1 to +5.8) | +2.7 | -1.5 | -2.0 |
|   not: Middle: 38-62% of the leg | 944 | 39.2 | 26.7 | 2419 | 32.3 | 23.0 | +6.9 (+3.2 to +10.5) | +4.9 | +8.6 | +6.7 |
| Nested in a 15m LVN | 77 | 33.8 | 19.5 | 161 | 34.2 | 27.3 | -0.4 (-13.3 to +12.5) | -5.2 | +5.7 | +11.4 |
|   not: Nested in a 15m LVN | 1378 | 41.1 | 28.4 | 3113 | 35.2 | 24.8 | +5.9 (+2.8 to +9.0) | +5.6 | +6.2 | +4.4 |
| Leg efficiency >= 0.30 | 883 | 40.8 | 28.8 | 1886 | 38.5 | 27.6 | +2.2 (-1.7 to +6.1) | +0.9 | +3.3 | +4.1 |
|   not: Leg efficiency >= 0.30 | 572 | 40.7 | 26.6 | 1388 | 30.6 | 21.4 | +10.1 (+5.4 to +14.8) | +10.0 | +10.3 | +5.9 |
| Leg made a BOS | 1303 | 41.7 | 28.3 | 2867 | 35.4 | 25.0 | +6.3 (+3.1 to +9.5) | +6.5 | +6.1 | +5.5 |
|   not: Leg made a BOS | 152 | 32.2 | 24.3 | 407 | 33.4 | 24.6 | -1.2 (-9.9 to +7.6) | -9.3 | +6.4 | -6.5 |
| Leg delta >= 5% in direction | 1214 | 41.4 | 28.3 | 2685 | 35.2 | 24.5 | +6.1 (+2.8 to +9.4) | +6.2 | +6.1 | +5.0 |
|   not: Leg delta >= 5% in direction | 241 | 37.8 | 25.7 | 589 | 35.0 | 27.0 | +2.8 (-4.4 to +10.0) | -2.3 | +6.5 | +2.2 |
| Leg volume >= 2 x median | 924 | 41.6 | 28.5 | 2090 | 34.4 | 24.5 | +7.1 (+3.3 to +10.9) | +5.7 | +8.3 | +4.9 |
|   not: Leg volume >= 2 x median | 531 | 39.4 | 26.9 | 1184 | 36.5 | 25.7 | +2.9 (-2.1 to +7.9) | +3.5 | +2.3 | +4.6 |
| Combined: Fast + Depth (random: Fast) | 1209 | 40.9 | 28.2 | 467 | 30.8 | 20.1 | +10.0 (+5.0 to +15.0) | +13.0 | +7.5 | +9.9 |
| Combined: Fast + Depth + BOS + delta (random: Fast + BOS + delta) | 916 | 42.4 | 29.3 | 377 | 31.0 | 19.1 | +11.3 (+5.7 to +17.0) | +15.7 | +7.2 | +11.5 |

## 15m zones

| Set | LVN n | LVN 1 ATR % | LVN 2 ATR % | Random n | Random 1 ATR % | Random 2 ATR % | LVN - random, 1 ATR (95%) | 1st half | 2nd half | 2024-25 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| All touches | 195 | 54.9 | 43.1 | 430 | 47.2 | 35.6 | +7.7 (-0.8 to +16.1) | +8.6 | +6.3 | +6.5 |
| Script tradable (STRONG 15m) | 72 | 54.2 | 45.8 | 182 | 45.1 | 34.1 | +9.1 (-4.5 to +22.7) | +10.0 | +7.4 | +13.9 |
| Depth: LVN/HVN <= 0.50 (random: all) | 195 | 54.9 | 43.1 | 430 | 47.2 | 35.6 | +7.7 (-0.8 to +16.1) | +8.6 | +6.3 | +6.5 |
| Fast: time at price <= 0.5 x leg average | 194 | 54.6 | 42.8 | 116 | 43.1 | 27.6 | +11.5 (+0.1 to +23.0) | +17.9 | +6.8 | +6.3 |
|   not: Fast: time at price <= 0.5 x leg average | 1 | 100.0 | 100.0 | 314 | 48.7 | 38.5 | +51.3 (+45.7 to +56.8) | +52.7 | - | -54.8 |
| Middle: 38-62% of the leg | 63 | 58.7 | 47.6 | 134 | 61.2 | 52.2 | -2.5 (-17.2 to +12.2) | -5.5 | +1.1 | +1.5 |
|   not: Middle: 38-62% of the leg | 132 | 53.0 | 40.9 | 296 | 40.9 | 28.0 | +12.2 (+2.0 to +22.3) | +15.0 | +8.6 | +8.5 |
| Leg efficiency >= 0.30 | 150 | 55.3 | 43.3 | 339 | 51.0 | 38.9 | +4.3 (-5.3 to +13.9) | +7.8 | +0.3 | +2.5 |
|   not: Leg efficiency >= 0.30 | 45 | 53.3 | 42.2 | 91 | 33.0 | 23.1 | +20.4 (+2.9 to +37.9) | +11.5 | +27.7 | +21.8 |
| Leg made a BOS | 188 | 55.3 | 43.6 | 404 | 48.3 | 36.4 | +7.1 (-1.6 to +15.7) | +9.5 | +4.0 | +5.3 |
|   not: Leg made a BOS | 7 | 42.9 | 28.6 | 26 | 30.8 | 23.1 | +12.1 (-28.6 to +52.8) | -10.8 | +69.2 | +18.8 |
| Leg delta >= 5% in direction | 169 | 54.4 | 41.4 | 364 | 49.2 | 36.5 | +5.3 (-3.8 to +14.4) | +6.2 | +3.9 | +1.1 |
|   not: Leg delta >= 5% in direction | 26 | 57.7 | 53.8 | 66 | 36.4 | 30.3 | +21.3 (-0.9 to +43.6) | +24.2 | +21.0 | +18.3 |
| Leg volume >= 2 x median | 116 | 56.0 | 44.8 | 269 | 45.7 | 35.7 | +10.3 (-0.5 to +21.1) | +11.5 | +8.9 | +7.0 |
|   not: Leg volume >= 2 x median | 79 | 53.2 | 40.5 | 161 | 49.7 | 35.4 | +3.5 (-10.0 to +16.9) | +4.3 | +1.7 | +5.8 |
| Combined: Fast + Depth (random: Fast) | 194 | 54.6 | 42.8 | 116 | 43.1 | 27.6 | +11.5 (+0.1 to +23.0) | +17.9 | +6.8 | +6.3 |
| Combined: Fast + Depth + BOS + delta (random: Fast + BOS + delta) | 161 | 54.7 | 41.6 | 88 | 47.7 | 30.7 | +6.9 (-6.0 to +19.9) | +18.2 | -1.7 | -6.6 |
