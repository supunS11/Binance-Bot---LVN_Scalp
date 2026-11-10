# Evidence for Low Volume Nodes (LVNs) and Market-Structure Signals (BOS, CHoCH, FVG, Order Blocks)

Bottom line for the report writer: I found no peer-reviewed or transparent test of LVNs as trading levels, and none of "LVN inside an impulse leg" or anchored-profile pullback entries. Tested evidence exists for price-based support and resistance, but those tests do not use volume-at-price. For SMC concepts, the most rigorous test I could locate (an unreviewed preprint, seen only through secondary descriptions) found no support for them as taught.

Evidence labels used below: [TEST-PR] peer-reviewed test; [TEST-PREPRINT] test not peer-reviewed; [VENDOR] claim from a party selling a product or education; [OPINION] untested practitioner statement.

Access limits: SSRN, ResearchGate, Deepscope and NexusFi returned HTTP 403 to my fetches. Items marked "search summary only" were not read in full. The Dalton and Steidlmayer books were not available.

## Origin in Market Profile / Auction Market Theory: what is claimed about low-volume areas, and do practitioners agree on rejection vs fast pass-through?

### Takeaway
The vocabulary descends from Steidlmayer's Market Profile and Dalton's later books, but "LVN" is mainly a volume-profile label, and I could not verify the primary wording. Practitioners claim both rejection and fast traversal, often in the same passage, so the claim as usually stated is hard to falsify.

