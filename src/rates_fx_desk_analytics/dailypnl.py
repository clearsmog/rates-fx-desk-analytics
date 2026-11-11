"""Daily P&L explain: yesterday's risk against today's revaluation.

    predicted = delta ladder x move in each par quote
              + FX delta x move in spot
              + vega x move in vol
    actual    = full revaluation, one block of market data at a time
    unexplained = actual - predicted, per trade

The risk is measured on yesterday's curves rolled to today (``market.roll_to``),
so roll-down sits in carry and the quote moves are the market's own. Carry and
the day-one value of new trades are revalued, not predicted. What the risk
cannot see (rate convexity, FX gamma, the cross effect of rates and spot) lands
in unexplained, and any trade over the threshold is listed for investigation.
Four causes are measured: rate convexity (all the quote moves applied
together, less the linear ladder sum), FX gamma (the spot move applied on its
own, less the linear delta term), the rates-FX cross effect (the rest of the
revalued spot step: mostly the day's GBP rates P&L translated at the new spot)
and curve basis (yesterday's curve rolled forward is not exactly the curve its
own par quotes rebuild, which shows after a weekend).

Vols are synthetic and static, so the vega line is zero by construction.
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from . import curves as C
from . import pricing as P
from . import risk as R
from .market import Market, build_market, roll_to
from .monthend import cash_events, explain
from .trades import FXOption, Swaption, Trade

THRESHOLD_USD = 1_000.0  # unexplained per trade


def quote_moves(rolled: Market, today: Market, ccy: str) -> dict[int, float]:
    """Move in each par quote, bp: today's close against yesterday's curve
    rolled to today."""
    was = dict(C.par_quotes(rolled.curves[ccy], [m for m, _ in today.curves[ccy].quotes]))
    return {m: (r - was[m]) * 1e4 for m, r in today.curves[ccy].quotes if m in was}


def _trade_prediction(t: Trade, rolled: Market, today: Market, moves: dict[str, dict[int, float]]) -> dict[str, float]:
    one = [t]
    out, convexity, basis = {}, 0.0, 0.0
    for ccy in ("GBP", "USD"):
        quotes = dict(C.par_quotes(rolled.curves[ccy], list(moves[ccy])))
        base_mkt = R.rebuilt(rolled, ccy, sorted(quotes.items()))
        base = R.value_usd(one, base_mkt)
        # the rolled curve is not exactly the curve its own par quotes rebuild
        basis += base - R.value_usd(one, rolled)
        linear = sum(
            (R.value_usd(one, R.bump_quote(base_mkt, ccy, m)) - base) * bp
            for m, bp in moves[ccy].items()
        )
        moved = [(m, r + moves[ccy][m] * 1e-4) for m, r in sorted(quotes.items())]
        out[f"{ccy.lower()}_delta"] = linear
        # all quote moves applied together, less the linear sum: what a
        # first-order ladder misses (option gamma, swap convexity)
        convexity += R.value_usd(one, R.rebuilt(rolled, ccy, moved)) - base - linear
    spot_move = today.spot["GBPUSD"] / rolled.spot["GBPUSD"] - 1.0
    out["fx_delta"] = R.fx_delta(one, rolled) * spot_move / 0.01
    # the actual spot move applied on its own, less the linear delta term
    out["fx_gamma"] = (
        R.value_usd(one, rolled.bump_spot("GBPUSD", spot_move)) - R.value_usd(one, rolled) - out["fx_delta"]
    )
    vega = 0.0
    if isinstance(t, FXOption) and t.expiry >= rolled.asof:
        t_exp = C.t_of(rolled.asof, t.expiry)
        vol_move = (today.fx_vol[t.pair].vol(t_exp) - rolled.fx_vol[t.pair].vol(t_exp)) * 100
        vega = P.sensitivities(t, rolled)["vega_1pt"] * vol_move
    elif isinstance(t, Swaption) and t.expiry >= rolled.asof:
        t_exp, tenor = C.t_of(rolled.asof, t.expiry), P.swaption_tenor(t)
        vol_move = today.swaption_vol[t.ccy].vol_bp(t_exp, tenor) - rolled.swaption_vol[t.ccy].vol_bp(t_exp, tenor)
        vega = P.to_usd(P.sensitivities(t, rolled)["vega_1bp"], t.ccy, rolled) * vol_move
    out["vega"] = vega
    out["convexity"] = convexity
    out["curve_basis"] = basis
    return out


def daily_explain(t0: date, t1: date, trades: list[Trade]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[str]]:
    """Returns (by trade, summary, quote moves, notes)."""
    m0, m1 = build_market(t0), build_market(t1)
    rolled = roll_to(m0, t1)
    moves = {ccy: quote_moves(rolled, m1, ccy) for ccy in ("GBP", "USD")}
    actual, _, _ = explain(t0, t1)
    actual = actual.set_index("trade_id")
    by_id = {t.trade_id: t for t in trades}

    rows, notes = [], []
    for tid, a in actual.iterrows():
        t = by_id[tid]
        new = a["status"].startswith("new")
        pred = (
            {"gbp_delta": 0.0, "usd_delta": 0.0, "fx_delta": 0.0, "vega": 0.0, "convexity": 0.0, "fx_gamma": 0.0, "curve_basis": 0.0}
            if new
            else _trade_prediction(t, rolled, m1, moves)
        )
        convexity, fx_gamma, basis = pred.pop("convexity"), pred.pop("fx_gamma"), pred.pop("curve_basis")
        total = a["value_t1"] - a["value_t0"]
        predicted = sum(pred.values()) + a["carry"] + a["new_trades"]
        unexplained = total - predicted
        flag = abs(unexplained) > THRESHOLD_USD
        rows.append(
            {
                "trade_id": tid,
                "product": a["product"],
                "status": a["status"],
                "carry": a["carry"],
                "gbp_delta_pred": pred["gbp_delta"],
                "gbp_rates_actual": a["gbp_rates"],
                "usd_delta_pred": pred["usd_delta"],
                "usd_rates_actual": a["usd_rates"],
                "fx_delta_pred": pred["fx_delta"],
                "fx_actual": a["fx_spot"],
                "vega_pred": pred["vega"],
                "vols_actual": a["vols"],
                "new_trades": a["new_trades"],
                "actual_pnl": total,
                "unexplained": unexplained,
                "of_which_rate_convexity": convexity,
                "of_which_fx_gamma": fx_gamma,
                # the spot step is revalued after the rates step, so it also
                # carries the day's rates P&L translated at the new spot
                "of_which_rates_fx_cross": 0.0 if new else a["fx_spot"] - pred["fx_delta"] - fx_gamma,
                "of_which_curve_basis": basis,
                "flag": "INVESTIGATE" if flag else "",
            }
        )
        if not new:
            notes += [f"{tid}: {e} in the period, cash not modelled" for e in cash_events(t, t0, t1)]
    per_trade = pd.DataFrame(rows)

    lines = [
        ("carry (revalued)", per_trade["carry"].sum(), per_trade["carry"].sum()),
        ("GBP rates", per_trade["gbp_delta_pred"].sum(), per_trade["gbp_rates_actual"].sum()),
        ("USD rates", per_trade["usd_delta_pred"].sum(), per_trade["usd_rates_actual"].sum()),
        ("FX spot", per_trade["fx_delta_pred"].sum(), per_trade["fx_actual"].sum()),
        ("vols", per_trade["vega_pred"].sum(), per_trade["vols_actual"].sum()),
        ("new trades (day-one value)", per_trade["new_trades"].sum(), per_trade["new_trades"].sum()),
    ]
    summary = pd.DataFrame(
        [{"line": n, "predicted_from_risk": p, "revalued": a, "unexplained": a - p} for n, p, a in lines]
    )
    total = pd.DataFrame(
        [
            {
                "line": "total",
                "predicted_from_risk": summary["predicted_from_risk"].sum(),
                "revalued": per_trade["actual_pnl"].sum(),
                "unexplained": per_trade["unexplained"].sum(),
            }
        ]
    )
    summary = pd.concat([summary, total], ignore_index=True)
    moves_df = pd.DataFrame(
        [{"ccy": ccy, "tenor": R.tenor_label(m), "move_bp": bp} for ccy in moves for m, bp in moves[ccy].items()]
        + [{"ccy": "GBPUSD", "tenor": "spot", "move_bp": (m1.spot["GBPUSD"] / m0.spot["GBPUSD"] - 1.0) * 1e4}]
    )
    return per_trade, summary, moves_df, notes
