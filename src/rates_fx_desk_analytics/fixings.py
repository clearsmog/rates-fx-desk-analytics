"""Fixings and coupon settlement check for the overnight floating legs.

For every SONIA or SOFR accrual period on the book that has settled most
recently, is accruing, or pays within the next few business days:

- the compounded rate from the daily fixings (the pricers' own routine) is set
  beside the rate implied by the published compounded index (Bank of England
  SONIA Compounded Index, New York Fed SOFR Index), an independent source;
- fixings that were missing and filled from the previous day are counted;
- for a completed period, the floating, fixed (or spread) and net amounts are
  computed from the trade terms.

Zero-day lookback and no payment lag, as in the pricers.
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from . import data as D
from .curves import CONVENTIONS
from .dates import add_business_days, schedule, year_fraction
from .market import Market
from .pricing import XCCY_FREQ, realised_compounding
from .trades import OISSwap, Trade, XCCYSwap

INDEX_TOL_BP = 0.001  # own compounding vs published index, in bp of rate
INDEX_WINDOW = (date(2024, 10, 1), date(2026, 10, 16))  # as market.build_market


def _legs(t: Trade) -> list[dict]:
    """Floating legs as (ccy, notional, fixed rate or spread, frequency, sign).
    ``sign`` is +1 where the book receives the floating leg."""
    if isinstance(t, OISSwap):
        return [dict(ccy=t.ccy, notional=t.notional, fixed=t.fixed_rate, spread=0.0,
                     freq=CONVENTIONS[t.ccy]["freq"], sign=1.0 if t.pay_fixed else -1.0)]
    if isinstance(t, XCCYSwap):
        s = 1.0 if t.receive_gbp else -1.0
        return [
            dict(ccy="GBP", notional=t.notional, fixed=0.0, spread=t.spread, freq=XCCY_FREQ, sign=s),
            dict(ccy="USD", notional=t.notional_usd, fixed=0.0, spread=0.0, freq=XCCY_FREQ, sign=-s),
        ]
    return []


def check(trades: list[Trade], mkt: Market, horizon_days: int = 5) -> pd.DataFrame:
    asof = mkt.asof
    index = {"SONIA": D.sonia_index(*INDEX_WINDOW), "SOFR": D.sofr_index(*INDEX_WINDOW)}
    rows = []
    for t in trades:
        for leg in _legs(t):
            c = CONVENTIONS[leg["ccy"]]
            horizon = add_business_days(asof, horizon_days, c["cal"])
            periods = schedule(t.start, t.end, leg["freq"], c["cal"])
            settled = [p for p in periods if p.end <= asof]
            live = [p for p in periods if p.start < asof < p.end]
            for p, status in [(p, "last settled") for p in settled[-1:]] + [(p, "accruing") for p in live]:
                to = min(p.end, asof)
                factor, filled = realised_compounding(mkt.fixings[c["index"]], p.start, to, c["cal"], c["day_count"])
                yf = year_fraction(p.start, to, c["day_count"])
                idx = index[c["index"]]
                idx_factor = idx[to] / idx[p.start] if to in idx.index and p.start in idx.index else float("nan")
                diff_bp = (factor - idx_factor) / yf * 1e4
                complete = to == p.end
                floating = leg["sign"] * leg["notional"] * (factor - 1.0)
                other = leg["sign"] * leg["notional"] * (leg["spread"] - leg["fixed"]) * yf
                rows.append(
                    {
                        "trade_id": t.trade_id,
                        "index": c["index"],
                        "period_start": p.start,
                        "period_end": p.end,
                        "status": "pays within horizon" if status == "accruing" and p.end <= horizon else status,
                        "fixed_to": to,
                        "compounded_rate_pct": (factor - 1.0) / yf * 100,
                        "index_rate_pct": (idx_factor - 1.0) / yf * 100,
                        "diff_bp": diff_bp,
                        "filled_fixings": filled,
                        "check": "OK" if abs(diff_bp) <= INDEX_TOL_BP else "INVESTIGATE",
                        "ccy": leg["ccy"],
                        "floating_amount": floating if complete else float("nan"),
                        "fixed_or_spread_amount": other if complete else float("nan"),
                        "net_amount": floating + other if complete else float("nan"),
                    }
                )
    return pd.DataFrame(rows)
