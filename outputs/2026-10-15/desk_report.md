# Desk report — 2026-10-15 (prior close 2026-10-14)

Synthetic book (26 trades), own model, USD. GBP curve: Bank of England OIS. USD curve: US Treasury par yields as a SOFR OIS **proxy**. FX and swaption vols are **synthetic** and static.

## Summary

- Daily P&L: -127,135 revalued, -129,143 predicted from the prior close's risk, 2,009 unexplained
- Trades over the 1,000 unexplained threshold: 2 (NBM-SWO-003, NBM-SWO-004)
- Fixings: 14/14 periods agree with the published index within 0.001bp; 2 fixings filled from the previous day

## Delta ladder (USD per +1bp on each par quote)

| ccy | tenor | delta_usd_per_bp | prior_close | change | from_new_trades | from_market_and_time |
|---|---|---|---|---|---|---|
| GBP | 1m | -152 | -180 | 27 | 0 | 27 |
| GBP | 2m | -265 | -258 | -7 | 0 | -7 |
| GBP | 3m | 846 | 820 | 26 | 0 | 26 |
| GBP | 6m | 1,029 | 1,070 | -41 | 0 | -41 |
| GBP | 9m | -47 | -33 | -15 | 0 | -15 |
| GBP | 1y | -1,334 | -1,368 | 35 | 0 | 35 |
| GBP | 18m | -991 | -1,023 | 32 | 0 | 32 |
| GBP | 2y | 5,949 | 5,926 | 23 | 0 | 23 |
| GBP | 3y | 8,866 | 8,805 | 60 | 0 | 60 |
| GBP | 4y | 10,146 | 10,183 | -37 | 0 | -37 |
| GBP | 5y | -19,830 | -19,721 | -108 | 0 | -108 |
| GBP | 7y | 311 | 401 | -90 | 0 | -90 |
| GBP | 10y | 15,453 | 15,433 | 21 | 0 | 21 |
| GBP | 15y | 0 | 13 | -13 | 0 | -13 |
| USD | 1m | 215 | 182 | 34 | 0 | 34 |
| USD | 2m | 239 | 276 | -37 | 0 | -37 |
| USD | 3m | -740 | -703 | -37 | 0 | -37 |
| USD | 4m | -35 | -37 | 2 | 0 | 2 |
| USD | 6m | 799 | 774 | 25 | 0 | 25 |
| USD | 1y | -519 | -504 | -15 | 2 | -17 |
| USD | 2y | -2,930 | 3,500 | -6,429 | -6,624 | 194 |
| USD | 3y | 8,839 | 8,804 | 35 | 5 | 30 |
| USD | 5y | -2,257 | -2,774 | 517 | 12 | 505 |
| USD | 7y | 10,868 | -1,029 | 11,897 | 11,755 | 141 |
| USD | 10y | -9,907 | -9,201 | -707 | 0 | -707 |
| USD | 20y | -5,178 | -4,851 | -327 | 0 | -327 |

Check: the ladder against all quotes moved together.

| ccy | ladder_sum | all_quotes_plus_1bp | difference |
|---|---|---|---|
| GBP | 19,981.2 | 19,981.4 | -0.2 |
| USD | -605.1 | -602.0 | -3.1 |

## Vega and FX delta

| product | underlying | expiry_bucket | tenor | unit | vega_usd | trades |
|---|---|---|---|---|---|---|
| FXOPT | GBPUSD | 0-3m |  | 1 vol point | 15,837 | 1 |
| FXOPT | GBPUSD | 3-6m |  | 1 vol point | -9,981 | 2 |
| FXOPT | GBPUSD | 6-12m |  | 1 vol point | -24,017 | 1 |
| FXOPT | GBPUSD | 1-2y |  | 1 vol point | 72,977 | 1 |
| SWPTN | GBP | 3-6m | 2y | 1bp normal vol | -1,160 | 1 |
| SWPTN | GBP | 6-12m | 5y | 1bp normal vol | 6,561 | 1 |
| SWPTN | USD | 3-6m | 5y | 1bp normal vol | -1,986 | 1 |
| SWPTN | USD | 2y+ | 10y | 1bp normal vol | 15,455 | 1 |

| measure | today | prior_close |
|---|---|---|
| FX delta, USD per +1% GBP/USD | 205,068 | 209,977 |

## Daily P&L explain

| line | predicted_from_risk | revalued | unexplained |
|---|---|---|---|
| carry (revalued) | -3,319 | -3,319 | 0 |
| GBP rates | -70,008 | -69,816 | 192 |
| USD rates | 82,960 | 84,583 | 1,623 |
| FX spot | -31,573 | -31,379 | 194 |
| vols | 0 | 0 | 0 |
| new trades (day-one value) | -107,204 | -107,204 | 0 |
| total | -129,143 | -127,135 | 2,009 |

Market moves (bp; spot in bp of the rate):

