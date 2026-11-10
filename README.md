# LVN scalp bot (Binance USD-M perps, 1H / 5m)

Follows `Scalp_LVN_1H5m.pine`: fresh 5m LVNs in a strong 1H trend (4H on the same side),
CHoCH / BOS confirmation plus order flow (absorption + delta shift), structure SL / TP, RR >= 2 after fees.
The handoff brief is `CLAUDE.md`.

## Run on a VPS (Ubuntu)

```bash
sudo apt update && sudo apt install -y python3 python3-venv git chrony   # chrony keeps the clock right
git clone https://github.com/supunS11/Binance-Bot---LVN_Scalp.git lvn-bot
cd lvn-bot
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env && nano .env        # API key / secret, MARGIN_USDT, USE_TESTNET, TRADING_ENABLED
python -m bot.account                    # balance, ONE-WAY mode, key restrictions
python -m bot.main                       # the bot
```

Keep it running after logout:

```bash
tmux new -s lvn          # then: . .venv/bin/activate && python -m bot.main
# detach: Ctrl+B then D     re-attach: tmux attach -t lvn
```

The first start downloads 21 days of 1m candles for every symbol (200 symbols: about 20 minutes).
Later starts load them from `bot_cache/`.

The Binance API key must be trade-only (no withdrawals) with the VPS IP on its whitelist.

## Files

- `live/status.md`: open positions, watches, armed zones, trend per symbol.
- `logs/decisions.jsonl`: every decision with its reason. `logs/trades.jsonl`: trades with R after fees.
- `logs/bot.log`: the full log.
- Stop new entries at once: `touch KILL_SWITCH` in the bot folder.
