# Quantitative and academic definitions of an impulse move, and evidence for continuation

Evidence tags used throughout:
- **[Tested]** = empirical result in a peer-reviewed paper or working paper.
- **[Preprint]** = empirical result in an unreplicated preprint.
- **[Convention]** = practitioner or vendor rule with no outcome test behind it.
- **[Derived]** = my own arithmetic, not from a source.

Depth of reading varied:
- Read in extracted full text (partial, targeted passages): Scaillet et al., Gervais et al. working paper, Lee & Swaminathan, Christensen et al., Llorente et al. working paper (tables only).
- Abstract or search summary only: everything else, flagged where it matters.

## Kaufman Efficiency Ratio: formula, thresholds, and difference from net move / sum of candle ranges

### Takeaway
ER is net close-to-close change divided by the sum of absolute close-to-close changes, on a 0 to 1 scale. No validated threshold exists: 10 bars is the standard lookback, and fixed cut-offs are conventions. I found no peer-reviewed test showing that high ER predicts continuation, in crypto or elsewhere.

### Cited Findings
- [Convention/definition] ER = Direction / Volatility, where Volatility is the sum of absolute bar-to-bar price changes over the length; ER is set to zero if Volatility is zero — [LuxAlgo](https://www.luxalgo.com/library/concept/kaufman-efficiency-ratio/); [TA-Lib](https://ta-lib.org/functions/er.html).
- [Convention] 1.0 is a straight-line move and values near 0 are churn — [TA-Lib](https://ta-lib.org/functions/er.html).
- [Convention] The usual KAMA settings are ER period 10, fast 2, slow 30 — [Groww](https://groww.in/blog/kaufman-adaptive-moving-average-kama) (secondary source).
- [Convention] ER thresholds are conventions to be tested, not constants. The suggestion is to use percentiles of the instrument's own history, or to require ER to hold above its recent average for several bars. ADX, by contrast, is conventionally read against fixed levels near 20 or 25 — [LuxAlgo](https://www.luxalgo.com/library/concept/kaufman-efficiency-ratio/).
- [Convention, untested claim] High ER favours trend strategies and low ER favours range strategies; no test is presented — [StockSharp](https://doc.stocksharp.com/en/topics/api/indicators/list_of_indicators/kaufman_efficiency_ratio).
- Sources disagree on how the KAMA smoothing constant is written (some square it, some do not) — compare [MetaTrader 5](https://www.metatrader5.com/en/terminal/help/indicators/trend_indicators/ama) with [Groww](https://groww.in/blog/kaufman-adaptive-moving-average-kama). This affects KAMA, not ER itself.

### Inferences
- [Derived] **Random-walk baseline.** For iid Gaussian returns, E|sum of n returns| / (n x E|return|) = 1/sqrt(n). A driftless market therefore has an expected ER of about 0.58 at n=3, 0.45 at n=5, 0.32 at n=10 and 0.22 at n=20. Any fixed threshold must be judged against n: ER 0.5 is unremarkable at 3 to 5 bars but well above baseline at 20. This is an expectation only. Fat tails and autocorrelation will shift it, so empirical percentiles per instrument and timeframe are safer.
- [Derived] **ER versus net move / sum of candle ranges (H-L).**
  - In 24/7 markets with open close to the prior close, |C(t) - C(t-1)| is at most H(t) - L(t). The range-based denominator is therefore at least as large, and net move / sum of ranges is at most ER.
  - The range version penalises wicks, while ER ignores them. A sequence of long-wick candles that close in one direction scores high on ER and lower on the range ratio.
  - For "clean impulse" definitions the range version is stricter and captures intrabar rejection. ER measures only close-to-close path efficiency.
  - Neither measure carries any magnitude information. A tiny drift can have ER = 1, so an efficiency measure needs a separate volatility-scaled size condition.

### Gaps
- I did not access Kaufman's book (*Trading Systems and Methods*), so any thresholds he publishes are unverified here.
- I found no peer-reviewed or out-of-sample study testing forward returns conditional on high ER. I also found none on 4H or 15m crypto perpetuals.

## ATR-normalised range, volatility-scaled moves and jump detection: what thresholds are used?

### Takeaway
Formal jump tests have defined thresholds (Lee-Mykland uses Gumbel quantiles, with FDR control preferred). ATR multiples such as 2 x ATR are conventions with no academic validation that I could find. Jump tests are built for high-frequency data, and many "jumps" found at lower frequency are really volatility bursts. Treating 15m or 4H bars as jumps is therefore a loose analogy.

### Cited Findings
- [Tested/method] The Lee-Mykland test uses the maximum normalised return increment and its asymptotic Gumbel distribution under the no-jump null, and critical values come from Gumbel quantiles at a chosen level — [Nunes & Ruas 2024](https://repositorio.iscte-iul.pt/bitstream/10071/31168/1/article_100198.pdf). A search summary reports the 0.99 Gumbel quantile as the original threshold; I did not confirm that in the original paper.
- [Tested/method] Nunes & Ruas note that later implementations replicate a typo in the 2008 paper's critical region; the region should be defined on the absolute statistic, and the standard formula is still recovered — [Nunes & Ruas 2024](https://ciencia.iscte-iul.pt/publications/a-note-on-the-gumbel-convergence-for-the-lee-and-mykland-jump-tests/100198?lang=en).
- [Tested, Bitcoin] Scaillet, Treccani & Trevisan apply Lee-Mykland (2012) with FDR control to Mt. Gox tick data, June 2011 to November 2013:
  - 124 days had at least one jump, about one detection day per week, which they say is significantly more than prior research observed for large-cap assets and indices.
  - Average jump size is +4.7% (positive) and -4.1% (negative), with moves of up to 32% within a 5-minute interval.
  - A fixed 1% level is "too permissive" and produces many spurious detections.
  - Source: [Scaillet et al. 2017](https://arxiv.org/pdf/1704.08175).
- [Tested, equities/FX] Using millisecond tick data, jumps account for about 1% of total price variation, an order of magnitude below lower-frequency estimates. A volatility burst is often spuriously labelled a jump at lower frequencies, and price continuity usually holds even during severe liquidity deterioration — [Christensen, Oomen & Podolskij](https://arxiv.org/pdf/2602.10925).
- [Method] The Barndorff-Nielsen & Shephard approach uses realised variance minus bipower variation, because that difference isolates the jump component of quadratic variation — [arXiv 2404.04962](https://arxiv.org/pdf/2404.04962). It has been applied to Bitcoin, with jumps reported as stronger than in the other instruments analysed — [Charles University thesis](https://dspace.cuni.cz/handle/20.500.11956/69721). It tests at the daily level, so it does not time-stamp an individual bar. The specific significance levels used in the literature were not verified.
- [Convention] A LuxAlgo indicator triggers at EMA +/- 2 x ATR and presents no outcome statistics — [LuxAlgo](https://www.luxalgo.com/library/indicator/RqEk3iZu-atr-breakouts/). A targeted search returned only scripts and blogs, no academic test of ATR-multiple breakouts.
- [Convention, low quality] A community script claims about 4.3 sigma at the 1% level over a 250-bar window — [TradingView](https://ru.tradingview.com/script/vKLsicM6-Volatility-Jump-Detector/).

### Inferences
- [Derived] Exact Gaussian multiple-testing cut-offs for a 1% family-wise false-alarm rate (Sidak, assumes iid normal bars with a good volatility estimate):

| Scan window | Bars tested | |z| threshold |
|---|---|---|
| 4H bars, one day | 6 | about 3.1 |
| 15m bars, one day | 96 | about 3.9 |
| 4H bars, one year | 2,190 | about 4.6 |
| 15m bars, one year | 35,040 | about 5.1 |

  Crypto returns are fat-tailed, so real false-positive rates would be higher. These are orientation values, not validated thresholds. They also suggest that a 2 x ATR bar is common rather than rare, although ATR (a range measure) and return standard deviation are not the same unit, so the two cannot be compared directly without calibration.
- A practical definition can use a volatility-scaled move (return / rolling sigma, or range / ATR) with empirically chosen percentiles. It should be described as a "large volatility-scaled move", not a statistically detected jump.

### Gaps
- From memory, not verified this session: Lee-Mykland's recommended local-volatility window (K about 270 at 5m, 156 at 15m) and the exact normalising constants. Check the original paper before use.
- I found no study giving ATR-multiple thresholds with forward-return evidence.
- The Mt. Gox sample is a retail spot venue that no longer exists, so its jump frequency and size may not carry over to modern perpetual markets.

## Volume: does abnormal volume alongside a move predict continuation or reversal?

### Takeaway
The answer depends on horizon, market and what drives the volume, so "high volume confirms the move" is too simple. Gervais et al. find a positive premium after high volume, Lee & Swaminathan find high-volume winners reverse sooner, Llorente et al. find the sign depends on informed trading, and the crypto evidence points to low-volume moves reversing. None of this tests 15m or 4H perpetual impulses.

### Cited Findings
- [Tested, US equities] **Gervais, Kaniel & Mingelgrin** ([JF 2001](https://econpapers.repec.org/RePEc:bla:jfinan:v:56:y:2001:i:3:p:877-919); [working paper](https://rodneywhitecenter.wharton.upenn.edu/wp-content/uploads/2014/04/9901.pdf)):
  - Sample: daily NYSE, August 1963 to December 1996, split into 161 non-overlapping 50-day intervals. The formation day's volume is compared with the prior 49-day reference period.
  - Zero-investment (long high-volume, short low-volume) returns range from 0.35% over 1 day to 0.94% over 20 days for small stocks, and from 0.12% to 0.50% for large stocks, with t-statistics about 3 or higher.
  - The premium grows with horizon through 20 days.
  - The authors state that volume by itself carries information about subsequent prices.
  - They also suggest profits could be exploited after costs, with medium firms the best candidates. I only saw fragments of that section.
  - Note this is a premium for high volume generally, not a test of continuation in the direction of the move.
- [Tested] Later work finds the premium in almost all developed and in emerging equity markets, but it fades very quickly for illiquid stocks and lasts longer in highly liquid ones — [search summary of later studies; primary paper not identified](https://repec.cepr.org/repec/cpr/ceprdp/DP14587.pdf).
- [Tested, US equities] **Lee & Swaminathan** ([JF 2000](https://www.johnhcochrane.com/s/lee_swaminathan_returns_volume_JF.pdf)):
  - Sample: NYSE/AMEX, January 1965 to December 1995. Volume is average daily turnover over multi-month formation periods.
  - For J=6, K=6 the momentum spread is 1.46% per month in high-volume firms versus 0.54% in low-volume firms (a reported difference of 0.91%).
  - For J=9, K=6 low-volume losers beat high-volume losers by 1.02% per month, and low-volume winners beat high-volume winners by 0.26% per month.
  - Momentum reverses over five years, and high-volume winners and low-volume losers reverse faster.
  - The horizon is months to years, so it is not intraday evidence.
- [Tested, US equities] **Llorente, Michaely, Saar & Wang** ([RFS 2002](https://econpapers.repec.org/RePEc:oup:rfinst:v:15:y:2002:i:4:p:1005-1047); [abstract](https://archive.nyu.edu/handle/2451/26698); [working paper tables](https://archive.nyu.edu/jspui/bitstream/2451/26698/1/FIN-00-032.pdf)):
  - Theory: returns from risk-sharing trades reverse and returns from speculative trades continue.
  - Test (working paper): NYSE/AMEX daily, 1993 to 1998, 2,226 regression observations. The regression is R(t+1) = C0 + C1 x R(t) + C2 x Volume(t) x R(t) + error, with volume as detrended log turnover.
  - C2 rises with the bid-ask spread rank (b = 0.0557, t = 15.9, R2 10.2%) and falls with market cap rank (b = -0.0442, t = -12.4, R2 6.4%).
  - So volume leans towards continuation in small, high-spread stocks, a proxy for informed trading, and towards reversal in large, liquid ones. Coefficients are from the working-paper tables and may differ in the published version.
- [Tested, crypto] **Bianchi, Babiak & Dickerson** ([JBF 2022](https://eprints.lancs.ac.uk/id/eprint/172093); [summary of 2018 working paper](https://www.cxoadvisory.com/technical-trading/predicting-crypto-asset-returns-with-past-returns-volume/)):
  - The interaction of volume shocks and past returns predicts returns, while volume alone has little power.
  - The main pattern is intraday and daily reversal after low-volume intervals, across 26 cryptocurrencies from 150+ exchanges (BTC-denominated).
  - A reversal strategy earned a gross annualised Sharpe as high as 2.96, per the secondary summary. Gross figure; the source does not establish a net result.
  - Liquidity-provision returns are amplified in smaller, more volatile and less liquid pairs.
- [Tested, equity ETF] Gao, Han, Li & Zhou: predictability of the last half-hour from the first half-hour generally rises with volatility and volume — [JFE 2018](https://econpapers.repec.org/RePEc:eee:jfinec:v:129:y:2018:i:2:p:394-414); [working paper](https://c.mql5.com/forextsd/forum/173/intraday_momentum_-_the_first_half-hour_return_predicts_the_last_half-hour_return.pdf).
- [Tested, Bitcoin] Shen, Urquhart & Wang: intraday momentum is strongest in the first sessions with the highest volume or volatility — [Financial Review 2022](https://centaur.reading.ac.uk/100181).
- [Tested, contradictory replications] International studies disagree on the volume-momentum interaction. A European study found momentum only in low-volume stocks and said volume does not predict persistence — [Lopes 2018](https://run.unl.pt/bitstream/10362/49540/1/Lopes_2018.pdf). (The attribution of this finding to this specific document comes from a search summary and was not checked in full text.)

### Inferences
- Crypto evidence better supports "a low-volume move is more likely to reverse" than "a high-volume move will continue". The two are not equivalent, and the second is not directly established by the sources here.
- Volume filters should be tested as an interaction with the signed return, in line with Llorente and Bianchi, and not as a standalone confirmation flag.
- Perpetual volume is exchange-specific and may be inflated by leveraged and liquidation flow, so abnormal volume is best defined relative to the same venue's own history (for example, against the same time of day). This is my reasoning, not a tested result.

### Gaps
- I found no study testing abnormal volume alongside a directional impulse on 15m or 4H crypto perpetuals.
- I did not obtain the exact high-volume rank cut-off in Gervais et al. or their results conditional on the sign of the formation-period return.
- I found no tested results on open interest or liquidation data as a filter.

## Short-term momentum vs reversal after large moves in crypto and futures

### Takeaway
Crypto results are mixed and conditional. Time-series momentum at daily and weekly horizons is the best supported, along with intraday predictability in both directions. After very large moves the picture is contested, and liquidity is the main moderator: illiquid coins tend to reverse and the largest, most tradable coins tend to continue. Nothing I found tests continuation after large moves directly on 15m or 4H perpetuals.

### Cited Findings
**Futures and benchmark evidence**
- [Tested] **Moskowitz, Ooi & Pedersen** (JFE 2012, 58 liquid futures): returns persist for 1 to 12 months and partly reverse over longer horizons. The 12-month strategy is profitable for every contract, and a diversified version earns abnormal returns with little exposure to standard factors, performing best in extreme markets — [SSRN](https://papers.ssrn.com/abstract=2089463); [RePEc](https://econpapers.repec.org/RePEc:eee:jfinec:v:104:y:2012:i:2:p:228-250). A blog puts the portfolio Sharpe near 1.0 over 1985 to 2009 — [secondary, unverified](https://themenonlab.blog/blog/time-series-momentum-hedge-fund-strategy-explained).
- [Tested, contradicts MOP] **Huang, Li, Wang & Zhou** (JFE 2020): asset-by-asset regressions show little evidence of time-series momentum in or out of sample. The pooled t-statistic falls below bootstrap critical values, and the strategy's performance is virtually the same as one using the historical sample mean, without predictability — [Huang et al.](https://profiles.wustl.edu/en/publications/time-series-momentum-is-it-there/). A later critique, which excludes volatility scaling, finds only 8 of 55 assets significant at 5% — [Alpha Architect](https://alphaarchitect.com/an-empirical-challenge-for-trend-following/). Another commentary still regards TSMOM as appealing — [Alpha Architect](https://alphaarchitect.com/are-trend-following-and-time-series-momentum-research-results-robust/).
- [Tested, equity ETF] **Gao et al.** (S&P 500 ETF, 1993 to 2013): first half-hour return predicts last half-hour return — [JFE 2018](https://econpapers.repec.org/RePEc:eee:jfinec:v:129:y:2018:i:2:p:394-414). Sources cite differing samples, and the earlier draft used 1999 to 2012 — [Alpha Architect](https://alphaarchitect.com/2014/08/attention-prop-traders-the-first-half-hour-of-trading-predicts-the-last-half-hour/).

**Crypto, daily and weekly**
- [Tested] **Liu & Tsyvinski** (RFS 2021): strong time-series momentum and attention-based predictability for Bitcoin, Ripple and Ethereum — [NBER 24877](https://econpapers.repec.org/RePEc:nbr:nberwo:24877); [RFS](https://econpapers.repec.org/RePEc:oup:rfinst:v:34:y:2021:i:6:p:2689-2727.). Significant at daily and weekly frequencies per a search summary. I did not retrieve effect sizes.
- [Tested] **Liu, Tsyvinski & Wu** (JF 2022): market, size and momentum factors capture the cross-section of crypto returns — [RePEc](https://econpapers.repec.org/RePEc:bla:jfinan:v:77:y:2022:i:2:p:1133-1177).
- [Tested] **Zaremba et al.** (IRFA 2021, more than 3,600 coins, daily): low prior-day-return coins beat high prior-day-return coins (reversal), which they attribute to illiquidity, while the largest, most tradable coins show daily momentum — [Zaremba et al.](https://www.x-mol.com/paper/1442395529393532928).
- [Tested] **Li, Urquhart, Wang & Zhang** (2021): coins with higher maximum daily returns earn higher future returns ("MAX momentum"), opposite to the equity MAX result — [working paper](https://centaur.reading.ac.uk/99101/1/MAX%20Momentum.R1.pdf). A separate study reports weekly high-minus-low MAX decile differences of 3.03% raw and 1.99% risk-adjusted — [Bilkent thesis](https://repository.bilkent.edu.tr/items/78167f5c-d3e2-4f07-b4bc-5e8a3ed0b2c0).
- [Tested] **Han, Kang & Ryu:** evidence for time-series momentum is strong and for cross-sectional momentum weak, under realistic assumptions — [working paper](https://acfr.aut.ac.nz/__data/assets/pdf_file/0009/918729/Time_Series_and_Cross_Sectional_Momentum_in_the_Cryptocurrency_Market_with_IA.pdf). Their time-series momentum is reported as concentrated in bullish markets, with negative profits in most falling-market cases (search summary; full text returned HTTP 403).

**Crypto, intraday**
- [Tested] **Wen, Bouri, Xu & Zhao** (NAJEF 2022, Bitcoin, March 2013 to May 2020): both momentum and reversal exist in intraday returns, and patterns change around large intraday jumps, FOMC releases, liquidity levels and COVID-19. Similar predictability appears in Ethereum, Litecoin and Ripple, and timing strategies beat always-long and buy-and-hold — [abstract](https://ideas.repec.org/a/eee/ecofin/v62y2022ics1062940822000833.html). A summary states jumps tend to weaken predictability — [ScienceDirect listing](https://www.sciencedirect.com/science/article/abs/pii/S1062940822000833) (full text not accessed).
- [Tested] **Shen, Urquhart & Wang** (Financial Review 2022): with volume used as a proxy for market trading time, the first half-hour positively predicts the last half-hour, driven by liquidity provision and not by late-informed trading — [Reading repository](https://centaur.reading.ac.uk/100181). Note the conflict: Wen et al. attribute momentum to late-informed investors.
- [Tested] **Scaillet et al.** (Mt. Gox, 2011 to 2013): jumps induce a significant, persistent price change; market-activity and illiquidity indicators revert to prior levels in under half an hour; and positive (negative) jumps occur during locally bearish (bullish) trends — [Scaillet et al. 2017](https://arxiv.org/pdf/1704.08175). This supports a persistent level change, but it does not show further drift after the jump.
- [Tested] Reported conditional reversal in BTC in both day and overnight sessions, with ETH combining positive overnight drift and daytime reversal — [ResearchGate abstract](https://www.researchgate.net/publication/414070255_On_the_Performance_of_Lagged_Momentum_and_Reversal_Strategies_Across_Daytime_and_Overnight_Sessions_in_Bitcoin_and_Ethereum_Cryptocurrencies) (abstract-level only).
- [Tested] Bitcoin's positive returns concentrate disproportionately at the turns of 15-minute candles, a timing artefact that could contaminate 15m backtests — [PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10015199/).
- [Tested, adjacent] A 2026 Finance Research Letters paper reports significant return reversal around Bitcoin option expiry, using Deribit perpetual data — [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S1544612326008688) (snippet only). It is event-specific, not about impulses in general.

### Inferences
- No source supports an unconditional claim that "impulses continue" in crypto. The fairest reading is that a large move leaves a lasting level change on average in some evidence, while follow-through depends on liquidity, trend regime, volume and horizon.
- Liquidity is the recurring moderator, in Zaremba, Bianchi and the Gervais-related work. This favours restricting any continuation rule to the largest, most liquid perpetuals, and testing rather than assuming it.
- Most of the momentum evidence is measured over periods far longer than one 15m or 4H impulse, so extrapolating it down to those bars is not justified. The half-hour studies are about time-of-session effects, not move-size conditioning.
- Bull-market concentration (Han et al.) means results from long-only-favourable samples should not be read as symmetric between long and short impulses.

### Gaps
- **Directly untested:** I found no study that conditions on a large 4H or 15m move on crypto perpetuals and measures subsequent continuation versus reversal. All crypto intraday evidence here is hourly or half-hourly, and mostly spot.
- Perpetual-specific mechanics (funding, liquidation cascades) are not addressed by these papers. A Binance perpetuals study covering 2020 to 2024 addresses microstructure, not post-jump direction — [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2214845025001188).
- Liu & Tsyvinski and Wen et al. effect sizes were not retrieved because full text was unavailable.
- I did not locate Dobrynskaya's or Grobys & Sapkota's results within the search results; a Dobrynskaya paper exists — [HSE](https://conference.hse.ru/files/download_file_ex?hash=FAE0AB2DC7A67656E89A0B1CB27D8C7D&id=3B5EE9A5-0B18-458A-9458-B4ED0F6C6664) — but its numbers were not extracted.

## Does the evidence hold after trading costs?

### Takeaway
Daily and multi-day crypto trend strategies have reported positive net results, though the sources are mostly working papers and backtests. Evidence for strategies at 15m and 4H is thin and unreplicated, and many published figures are gross. Costs matter most at the short horizons where reversal has been found.

### Cited Findings
- [Tested, working paper] **Zarattini, Pagani & Barbon** (2025): an ensemble of Donchian trend models with volatility sizing, on Bitcoin and a rotating top-20 liquid coin portfolio. Net-of-fees Sharpe above 1.5 and annualised alpha of 10.8% versus Bitcoin (from a search summary of the paper) — [IDEAS](https://ideas.repec.org/p/chf/rpseri/rp2580.html). Costs of 0.10%, 0.25% and 0.50% are considered — [CXO Advisory](https://www.cxoadvisory.com/technical-trading/crypto-asset-trend-following-strategies/). A third party reports a Sharpe of 1.58 and CAGR of 30% without stating the basis — [Quantified Strategies](https://www.quantifiedstrategies.com/?p=1192563). The primary abstract page could not be fetched (HTTP 500), so treat this as secondary. These are not intraday signals as far as I could verify.
- [Preprint, closest match in timeframe] **AdaptiveTrend** (2026): trend-following on 6-hour bars with a volatility-calibrated trailing stop over 150+ pairs, 2022 to 2024, with a 36-month evaluation window. Reported Sharpe 2.41, maximum drawdown -12.7%, Calmar 3.18 — [arXiv 2602.11708](https://arxiv.org/abs/2602.11708). The PDF is described in a search summary as modelling a 4 bps taker fee, slippage and funding — [arXiv PDF](https://arxiv.org/pdf/2602.11708). It is a single v1 preprint, and such a high Sharpe over a short window warrants scepticism. Selection and multiple-testing effects were not assessed.
- [Tested] **Han, Kang & Ryu:** many momentum portfolios are liquidated, and many with statistically significant returns earn insignificant profits once costs and daily price swings are included. They also argue a t-test on mean returns is insufficient to establish profitability — [working paper](https://acfr.aut.ac.nz/__data/assets/pdf_file/0009/918729/Time_Series_and_Cross_Sectional_Momentum_in_the_Cryptocurrency_Market_with_IA.pdf) (search summary; direct fetch returned HTTP 403).
- [Tested] **Wen et al.:** timing strategies produce higher economic value than always-long or buy-and-hold — [abstract](https://ideas.repec.org/a/eee/ecofin/v62y2022ics1062940822000833.html). A separate 2021 Bitcoin study reports abnormal returns remaining positive after fees, especially for leveraged investors — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1057521921001228) (abstract-level; I did not confirm the fee assumptions).
- [Gross only] **Bianchi et al.:** the gross Sharpe of up to 2.96 for crypto reversal concentrates in smaller, less liquid pairs, exactly where costs are highest — [summary](https://www.cxoadvisory.com/technical-trading/predicting-crypto-asset-returns-with-past-returns-volume/); [JBF abstract](https://eprints.lancs.ac.uk/id/eprint/172093).
- [Apparently gross] MOP's reported returns appear to be gross of trading costs — [Quantpedia/CXO summary](https://www.cxoadvisory.com/momentum-investing/intrinsic-momentum-investing/) (secondary).
- [Informal] A blog finds mean reversion on smaller time steps that is very hard to exploit because of costs, with momentum on longer time steps — [Substack](https://financialnoob.substack.com/p/momentum-vs-mean-reversion-in-crypto) (not peer reviewed).
- [Convention, weak] One blog's regime-filtered breakout had a profit factor of 1.02 on gold futures, described as close to a coin flip after slippage — [blog](https://anupshindedotcom.pages.dev/pattern-rotation-backtested/) (anecdote, not crypto).

### Inferences
- [Derived] At a 4 bps taker fee per side, a round trip costs 8 bps before slippage and funding. At the 10 to 50 bps cost levels stress-tested by Zarattini et al., a single 15m trade would need much larger average gross gain than typical drift estimates could imply. A 15m impulse-continuation rule therefore needs net-of-cost testing before any weight is placed on it. A 4H rule has more room to absorb costs because expected moves are larger, but this does not show that it is profitable.
- Reported net Sharpes should be discounted for backtest overfitting, survivorship in coin selection and the short, bull-heavy history of crypto. The Han et al. liquidation point also means leverage can turn a positive average into a realised loss.

### Gaps
- I found no peer-reviewed, net-of-cost study of impulse-conditioned entries on 15m or 4H crypto perpetuals.
- I found no independent replication of the AdaptiveTrend results and could not confirm cost assumptions from a full read of the paper.
- Effect of funding payments on short-horizon impulse trades is not quantified in the sources I reached.
- Han, Kang & Ryu's exact sample, cost assumptions and net figures could not be retrieved (HTTP 403), so no numbers are given.
