#!/usr/bin/env python3
"""4H/15m script: do looser leg rules give more LVNs that still react better than random levels?

Same reaction test as backtest_lvn_reaction.py --swing (no TP/SL). Each setting changes one leg rule for both 4H and 15m
legs; the last one changes all four. All values fixed before the first run.

    python backtest_lvn_loose.py
"""
import multiprocessing as mp

from backtest_lvn_reaction import DATA, cell, diff, half, job

VARIANTS = (("Current (4 ATR, vol 1.5x, dir 70%, pullback 30% + 2 ATR)", {}),
            ("Size 3 ATR", {"MIN_ATR": 3.0}),
            ("Volume 1.2x", {"MIN_VOL_CHART": 1.2}),
            ("Direction 60%", {"MIN_DIR": 0.60}),
            ("Pullback 20% + 1 ATR", {"PULLBACK": 0.20, "PB_ATR": 1.0}),
            ("All four looser", {"MIN_ATR": 3.0, "MIN_VOL_CHART": 1.2, "MIN_DIR": 0.60, "PULLBACK": 0.20, "PB_ATR": 1.0}))
HEAD = ("| Setting | Zones made per coin per day | Touched when made % | LVN touches | LVN 1 ATR % | Random 1 ATR % | LVN - random (95%) | 1st half | 2nd half | 2024-25 |\n"
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")


def line(name, rows, tier):
    new = [r for r in rows if r["tier"] == tier and r["period"] == "2025"]
    old = [r for r in rows if r["tier"] == tier and r["period"] == "2024"]
    made = [r for r in new if r["kind"] == "made"]
    lv, rd = [r for r in new if r["kind"] == "lvn"], [r for r in new if r["kind"] == "rand"]
    h1 = [r for r in lv if not r["late"]], [r for r in rd if not r["late"]]
    h2 = [r for r in lv if r["late"]], [r for r in rd if r["late"]]
    ol = [r for r in old if r["kind"] == "lvn"], [r for r in old if r["kind"] == "rand"]
    seen = 100 * sum(r["seen"] for r in made) / len(made) if made else float("nan")
    return (f"| {name} | {len(made) / (4 * 365):.2f} | {seen:.0f} | {len(lv)} | {cell(lv, 'h1')} | {cell(rd, 'h1')} | {diff(lv, rd, 'h1')} | "
            f"{half(*h1, 'h1')} | {half(*h2, 'h1')} | {half(*ol, 'h1')} |")


def main():
    jobs = [d + (False, "swing", over) for _, over in VARIANTS for d in DATA]
    with mp.Pool(4, maxtasksperchild=1) as p:
        done = p.map(job, jobs, chunksize=1)
    n = len(DATA)
    res = [[r for x in done[i * n:(i + 1) * n] for r in x] for i in range(len(VARIANTS))]
    o = ["# 4H/15m: looser leg rules vs LVN reaction", "",
         "BTC, ETH, SOL, XRP, 2025-10-19 to 2026-10-19 (2024-25 = BTC, ETH). Reaction = 1 x 15m ATR from the near edge before a 1m close beyond the far edge, within 3 days of the first touch.",
         "Zones made counts every LVN, also the ones already touched when made; the reaction columns use only the untouched ones.", ""]
    for tf, tier in (("15m", 0), ("4H", 1)):
        o += [f"## {tf} zones", "", HEAD] + [line(name, rows, tier) for (name, _), rows in zip(VARIANTS, res)] + [""]
    text = "\n".join(o)
    with open("backtest_lvn_loose_report.md", "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