| ccy | tenor | move_bp |
|---|---|---|
| GBP | 1m | -0.0 |
| GBP | 2m | 0.1 |
| GBP | 3m | -0.2 |
| GBP | 6m | -0.7 |
| GBP | 9m | -1.3 |
| GBP | 1y | -1.9 |
| GBP | 18m | -2.7 |
| GBP | 2y | -2.8 |
| GBP | 3y | -2.4 |
| GBP | 4y | -2.2 |
| GBP | 5y | -2.3 |
| GBP | 7y | -3.0 |
| GBP | 10y | -3.8 |
| GBP | 15y | -4.3 |
| GBP | 20y | -4.6 |
| GBP | 25y | -4.7 |
| USD | 1m | 5.4 |
| USD | 2m | 1.1 |
| USD | 3m | -0.4 |
| USD | 4m | -1.5 |
| USD | 6m | -2.7 |
| USD | 1y | -4.4 |
| USD | 2y | -5.4 |
| USD | 3y | -7.3 |
| USD | 5y | -9.2 |
| USD | 7y | -9.1 |
| USD | 10y | -9.2 |
| USD | 20y | -9.1 |
| USD | 30y | -9.1 |
| GBPUSD | spot | -15.0 |

### Unexplained over threshold

| trade_id | product | actual_pnl | unexplained | of_which_rate_convexity |
|---|---|---|---|---|
| NBM-SWO-003 | SWPTN | 119,985 | 4,768 | 4,675 |
| NBM-SWO-004 | SWPTN | 39,524 | -3,653 | -3,644 |


### By trade

| trade_id | product | carry | gbp_delta_pred | gbp_rates_actual | usd_delta_pred | usd_rates_actual | fx_delta_pred | fx_actual | vega_pred | vols_actual | new_trades | actual_pnl | unexplained | of_which_rate_convexity | flag |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| NBM-IRS-001 | OIS | 5 | -46,071 | -46,038 | 0 | 0 | -1,965 | -1,896 | 0 | 0 | 0 | -47,930 | 102 | -23 |  |
| NBM-IRS-002 | OIS | 11 | 18,349 | 18,357 | 0 | 0 | 794 | 767 | 0 | 0 | 0 | 19,135 | -20 | 8 |  |
| NBM-IRS-003 | OIS | 4 | -27,990 | -28,003 | 0 | 0 | -51 | -9 | 0 | 0 | 0 | -28,008 | 29 | -13 |  |
| NBM-IRS-004 | OIS | -2 | 26,303 | 26,322 | 0 | 0 | 24 | -15 | 0 | 0 | 0 | 26,305 | -20 | 19 |  |
| NBM-IRS-005 | OIS | 6 | -58,304 | -58,404 | 0 | 0 | -93 | -5 | 0 | 0 | 0 | -58,403 | -12 | -99 |  |
| NBM-IRS-006 | OIS | -45 | 45,720 | 45,567 | 0 | 0 | 643 | 575 | 0 | 0 | 0 | 46,097 | -221 | 30 |  |
| NBM-IRS-007 | OIS | -167 | 0 | 0 | -157,140 | -156,951 | -0 | 0 | 0 | 0 | 0 | -157,118 | 189 | -233 |  |
| NBM-IRS-010 | OIS | 120 | 0 | 0 | 83,897 | 83,727 | -0 | 0 | 0 | 0 | 0 | 83,847 | -171 | 159 |  |
| NBM-FXF-001 | FXFWD | -374 | 3 | 2 | 562 | 606 | -19,845 | -19,845 | 0 | 0 | 0 | -19,611 | 43 | -0 |  |
| NBM-FXF-002 | FXFWD | 991 | -172 | -161 | 357 | 357 | 49,268 | 49,268 | 0 | 0 | 0 | 50,455 | 11 | 0 |  |
| NBM-FXF-003 | FXFWD | -507 | 747 | 743 | -2,553 | -2,554 | -29,248 | -29,249 | 0 | 0 | 0 | -31,567 | -6 | -0 |  |
| NBM-FXF-004 | FXFWD | 313 | -1,933 | -1,933 | 4,372 | 4,374 | 15,236 | 15,239 | 0 | 0 | 0 | 17,992 | 4 | 2 |  |
| NBM-FXF-005 | FXFWD | -453 | -30 | -36 | 353 | 800 | -23,737 | -23,736 | 0 | 0 | 0 | -23,426 | 441 | -0 |  |
| NBM-FXO-001 | FXOPT | -2,194 | 1 | -1 | 331 | 331 | -10,972 | -10,784 | 0 | 0 | 0 | -12,648 | 186 | 0 |  |
| NBM-FXO-002 | FXOPT | -1,547 | -21 | -20 | 44 | 44 | 6,191 | 6,225 | 0 | 0 | 0 | 4,703 | 35 | 0 |  |
| NBM-FXO-003 | FXOPT | 1,163 | -188 | -188 | 643 | 642 | 7,423 | 7,222 | -0 | 0 | 0 | 8,839 | -201 | -2 |  |
| NBM-FXO-004 | FXOPT | 236 | 412 | 412 | -984 | -986 | -3,255 | -3,294 | -0 | 0 | 0 | -3,632 | -41 | -5 |  |
| NBM-FXO-005 | FXOPT | -770 | 2,826 | 2,834 | -4,955 | -4,956 | -10,825 | -10,723 | 0 | 0 | 0 | -13,615 | 110 | 25 |  |
| NBM-SWO-001 | SWPTN | -781 | -25,745 | -25,220 | 0 | 0 | -1,137 | -1,099 | 0 | 0 | 0 | -27,100 | 563 | 334 |  |
| NBM-SWO-002 | SWPTN | 314 | -3,970 | -4,106 | 0 | 0 | 82 | 88 | -0 | 0 | 0 | -3,705 | -130 | -136 |  |
| NBM-SWO-003 | SWPTN | -918 | 0 | 0 | 116,135 | 120,903 | -0 | 0 | 0 | 0 | 0 | 119,985 | 4,768 | 4,675 | INVESTIGATE |
| NBM-SWO-004 | SWPTN | 1,279 | 0 | 0 | 41,898 | 38,245 | -0 | 0 | -0 | 0 | 0 | 39,524 | -3,653 | -3,644 | INVESTIGATE |
| NBM-XCY-001 | XCCY | -155 | -0 | 0 | 0 | 0 | -40,062 | -40,062 | 0 | 0 | 0 | -40,217 | 0 | 0 |  |
| NBM-XCY-002 | XCCY | 154 | 56 | 56 | 0 | -0 | 29,956 | 29,956 | 0 | 0 | 0 | 30,165 | -0 | 0 |  |
| NBM-IRS-008 | OIS | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | -13,256 | -13,256 | 0 | 0 |  |
| NBM-IRS-009 | OIS | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | -93,948 | -93,948 | 0 | 0 |  |

