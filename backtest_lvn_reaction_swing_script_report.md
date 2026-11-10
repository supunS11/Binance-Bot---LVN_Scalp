# Script LVNs (LVN/HVN <= 0.50, time at price <= 0.50): do LVNs react better than random levels? 4H/15m zones

Main columns: BTC, ETH, SOL, XRP, 2025-10-19 to 2026-10-19. 1st / 2nd half and 2024-25 (BTC, ETH, 2024-10-19 to 2025-10-19) show only LVN - random at 1 ATR.
Reaction = price moves 1 or 2 x 15m ATR from the near edge before a 1m close beyond the far edge, within 3 days of the first touch. No zone widening.

## 15m zones

| Set | LVN n | LVN 1 ATR % | LVN 2 ATR % | Random n | Random 1 ATR % | Random 2 ATR % | LVN - random, 1 ATR (95%) | 1st half | 2nd half | 2024-25 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| All touches | 1031 | 27.9 | 16.1 | 1400 | 25.7 | 15.4 | +2.2 (-1.3 to +5.8) | +3.5 | +0.9 | +2.5 |
| 4H trend on the zone side | 505 | 28.5 | 16.0 | 692 | 25.9 | 15.9 | +2.6 (-2.5 to +7.8) | +3.1 | +2.1 | +1.4 |
| Depth: LVN/HVN <= 0.50 (random: all) | 1031 | 27.9 | 16.1 | 1400 | 25.7 | 15.4 | +2.2 (-1.3 to +5.8) | +3.5 | +0.9 | +2.5 |
| Fast: time at price <= 0.5 x leg average | 1013 | 27.8 | 16.2 | 403 | 26.8 | 13.9 | +1.0 (-4.1 to +6.2) | +1.1 | +1.0 | +5.8 |
|   not: Fast: time at price <= 0.5 x leg average | 18 | 33.3 | 11.1 | 997 | 25.3 | 16.0 | +8.1 (-13.9 to +30.0) | +16.2 | -1.8 | +13.4 |
| Middle: 38-62% of the leg | 367 | 23.2 | 11.7 | 464 | 28.9 | 17.0 | -5.7 (-11.7 to +0.3) | -5.5 | -5.9 | +5.3 |
|   not: Middle: 38-62% of the leg | 664 | 30.6 | 18.5 | 936 | 24.1 | 14.6 | +6.4 (+2.0 to +10.9) | +8.7 | +4.2 | +1.2 |
| Nested in a 4H LVN | 70 | 31.4 | 17.1 | 76 | 25.0 | 11.8 | +6.4 (-8.2 to +21.0) | +8.4 | +2.3 | +0.0 |
|   not: Nested in a 4H LVN | 961 | 27.7 | 16.0 | 1324 | 25.8 | 15.6 | +1.9 (-1.8 to +5.6) | +3.1 | +0.7 | +2.6 |
| Leg efficiency >= 0.30 | 824 | 28.0 | 16.0 | 1088 | 28.2 | 16.8 | -0.2 (-4.3 to +3.9) | +1.0 | -1.5 | +1.6 |
|   not: Leg efficiency >= 0.30 | 207 | 27.5 | 16.4 | 312 | 17.0 | 10.6 | +10.5 (+3.2 to +17.9) | +11.8 | +9.2 | +5.9 |
| Leg made a BOS | 972 | 28.8 | 16.6 | 1307 | 26.4 | 15.8 | +2.4 (-1.3 to +6.1) | +4.2 | +0.5 | +3.3 |
|   not: Leg made a BOS | 59 | 13.6 | 8.5 | 93 | 16.1 | 10.8 | -2.6 (-14.1 to +8.9) | -7.4 | +2.5 | -9.9 |
| Leg delta >= 5% in direction | 730 | 28.8 | 16.3 | 1026 | 25.2 | 15.8 | +3.5 (-0.7 to +7.7) | +7.9 | -0.1 | +3.8 |
|   not: Leg delta >= 5% in direction | 301 | 25.9 | 15.6 | 374 | 27.0 | 14.4 | -1.1 (-7.8 to +5.6) | -4.5 | +5.2 | -0.7 |
| Leg volume >= 2 x median | 817 | 28.6 | 16.2 | 1092 | 26.4 | 15.5 | +2.3 (-1.8 to +6.3) | +4.3 | -0.1 | +1.5 |
|   not: Leg volume >= 2 x median | 214 | 25.2 | 15.9 | 308 | 23.4 | 15.3 | +1.9 (-5.6 to +9.4) | -0.2 | +3.5 | +7.0 |
| Combined: Fast + Depth (random: Fast) | 1013 | 27.8 | 16.2 | 403 | 26.8 | 13.9 | +1.0 (-4.1 to +6.2) | +1.1 | +1.0 | +5.8 |
| Combined: Fast + Depth + BOS + delta (random: Fast + BOS + delta) | 685 | 29.2 | 16.6 | 266 | 25.6 | 14.3 | +3.6 (-2.6 to +9.9) | +10.6 | -2.3 | +7.8 |

