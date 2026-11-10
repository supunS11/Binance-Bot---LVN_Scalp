# LVN scalp bot: handoff brief

Read this first. It sums up a long earlier chat (TradingView Pine indicator + Python backtests) so a new Claude session can build the bot.
The full chat export is in the zip in the user's Downloads folder, if a detail is missing here.

## The user

- Trades crypto USDT perpetuals (Binance). Builds TradingView Pine indicators.
- Writes in Singlish (Sinhala in Latin script). **Answer in Singlish.**
- Does not read code in depth: explain results plainly, with numbers.
- Wants honest test results; do not tune thresholds on the result.

## Goal

A bot that runs the full flow the user now does by hand with `Scalp_LVN_1H5m.pine` (5m chart, 1H HTF, 4H filter), and does it more accurately:

1. Find valid 5m / 1H LVN zones (same rules as the script).
2. While price pulls back to the zone, keep checking that the LVN is still valid.
3. When an LVN and a supply/demand zone are near each other, decide which zone to trade.
4. At the zone, wait for an **order flow confirmation** (the user never did this by hand).
5. Place the entry, and the SL / TP from **market structure**, with **RR at least 2:1**.
6. Manage the trade.

Start with 1H/5m only. The 15m/1m version (`Scalp_LVN_15m1m.pine`) exists but is not in scope yet.

## What exists (all in this folder)

| File | What it is |
|---|---|
| `Scalp_LVN_1H5m.pine` / `.txt` | The indicator the bot must follow. Source of truth for zone rules. |
| `Scalp_LVN_15m1m.pine` / `.txt` | Same script for a 1m chart (15m HTF, 1H filter). |
| `backtest.py` | Python port of the Pine logic: `Engine` (impulse legs), `find_lvns` (per-leg 1m volume profile), `run_symbol` (zones, status, nesting). Start the bot's zone engine from this. |
| `backtest_scalp_1h5m.py` | `strength()`: 1H trend + STRONG (ADX / DI / EMA50). |
| `backtest_lvn_reaction.py` | Reaction test: LVNs vs random levels, no TP/SL. |
| `backtest_lvn_break.py` | Which LVNs break: S/D gap, approach speed, zone age, confirmation entries. `base_zone()` = standard S/D. |
| `scan_zones.py` | Live scanner of Binance perps with the script rules (public data only). Good base for the bot's live data loop. |
| `backtest_*_report.md` | Results of every test. |
| `cache/`, `scan_cache/` | 1m candles (Binance), with taker buy volume (`tb`). |

## Zone rules (script defaults)

- **Impulse leg** (5m and 1H): size >= 4 x ATR, volume >= 1.5 x median (1H: 1.1 x), >= 70% of candles in the leg direction, efficiency >= 0.15, max 30 candles (1H: 16). The leg is final after a 30% pullback that is also >= 2 ATR. No BOS needed.
- **LVN**: 1m volume profile of the leg, 150 rows. A valley between two HVN peaks, not in the top / bottom 10% of the leg. Max 5 per leg.
  - Deep: LVN / HVN volume <= 0.50.
  - Fast: 1m bars at the zone middle / leg average per row <= 0.50.
- **Zone** = LVN widened 0.25 x 5m ATR on the entry side. It only counts if price has not come back to it since the impulse left it.
- **Trade filter**: 1H trend STRONG (ADX >= 20, DI on the trend side, close on the trend side of EMA 50), zone in the trend direction, 4H trend on the same side, stop >= 0.30%.
- **NESTED** = a 5m LVN inside a same-direction 1H LVN.
- **LVN quality** (added last, see the tests below):
  - Hide a 5m LVN if its far edge is > 3 x ATR from the proximal line of its own leg's S/D zone.
  - WAIT: no entry in the first 2 h after the zone is made.
  - SLOW warning: price travelled <= 2 ATR toward the zone in the last 30 min.

## Standard supply / demand (base candles)

This is the Sam Seiden / OTA method:

- Leg-out candle: body > 50% of its range. The first one in the leg direction.
- Base: the 1-6 candles with a body <= 50% of their range right before the leg-out.
- Demand: proximal = highest base body, distal = lowest base wick. Supply: the mirror.
- No base candles = no S/D zone.
- Code: `base_zone()` in `backtest_lvn_break.py`. Same logic is in both Pine scripts.

## Test method the user agreed to

- For the indicator: **no TP/SL backtest.** Judge LVNs by reaction only.
  - "Held" = price moves 1 x 5m ATR from the near edge before a 1m close beyond the far edge. First touch only.
- Data: BTC, ETH, SOL, XRP, 2025-10-19 to 2026-10-19. Check each half, and 2024-25 (BTC, ETH) as a second period.
- Fix thresholds before the run.
- For the bot, a TP/SL backtest **is** needed now, with fees (0.05% per side taker), because the bot places them.

## Results so far

