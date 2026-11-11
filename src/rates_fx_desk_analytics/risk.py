"""Desk risk report: bucketed delta, vega and FX delta, with the day's change.

Delta is quoted the way a swaps desk reads it: each par OIS quote on the curve
is raised by 1bp in turn, the curve is bootstrapped again and the book is
revalued. The ladder therefore says which market instrument hedges the risk,
unlike ``pricing.sensitivities``, which shifts the whole zero curve.

Vega is per trade for a parallel move in the vol input (1bp normal vol for
swaptions, 1 vol point for FX options) and is grouped by expiry and, for
swaptions, underlying tenor. The vol inputs are synthetic.

All figures are in USD at the valuation date's spot.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from pathlib import Path

import pandas as pd

from . import curves as C
from . import pricing as P
from .market import Market
from .trades import FXOption, Swaption, Trade

TRADE_DATES = Path(__file__).resolve().parents[2] / "data" / "trades" / "trade_dates.csv"
EXPIRY_BUCKETS = [(0.25, "0-3m"), (0.5, "3-6m"), (1.0, "6-12m"), (2.0, "1-2y"), (99.0, "2y+")]


def book_on(trades: list[Trade], d: date) -> list[Trade]:
    """Trades with a trade date on or before ``d``."""
    td = {r.trade_id: date.fromisoformat(r.trade_date) for r in pd.read_csv(TRADE_DATES).itertuples()}
    return [t for t in trades if td[t.trade_id] <= d]


def value_usd(trades: list[Trade], mkt: Market) -> float:
    return sum(P.to_usd(P.price(t, mkt), P.pv_ccy(t), mkt) for t in trades)


def tenor_label(months: int) -> str:
    return f"{months}m" if months < 12 or months % 12 else f"{months // 12}y"


def rebuilt(mkt: Market, ccy: str, quotes: list[tuple[int, float]]) -> Market:
    """The market with ``ccy``'s curve bootstrapped from ``quotes``."""
    curve = C.bootstrap(mkt.asof, ccy, quotes, mkt.curves[ccy].label)
    return replace(mkt, curves={**mkt.curves, ccy: curve})


def bump_quote(mkt: Market, ccy: str, tenor_m: int | None, bp: float = 1.0) -> Market:
    """One par quote (or all of them, ``tenor_m=None``) moved by ``bp``."""
    quotes = [
        (m, r + bp * 1e-4 if tenor_m in (None, m) else r)
        for m, r in mkt.curves[ccy].quotes
    ]
    return rebuilt(mkt, ccy, quotes)


def delta_ladder(trades: list[Trade], mkt: Market) -> pd.DataFrame:
    """USD value change per +1bp on each par quote, one row per quote."""
    rows = []
    for ccy in ("GBP", "USD"):
        base = value_usd(trades, rebuilt(mkt, ccy, mkt.curves[ccy].quotes))
        for m, rate in mkt.curves[ccy].quotes:
            rows.append(
                {
                    "ccy": ccy,
                    "tenor": tenor_label(m),
                    "tenor_m": m,
                    "par_rate_pct": rate * 100,
                    "delta_usd_per_bp": value_usd(trades, bump_quote(mkt, ccy, m)) - base,
                }
            )
    return pd.DataFrame(rows)


def parallel_delta(trades: list[Trade], mkt: Market, ccy: str) -> float:
    """USD value change for +1bp on every par quote at once (ladder check)."""
    base = value_usd(trades, rebuilt(mkt, ccy, mkt.curves[ccy].quotes))
    return value_usd(trades, bump_quote(mkt, ccy, None)) - base


def fx_delta(trades: list[Trade], mkt: Market) -> float:
    """USD value change per +1% in GBP/USD, including the translation of GBP
    values. Central difference."""
    up = value_usd(trades, mkt.bump_spot("GBPUSD", 0.01))
    down = value_usd(trades, mkt.bump_spot("GBPUSD", -0.01))
    return (up - down) / 2


def _expiry_bucket(t_exp: float) -> str:
    return next(label for limit, label in EXPIRY_BUCKETS if t_exp <= limit)


def vega_table(trades: list[Trade], mkt: Market) -> pd.DataFrame:
    """Vega by product, currency (or pair), expiry bucket and underlying tenor."""
    rows = []
    for t in trades:
        if not isinstance(t, FXOption | Swaption) or t.expiry < mkt.asof:
            continue
        sens = P.sensitivities(t, mkt)
        swaption = isinstance(t, Swaption)
        rows.append(
            {
                "product": t.product,
                "underlying": t.ccy if swaption else t.pair,
                "expiry_bucket": _expiry_bucket(C.t_of(mkt.asof, t.expiry)),
                "tenor": f"{round(P.swaption_tenor(t))}y" if swaption else "",
                "unit": "1bp normal vol" if swaption else "1 vol point",
                "vega_usd": P.to_usd(sens["vega_1bp" if swaption else "vega_1pt"], P.pv_ccy(t), mkt),
            }
        )
    cols = ["product", "underlying", "expiry_bucket", "tenor", "unit"]
    if not rows:
        return pd.DataFrame(columns=cols + ["vega_usd", "trades"])
    df = pd.DataFrame(rows)
    labels = [label for _, label in EXPIRY_BUCKETS]
    df["expiry_bucket"] = pd.Categorical(df["expiry_bucket"], labels, ordered=True)
    out = df.groupby(cols, as_index=False, observed=True).agg(
        vega_usd=("vega_usd", "sum"), trades=("vega_usd", "size")
    )
    return out.astype({"expiry_bucket": str})


def ladder_change(trades: list[Trade], mkt: Market, prior: Market) -> pd.DataFrame:
    """Today's ladder beside yesterday's close, with the part of the change
    that comes from trades booked today."""
    today = delta_ladder(book_on(trades, mkt.asof), mkt)
    old_book = book_on(trades, prior.asof)
    was = delta_ladder(old_book, prior).set_index(["ccy", "tenor_m"])["delta_usd_per_bp"]
    new = [t for t in book_on(trades, mkt.asof) if t not in old_book]
    from_new = delta_ladder(new, mkt).set_index(["ccy", "tenor_m"])["delta_usd_per_bp"]
    keys = list(zip(today["ccy"], today["tenor_m"]))
    today["prior_close"] = [was.get(k, 0.0) for k in keys]
    today["change"] = today["delta_usd_per_bp"] - today["prior_close"]
    today["from_new_trades"] = [from_new.get(k, 0.0) for k in keys]
    today["from_market_and_time"] = today["change"] - today["from_new_trades"]
    return today