### Cited Findings
**Origin (secondary sources)**
- Steidlmayer's TPO construction dates to the Chicago Board of Trade in the 1980s, and Dalton popularized it for screen traders — [Futures TA course notes, ch. 9](https://portfoliowebsite-3hz.pages.dev/research/futures-ta/chapters/ch09-volume-profile).
- Steidlmayer and Kevin Koy set out auction language in *Markets and Market Logic* (1986); Dalton, Jones and Dalton covered poor highs, poor lows and excess in *Mind Over Markets* (1990) — [search summary of The Right Trader](https://therighttrader.com/learn/volume-and-order-flow/poor-highs-and-lows). Secondary, not checked against the books.
- Index listings for *Mind Over Markets* reportedly show sections titled "Low-Volume Areas" and "High- and Low-Volume Areas", but only table-of-contents text surfaced — [search summary of Thalia listing](https://www.thalia.de/shop/home/artikeldetails/A1025407863). The topic is in the book; its wording is unverified.
- Market Profile is time-based and volume profile is volume-at-price — [Axelrod substack, search summary](https://axelrod.substack.com/p/volume-profile). A single print is thin in time and an LVN is thin in volume; they often coincide on a fast move but can differ — [search summary, The Right Trader](https://therighttrader.com/learn/volume-and-order-flow/single-prints).

**Claims about price at LVNs [OPINION / VENDOR]**
- Pass-through: LVNs act as "air pockets" that price tends to cross quickly, and once price leaves an HVN the intervening LVNs are expected to trade fast, with the next HVN a common target — [LuxAlgo](https://www.luxalgo.com/library/concept/high-low-volume-nodes.md).
- Rejection: a touch may reject quickly or slice straight through, which the same page calls a binary outcome. It adds that building volume inside a former LVN may signal acceptance — [LuxAlgo](https://www.luxalgo.com/library/concept/high-low-volume-nodes.md).
- Both: LVNs may break through sharply or reverse after rejection — [Angel One, search summary](https://oga-prod.angelone.in/knowledge-center/online-share-trading/low-volume-nodes-lvn).
- Skip behaviour: rejection zones create voids or low-volume nodes that price may skip in future moves — [Bookmap, search summary](https://bookmap.com/blog/inside-the-auction-what-it-means-when-the-market-rejects-a-price).
- Repair or fill: single prints and poor highs and lows are described as failed auctions that price typically returns to; another source says there is no reliable published rate for how often repairs happen — [search summaries, LuxAlgo](https://www.luxalgo.com/library/concept/single-prints/) and [The Right Trader](https://therighttrader.com/learn/volume-and-order-flow/single-prints).
- Steidlmayer and Dalton reportedly published no single mechanical system with a sample and win rate — [JournalPlus, search summary](https://journalplus.co/learn/glossary/market-profile). This is a statement by a practitioner site, not something I checked against the books.
- LuxAlgo cites no statistics, backtests, sample sizes or studies for these behaviours — [LuxAlgo](https://www.luxalgo.com/library/concept/high-low-volume-nodes.md).

### Inferences
- The two readings are not necessarily contradictory: "rejected earlier" describes why the node is thin, and "cross fast" predicts what happens on return. They do conflict as trade instructions, because one implies fading at the node and the other implies trading through to the next HVN.
- With both outcomes allowed ("binary outcome"), the claim cannot fail unless a test specifies the condition that decides between them. No source I read specifies such a condition in testable form.
- There are at least three distinct return claims in circulation: bounce at the node, fast traversal, and later fill. Any test must pick one in advance.

### Gaps
- Dalton's and Steidlmayer's exact wording on low-volume areas could not be read. The report should not attribute a specific LVN claim or the term "LVN" to them. I could not establish who first used the term.

## Is there a standard numeric definition of an LVN?

### Takeaway
No standard numeric definition turned up. Published definitions are qualitative, and indicator settings vary, so the "LVN" a trader sees depends on tool parameters.

### Cited Findings
- LuxAlgo describes LVNs as "pronounced valleys" and "thin strips" with no volume threshold or bin count, and says results depend on window, row size and profile period. It suggests giving more weight to nodes that persist across reasonable settings — [LuxAlgo](https://www.luxalgo.com/library/concept/high-low-volume-nodes.md).
- A TradingView script defines LVNs only as zones "significantly thinner than surrounding levels", with a user-set "Node Detection %" where a higher value finds more zones. The page does not state the calculation — [Volume Profile LVN script](https://www.tradingview.com/script/yhGyDKDr-Volume-Profile-LVN/).
- By contrast, the value area does have a numeric convention, about 70% of activity, justified by analogy to one standard deviation (about 68%) rather than by test — [Futures TA course notes](https://portfoliowebsite-3hz.pages.dev/research/futures-ta/chapters/ch09-volume-profile).

### Inferences
- Bin width, lookback and anchor are free parameters. Together with the lack of a definition, this creates many testable variants, which raises data-snooping risk (see Sullivan, Timmermann and White below).
- A test needs a stated rule, for example a local minimum in a smoothed volume-at-price histogram below a set fraction of neighbouring peaks. That example is my suggestion, not a standard from any source.

### Gaps
- I did not inspect indicator source code, or survey vendors systematically (for example Sierra Chart, Bookmap, TradingView's built-in tools). "No standard" means none found, not proven absent.

## Academic evidence on support and resistance and volume-at-price

### Takeaway
Price-based support and resistance has real but modest tested evidence, mostly on bounce rates rather than net profit. Direct evidence on volume-at-price is thin and weak, and I found nothing testing LVNs specifically, including in crypto.

### Cited Findings
**Support and resistance, not volume-based**
- [TEST-PR, Fed journal] Osler (2000) used levels published daily by six firms for three dollar exchange rates, January 1996 to March 1998, with one-minute data, against 10,000 sets of artificial levels using a bootstrap. Rates bounced off published levels 60.8% of the time and arbitrary levels 56.2%, and published levels beat artificial ones in all sixteen firm-currency pairs. For most firms, predictive power lasted at least five business days — [Osler, FRBNY Economic Policy Review](https://resources.newyorkfed.org/medialibrary/media/research/epr/00v06n2/0007osle.pdf).
- Osler also found that more than 70% of levels end in 0 and 96% end in 0 or 5, and that firms agreed on only about 30% of possible matches, so levels are far from a shared objective set — [Osler](https://resources.newyorkfed.org/medialibrary/media/research/epr/00v06n2/0007osle.pdf).
- [TEST-PR] Brock, Lakonishok and LeBaron (1992) tested moving-average and trading-range break rules on daily data, and Osler summarises the result as prices moving rapidly after breaks in the S&P 500, though profits may not offset transaction costs. Curcio et al. (1997) found that this does not hold on average for currencies, but may during strong trends — [Osler's literature review](https://resources.newyorkfed.org/medialibrary/media/research/epr/00v06n2/0007osle.pdf).
- [TEST-PR] Sullivan, Timmermann and White (1999) expanded the Brock et al. rule set and used White's Reality Check over 100 years of daily Dow data to adjust for data snooping — [Journal of Finance record](https://econpapers.repec.org/RePEc:bla:jfinan:v:54:y:1999:i:5:p:1647-1691). I did not read the detailed results, so its conclusions should be checked in the [full text](https://bashtage.github.io/kevinsheppard.com/files/teaching/mfe/advanced-econometrics/Sullivan_Timmermann_White.pdf) before they are quoted.
- [TEST-PREPRINT] Chung and Bellotti (2021) detected levels from rolling-window local extrema in minute data for EURUSD, Lloyds and Brent. Bounce probability rose with prior bounces and decayed over time, and shuffled-return series and AR(1) simulations did not reproduce this — [arXiv 2101.07410](https://arxiv.org/abs/2101.07410). A keyword search of the text found no profitability or transaction-cost test, and volume does not appear to be an input.

**Volume-at-price and Market Profile**
- [Conference paper] Huang et al. (IEEE CCBD 2016, published 2017) studied Taiwan index futures, reporting that historical POCs can serve as entry references, with the previous five days' POC performing best. The abstract page gives no returns, win rates or sample sizes — [NYCU record](https://scholar.nycu.edu.tw/en/publications/applying-market-profile-theory-to-analyze-financial-big-data-and-/). It concerns POCs (high-activity prices), not LVNs, and "best of several lookbacks" is a selected result.
- [Descriptive] Anderson (2008) gives a statistical review of the distributions Market Profile creates in S&P 500 futures. It is not a test of predictability, and I could not confirm peer review — [ResearchGate listing, search summary only](https://www.researchgate.net/publication/253235305_Market_Profile_in_Futures_Markets_-_a_Statistical_Review_of_a_Market_Practitioner_Tool).
- [Weak study] A paper on WIG20, January to June 2024, looks at reactions to the prior session's volume profile. It covers one index for six months — [ResearchGate, search summary only](https://www.researchgate.net/publication/398683237_Use_of_the_volume_profile_in_making_investment_decisions_on_the_stock_market). I could not read its method or check for an LVN test.
- [VENDOR] Deepscope reports a test on 731 Thai and 469 US stocks, 2016 to 2026, with volume-profile support holding 59% of the time once touched, and calls the level more of a magnet than a floor — [Deepscope, search summary only](https://deepscope.com/support-resistance-volume-profile/). The publisher has a commercial interest. Without a random-level comparison, 59% is hard to interpret, given Osler's 56.2% for arbitrary levels in a different market.
- [VENDOR/OPINION] Claims of about 75% naked POC retests are called "practitioner consensus", "informally validated", with no sample or method — [Futures TA course notes](https://portfoliowebsite-3hz.pages.dev/research/futures-ta/chapters/ch09-volume-profile). Blog figures such as a 72% POC revisit rate, or 68% attributed to "CME Group research", have no traceable source and should not be used — [search summary of the TradersPost blog and similar pages](https://blog.traderspost.io/article/market-profile-trading-strategies).

**Crypto**
- [TEST-PR] Urquhart (2017) found Bitcoin prices cluster at round numbers (over 10% end in 00), with no significant return pattern after round numbers, and a positive link between price, volume and clustering at whole numbers — [Economics Letters record](https://ideas.repec.org/a/eee/ecolet/v159y2017icp145-148.html). This is about round numbers, not volume profiles.
- I found no empirical study testing volume-profile nodes as support or resistance in crypto. Results were education pages and TradingView ideas — for example [TabTrader](https://tabtrader.com/academy/articles/identify-bitcoin-support-resistance-levels).

### Inferences
- Osler's 56.2% is the most useful number for this project: arbitrary levels "bounce" more than half the time under her definition, so raw hold rates say little. The evidence for an edge is the 4.6-point gap, and that is a bounce measure, not a net trading return.
- None of these results transfers directly to LVNs. In fact, the support and resistance logic (price memory at previously traded or bounced levels) maps more naturally to HVNs and swing extremes than to thin areas.

### Gaps
- Exact Brock et al. and Sullivan et al. statistics were not read in the primary papers.
- The search may have missed work published under other terms such as "price-volume distribution" or "volume by price". Absence is relative to about 25 tool calls, not an exhaustive review.
- No microstructure study linking historical thin-volume prices to current order-book depth was found. The "vacuum" claim is therefore untested in what I read, and historical volume at a price is not the same as resting liquidity there today.

## Tested evidence for BOS, CHoCH, FVG and order blocks

### Takeaway
No peer-reviewed standalone test showing these concepts predict returns was located. The most rigorous test found is an unreviewed preprint reporting no evidence for them as taught, while one journal paper reports positive gold results that do not isolate the concepts' value.

### Cited Findings
- [TEST-PREPRINT, primary not read] Mahadzva (2026), "Smart Money or Costly Folklore?", coded six ICT/SMC rules on four G10 pairs with walk-forward, bootstrap, permutation and holdout tests. It reports no evidence the concepts work as literally taught, and that CHoCH confirmed by an FVG retracement did better faded than traded. It also reports an order-block detector bug that the project's own checks missed — [SSRN, search summary only](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7430998).
- Secondary details on the same preprint: three liquidity-sweep rules agreed in 65 of 66 fold selections on continuation rather than reversal. The flagship faded EURUSD 1-hour variant had p = 0.0192, +19.3% over 60 holdout trades and profit factor 1.50, and reportedly fails a Deflated Sharpe check at every defensible trial count — [Thor blog](https://thortradecopier.com/blog/does-ict-smart-money-concepts-work). The blog's publisher sells a trade copier, so these figures need checking against the paper.
- [TEST-PR, limited] Oukhouya et al. (2026, *Informatica*) extracted sweeps, BOS/CHoCH, FVGs and order blocks from hourly XAUUSD. For January 2023 to May 2025, a rules-only strategy returned 38.6% net with Sharpe 0.86, and the ML plus LP hybrid 46.7% with Sharpe 1.18. The June to December 2025 hold-out is described as used for calibration and risk diagnostics — [Informatica](https://www.informatica.si/index.php/informatica/article/view/12899/6712). This covers one asset, and the paper's own ablations credit calibration and CVaR constraints as primary drivers of risk-adjusted gains, not the SMC signals.
- [TEST-PREPRINT, unverified] Bindra (2026) reports a 78.0% win rate and +265.0R on 473 FVG trades in gold and three currency pairs in 2025; its abstract reportedly mentions no out-of-sample test, random baseline or costs — [Thor blog](https://thortradecopier.com/blog/does-ict-smart-money-concepts-work). Do not count it as supporting evidence on this description.
- [Metric proposal, not a trading test] Kondapally (2025) reports that flatter FVGs precede stronger reactions, using tick data and regression slopes — [SSRN, search summary only](https://papers.ssrn.com/sol3/Delivery.cfm/6032676.pdf?abstractid=6032676&mirid=1). Fetching failed, so method and sample are unverified.
- [VENDOR, own simulation] Random-walk simulations show FVG fill and revisit rates matching random levels at the same distance — [Thor blog](https://thortradecopier.com/blog/does-ict-smart-money-concepts-work). This is useful as a null-model warning, not market evidence.
- A Crossref search dated 27 September 2026 reportedly found no peer-reviewed journal article testing ICT/SMC as defined — [Thor blog](https://thortradecopier.com/blog/does-ict-smart-money-concepts-work). A broker guide makes a similar statement — [XS, search summary](https://www.xs.com/en/test-blog/smc-smart-money-concepts-explained/). The Informatica paper above is an exception of a kind, though it tests a pipeline rather than the concepts in isolation.
- [VENDOR] Build Alpha explains how to code the concepts but reports no results, and says most configurations will not survive its test suite — [Build Alpha](https://www.buildalpha.com/backtest-ict-and-smc/). Win rates above 65% for OB and FVG confluence come without method or sample — [Backtrex, search summary](https://backtrex.com/en/blog/order-block-fair-value-gap-smc-confluence). Disregard these as evidence.
- Definitions differ: an order block may require a BOS or CHoCH plus an FVG, or a minimum percentage move or FVG left behind — [Backtrex](https://backtrex.com/en/blog/ict-order-block-backtest-strategy) and [Tradelybox](https://www.tradelybox.com/blogs/order-blocks-how-to-define-and-test-them) (search summaries).

### Inferences
- The balance of tested evidence is against the textbook reading, but it is thin: effectively one unreviewed preprint in FX. "Not shown to work" is a more defensible phrase than "shown not to work".
- The faded result should not be presented as a discovered edge: it has few holdout trades and reportedly fails multiple-testing correction.
- I found no standalone test of BOS as a continuation signal. It appears only as a component in the works above.

### Gaps
- The Mahadzva paper could not be read directly, so its per-rule results are known only secondhand.
- Oukhouya et al.'s comparison with buy-and-hold gold was not confirmed. Gold's own trend in the period could matter, and this should be checked before any favourable use.

## Tested evidence for "LVN inside an impulse leg" or anchored volume profile pullback entries

### Takeaway
I found no such evidence. There are indicators that build this setup, but no published test with a clear method, sample, costs or baseline.

### Cited Findings
- Search results were indicator descriptions. One builds profiles automatically between confirmed swing highs and lows and is described as educational — [TradingView, Pivot Anchored Pro listing](https://www.tradingview.com/scripts/wave-analysis/).
- LuxAlgo's Structural Leg Profiler profiles legs, and a related page notes that its statistics describe recorded historical behaviour on the loaded chart — [LuxAlgo, search summary](https://www.luxalgo.com/library/indicator/structural-leg-profiler.md). This is a chart statistic, not a strategy test.
- "Volume Profile Pullback Sniper" includes an LVN rejection setup disabled by default, with no backtest figures in what I saw — [TradingView, search summary](https://ru.tradingview.com/script/mJHljKmD-Volume-Profile-Pullback-Sniper/).
- The only large figure that surfaced, over 26,000 trades at 1:1 reward-to-risk on a 5-minute chart, is a vendor script's claim about VPOC, VAH and VAL, not LVN pullbacks, and is unverified — [TradingView strategy, search summary](https://it.tradingview.com/script/Rzyqmul1-Volume-Profile-VPOC-VAH-VAL-VERY-GREEN-STRATEGY).
- A practitioner argues volume-profile strategies suit discretion and are hard to backtest automatically — [Elite Trader, search summary](https://www.elitetrader.com/et/threads/programming-and-back-testing-volume-profile-and-value-areas.305261/). That is opinion, and I infer it partly explains the absence of tests.

### Inferences
- The setup combines at least three untested or loosely defined choices: impulse definition, anchor points and LVN rule. Each adds parameters, so a good in-sample result from tuning them would mean little.
- Mechanical confound: by construction, a fast leg spends little volume at many prices, so thin nodes inside it may simply reflect speed or time at price. In addition, a pullback will cross some of those prices in any case. A test should compare LVN prices against other prices in the same leg at matched retracement depth, not against no baseline. This design is my suggestion, not drawn from a source.
- Osler's random-level bootstrap and Chung and Bellotti's shuffled-return null are ready templates. Outcomes should be pre-specified as bounce, traversal speed, or net return after costs, on out-of-sample data, with multiple-testing adjustment.

### Gaps
- Private or proprietary tests may exist, but none is public in what I could find. If the report addresses this question directly, it should state plainly: no tested evidence located; this is an open empirical question, and the setup remains opinion.