## Fixings and coupon settlement

| trade_id | index | period_start | period_end | status | compounded_rate_pct | index_rate_pct | diff_bp | filled_fixings | check |
|---|---|---|---|---|---|---|---|---|---|
| NBM-IRS-001 | SONIA | 2025-03-17 | 2026-03-17 | last settled | 4.122858 | 4.122858 | -0.000000 | 0 | OK |
| NBM-IRS-001 | SONIA | 2026-03-17 | 2027-03-17 | accruing | 3.770637 | 3.770637 | 0.000001 | 0 | OK |
| NBM-IRS-002 | SONIA | 2026-01-15 | 2027-01-15 | accruing | 3.781749 | 3.781749 | 0.000001 | 0 | OK |
| NBM-IRS-007 | SOFR | 2025-06-02 | 2026-06-02 | last settled | 4.036100 | 4.036098 | 0.000250 | 1 | OK |
| NBM-IRS-007 | SOFR | 2026-06-02 | 2027-06-02 | accruing | 3.706174 | 3.706173 | 0.000133 | 0 | OK |
| NBM-IRS-010 | SOFR | 2026-02-17 | 2027-02-17 | accruing | 3.704214 | 3.704208 | 0.000563 | 1 | OK |
| NBM-XCY-001 | SONIA | 2026-05-19 | 2026-08-19 | last settled | 3.747691 | 3.747691 | -0.000001 | 0 | OK |
| NBM-XCY-001 | SONIA | 2026-08-19 | 2026-11-19 | accruing | 3.741552 | 3.741552 | 0.000002 | 0 | OK |
| NBM-XCY-001 | SOFR | 2026-05-19 | 2026-08-19 | last settled | 3.634886 | 3.634886 | -0.000009 | 0 | OK |
| NBM-XCY-001 | SOFR | 2026-08-19 | 2026-11-19 | accruing | 3.768338 | 3.768335 | 0.000292 | 0 | OK |
| NBM-XCY-002 | SONIA | 2026-04-20 | 2026-07-20 | last settled | 3.747043 | 3.747043 | 0.000002 | 0 | OK |
| NBM-XCY-002 | SONIA | 2026-07-20 | 2026-10-20 | pays within horizon | 3.747372 | 3.747372 | 0.000000 | 0 | OK |
| NBM-XCY-002 | SOFR | 2026-04-20 | 2026-07-20 | last settled | 3.627809 | 3.627811 | -0.000124 | 0 | OK |
| NBM-XCY-002 | SOFR | 2026-07-20 | 2026-10-20 | pays within horizon | 3.731867 | 3.731865 | 0.000241 | 0 | OK |

Completed periods (amounts in the leg's currency; positive is a receipt):

| trade_id | ccy | period_end | floating_amount | fixed_or_spread_amount | net_amount |
|---|---|---|---|---|---|
| NBM-IRS-001 | GBP | 2026-03-17 | 2,061,428.87 | -2,050,000.00 | 11,428.87 |
| NBM-IRS-007 | USD | 2026-06-02 | 2,455,294.20 | -2,433,333.33 | 21,960.87 |
| NBM-XCY-001 | GBP | 2026-08-19 | 188,924.68 | 0.00 | 188,924.68 |
| NBM-XCY-001 | USD | 2026-08-19 | -247,091.46 | -0.00 | -247,091.46 |
| NBM-XCY-002 | GBP | 2026-07-20 | -140,129.12 | 5,609.59 | -134,519.54 |
| NBM-XCY-002 | USD | 2026-07-20 | 185,010.72 | 0.00 | 185,010.72 |