## 4H zones

| Set | LVN n | LVN 1 ATR % | LVN 2 ATR % | Random n | Random 1 ATR % | Random 2 ATR % | LVN - random, 1 ATR (95%) | 1st half | 2nd half | 2024-25 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| All touches | 36 | 50.0 | 38.9 | 25 | 48.0 | 40.0 | +2.0 (-23.5 to +27.5) | +22.2 | -11.8 | +38.0 |
| 4H trend on the zone side | 13 | 46.2 | 23.1 | 16 | 43.8 | 31.2 | +2.4 (-34.0 to +38.8) | +37.1 | -21.2 | +47.8 |
| Depth: LVN/HVN <= 0.50 (random: all) | 36 | 50.0 | 38.9 | 25 | 48.0 | 40.0 | +2.0 (-23.5 to +27.5) | +22.2 | -11.8 | +38.0 |
| Fast: time at price <= 0.5 x leg average | 36 | 50.0 | 38.9 | 14 | 42.9 | 35.7 | +7.1 (-23.5 to +37.8) | +22.2 | -1.0 | +54.7 |
|   not: Fast: time at price <= 0.5 x leg average | 0 | - | - | 11 | 54.5 | 45.5 | - | - | - | - |
| Middle: 38-62% of the leg | 19 | 63.2 | 47.4 | 10 | 70.0 | 50.0 | -6.8 (-42.6 to +28.9) | +35.0 | -33.3 | -40.0 |
|   not: Middle: 38-62% of the leg | 17 | 35.3 | 29.4 | 15 | 33.3 | 33.3 | +2.0 (-31.0 to +34.9) | +10.0 | -7.8 | +45.2 |
| Leg efficiency >= 0.30 | 27 | 48.1 | 40.7 | 24 | 50.0 | 41.7 | -1.9 (-29.3 to +25.6) | +16.7 | -13.8 | +33.5 |
|   not: Leg efficiency >= 0.30 | 9 | 55.6 | 33.3 | 1 | 0.0 | 0.0 | +55.6 (+23.1 to +88.0) | - | +40.0 | +66.7 |
| Leg made a BOS | 36 | 50.0 | 38.9 | 25 | 48.0 | 40.0 | +2.0 (-23.5 to +27.5) | +22.2 | -11.8 | +41.1 |
|   not: Leg made a BOS | 0 | - | - | 0 | - | - | - | - | - | +0.0 |
| Leg delta >= 5% in direction | 4 | 50.0 | 25.0 | 5 | 20.0 | 20.0 | +30.0 (-30.3 to +90.3) | +33.3 | +75.0 | +100.0 |
|   not: Leg delta >= 5% in direction | 32 | 50.0 | 40.6 | 20 | 55.0 | 45.0 | -5.0 (-32.8 to +22.8) | +22.5 | -25.5 | +20.0 |
| Leg volume >= 2 x median | 12 | 66.7 | 66.7 | 9 | 33.3 | 33.3 | +33.3 (-7.4 to +74.1) | +41.7 | +16.7 | +14.3 |
|   not: Leg volume >= 2 x median | 24 | 41.7 | 25.0 | 16 | 56.2 | 43.8 | -14.6 (-45.9 to +16.7) | +6.7 | -27.1 | +57.5 |
| Combined: Fast + Depth (random: Fast) | 36 | 50.0 | 38.9 | 14 | 42.9 | 35.7 | +7.1 (-23.5 to +37.8) | +22.2 | -1.0 | +54.7 |
| Combined: Fast + Depth + BOS + delta (random: Fast + BOS + delta) | 4 | 50.0 | 25.0 | 2 | 0.0 | 0.0 | +50.0 (+1.0 to +99.0) | - | +100.0 | +100.0 |