- LVNs react better than random levels in the same leg: about +8 points.
- Script LVNs (deep + fast) held 38.2% of first touches (n = 2,881).
- What breaks an LVN (5m, standard S/D):

| Condition | Held % |
|---|---:|
| All script LVNs | 38.2 |
| Gap to own S/D > 3 ATR | 19.9 |
| Gap to own S/D <= 1 ATR | 42.7 |
| Slow approach (<= 2 ATR in 30 min) | 26.8 |
| Fast approach (> 4 ATR in 30 min) | 49.4 |
| Zone younger than 2 h | 34.3 |
| Zone 12 h or older | 48.6 |
| Gap <= 1 + approach > 2 + age >= 2 h | 48.8 |

- **S/D zone vs LVN:**
  - The S/D zone held 58.8%, but it is about 2.4 x wider (1.12 vs 0.47 ATR).
  - With the same 1 ATR stop for both: S/D 56.1%, LVN 50.4%. The S/D zone is a little better, with a bigger stop.
- **1H S/D near the LVN:** too few cases (n = 46) to tell.
- **Confirmation by candle close** (1m or 5m close back out of the zone):
  - Entries that confirmed held 49-53%.
  - Per touch it gives fewer winners (32-34% vs 38%), so it was not added.
- **Old TP/SL backtest** (`backtest_scalp_1h5m_report.md`, before the quality filters): a limit at the near edge, stop beyond the far edge + 0.5 ATR, 2R target, with fees.
  - It lost in every group: avg R -0.56 to -0.86.
  - The 5m stops are small (median 0.15-0.25%), so fees are a large part of 1R.
  - **The mechanical version has not made money yet.** The bot must show an edge on paper before any real money.

## Notes on the user's new requirements

1. **"If the pullback is fast, the LVN is not valid."** The data says the opposite.
   - A slow drift into the zone broke more (26.8% held). A fast push held better (49.4%).
   - The "fast" that helps is the impulse leg passing fast through the LVN price (time at price filter).
   - Show the user these numbers and agree on a rule before coding it.
2. **LVN or S/D, which zone?** Not tested as a trade yet. Test with TP/SL + fees:
   - LVN entry.
   - S/D entry.
   - LVN entry with the stop beyond the S/D distal line.
3. **Order flow confirmation.**
   - Free, real-time, from Binance USD-M futures:
     - `<symbol>@aggTrade`: taker side, so delta and CVD.
     - `<symbol>@depth` (100 / 500 ms): order book.
     - `<symbol>@forceOrder`: liquidations.
     - Open interest: REST polling (no WebSocket stream found).
   - CoinGlass API v4 (`open-api-v4.coinglass.com`, `CG-API-KEY` header):
     - Paid: Hobbyist $29/mo, 30 requests/min, data updates <= 1 min. Startup $79/mo, 80/min. Standard $299/mo, 300/min.
     - Too slow and rate-limited to confirm a 5m zone touch.
     - Useful for slower context only: aggregated OI, funding, liquidation maps across exchanges.
   - What can be tested now: delta at the touch, from the `tb` (taker buy volume) field in the cached 1m candles. Run the same held / broke test.
   - Order book and liquidation history are not in the cache. Record them live, then test on paper.
4. **SL / TP from market structure, RR >= 2:1.** Define it in code and test it with fees:
   - SL beyond the zone and the nearest protected swing (or the S/D distal line).
   - TP at the next opposing swing / liquidity, or the opposing HTF zone.
   - Skip the trade if RR < 2.
5. **Accuracy.**
   - Every rule is tested the same way before it goes in: fixed thresholds, both halves, the second period.
   - Then paper trading, then Binance testnet, then small size.

## Suggested build order

1. **Live zone engine:** Binance klines + WebSocket, using `backtest.py` logic. Check that the zones match TradingView on a few coins.
2. **Validity tracker per zone:** gap, age, approach, status (FRESH / TESTED / BROKEN), trend filters.
3. **Order flow recorder:** aggTrade delta / CVD, depth, liquidations. Store to disk.
4. **Tests with TP/SL and fees:** entry type, zone choice, structure SL/TP, order flow confirmation.
5. **Paper trading loop:** log every signal and decision with the reason.
6. **Execution on testnet:** limit / stop orders, position size from risk %.
   - Daily loss limit and kill switch.
   - API key from an environment variable, trade-only (no withdrawal), IP whitelist.
7. **Live with small size**, only after paper results hold up.

## Sources checked (2026-11-09)

- CoinGlass pricing: https://coinglass.com/pricing
- CoinGlass API docs: https://docs.coinglass.com/reference/responses-error-codes
- Binance USD-M WebSocket streams: https://developers.binance.com/docs/derivatives/usds-margined-futures/websocket-market-streams
- Binance stream change notice: https://developers.binance.com/docs/derivatives/usds-margined-futures/websocket-market-streams/Important-WebSocket-Change-Notice
- Open interest has no WebSocket (secondary source, check it): https://docs.tardis.dev/historical-data-details/binance-futures
