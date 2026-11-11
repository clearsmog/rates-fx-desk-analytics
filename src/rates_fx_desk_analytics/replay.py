"""Replay of the desk's daily run over a period.

    uv run python -m rates_fx_desk_analytics.replay 2026-08-19 2026-10-15

Runs the daily P&L explain and the delta ladder for every pair of consecutive
valuation dates in the window and writes ``outputs/replay_<start>_<end>/``.
A valuation date needs all three market sources (Bank of England curve, US
Treasury curve, ECB spot), so UK and US holidays drop out.

The book is synthetic; trades enter on their trade dates. The explain does not
model cash leaving the book, so the window should hold no coupons, deliveries
or expiries: any that fall in it are listed in the notes.
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import pandas as pd

from . import data as D
from . import dailypnl as DP
from . import risk as R
from .cycle import PORTFOLIO, ROOT, _md_table, write_excel
from .market import build_market
from .trades import load_portfolio


def valuation_dates(start: date, end: date) -> list[date]:
    boe = set(D.boe_ois_archive().dropna(how="all").index) | set(
        D.boe_ois_curve(end.strftime("%Y-%m")).dropna(how="all").index
    )
    ust = set(D.treasury_par(end.year).dropna(how="all").index)
    fx = set(D.ecb_fx(date(2026, 6, 1), date(2026, 10, 16)).dropna().index)
    return sorted(d for d in boe & ust & fx if start <= d <= end)


def run(start: date, end: date) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    """Returns (one row per day, one row per flagged trade-day, notes)."""
    trades = load_portfolio(PORTFOLIO)
    days = valuation_dates(start, end)
    daily, flagged, notes = [], [], []
    for t0, t1 in zip(days[:-1], days[1:]):
        per_trade, summary, moves, day_notes = DP.daily_explain(t0, t1, trades)
        s = summary.set_index("line")
        mkt = build_market(t1)
        book = R.book_on(trades, t1)
        f = per_trade[per_trade["flag"] != ""]
        mv = moves.set_index(["ccy", "tenor"])["move_bp"]
        daily.append(
            {
                "date": t1,
                "trades": len(book),
                "gbp_5y_move_bp": mv["GBP", "5y"],
                "usd_5y_move_bp": mv["USD", "5y"],
                "gbpusd_move_pct": mv["GBPUSD", "spot"] / 100,
                "carry": s.loc["carry (revalued)", "revalued"],
                "new_trades": s.loc["new trades (day-one value)", "revalued"],
                # existing book only: a new trade's day-one value is mostly
                # premium, whose cash the model does not carry
                "predicted_from_risk": s.loc["total", "predicted_from_risk"] - s.loc["new trades (day-one value)", "revalued"],
                "revalued": s.loc["total", "revalued"] - s.loc["new trades (day-one value)", "revalued"],
                "unexplained": s.loc["total", "unexplained"],
                "rate_convexity": per_trade["of_which_rate_convexity"].sum(),
                "fx_gamma": per_trade["of_which_fx_gamma"].sum(),
                "rates_fx_cross": per_trade["of_which_rates_fx_cross"].sum(),
                "curve_basis": per_trade["of_which_curve_basis"].sum(),
                "gross_unexplained": per_trade["unexplained"].abs().sum(),
                "flagged_trades": len(f),
                "gbp_delta_per_bp": R.parallel_delta(book, mkt, "GBP"),
                "usd_delta_per_bp": R.parallel_delta(book, mkt, "USD"),
                "fx_delta_per_pct": R.fx_delta(book, mkt),
            }
        )
        for r in f.itertuples():
            flagged.append(
                {
                    "date": t1,
                    "trade_id": r.trade_id,
                    "product": r.product,
                    "actual_pnl": r.actual_pnl,
                    "unexplained": r.unexplained,
                    "of_which_rate_convexity": r.of_which_rate_convexity,
                    "of_which_fx_gamma": r.of_which_fx_gamma,
                    "of_which_rates_fx_cross": r.of_which_rates_fx_cross,
                    "of_which_curve_basis": r.of_which_curve_basis,
                    "remaining": r.unexplained
                    - r.of_which_rate_convexity
                    - r.of_which_fx_gamma
                    - r.of_which_rates_fx_cross
                    - r.of_which_curve_basis,
                }
            )
        notes += [f"{t1}: {n}" for n in day_notes]
    return pd.DataFrame(daily), pd.DataFrame(flagged), notes


CAUSES = ["of_which_rate_convexity", "of_which_fx_gamma", "of_which_rates_fx_cross", "of_which_curve_basis"]


def main_cause(row) -> str:
    return max(CAUSES, key=lambda c: abs(row[c])).removeprefix("of_which_")


def write(start: date, end: date, daily: pd.DataFrame, flagged: pd.DataFrame, notes: list[str]) -> Path:
    out = ROOT / "outputs" / f"replay_{start}_{end}"
    out.mkdir(parents=True, exist_ok=True)
    flagged = flagged.assign(main_cause=flagged.apply(main_cause, axis=1))
    by_cause = (
        flagged.groupby(["product", "main_cause"], as_index=False)
        .agg(trade_days=("trade_id", "size"), largest_unexplained=("unexplained", lambda s: s.abs().max()),
             largest_remaining=("remaining", lambda s: s.abs().max()))
    )
    gross_pnl, gross_unx = daily["revalued"].abs().sum(), daily["unexplained"].abs().sum()
    lines = [
        f"# Desk replay — {daily['date'].iloc[0]} to {daily['date'].iloc[-1]} ({len(daily)} business days)",
        "",
        "Synthetic book, own model, USD. Each day's P&L on the existing book is predicted from the prior close's risk "
        "and compared with full revaluation. New trades' day-one value is left out of both (premium cash is not "
        "modelled). GBP curve: Bank of England OIS. USD curve: US Treasury par yields as a SOFR OIS **proxy**. "
        "Vols are **synthetic** and static.",
        "",
        "## Summary",
        "",
        f"- Sum of absolute daily P&L: {gross_pnl:,.0f}; sum of absolute daily unexplained: {gross_unx:,.0f} "
        f"({gross_unx / gross_pnl:.1%})",
        f"- Largest daily unexplained: {daily['unexplained'].abs().max():,.0f}",
        f"- Trade-days over the {DP.THRESHOLD_USD:,.0f} threshold: {len(flagged)}, on {flagged['date'].nunique()} of {len(daily)} days",
        f"- After the four measured causes, the largest amount left on any flagged trade-day is "
        f"{flagged['remaining'].abs().max():,.0f}",
        "",
        "## Flagged trade-days by product and main cause",
        "",
        _md_table(by_cause),
        "",
        "## By day",
        "",
        _md_table(daily[["date", "trades", "gbp_5y_move_bp", "usd_5y_move_bp", "gbpusd_move_pct", "predicted_from_risk",
                         "revalued", "unexplained", "flagged_trades"]], ",.1f"),
        "",
        "## Flagged trade-days",
        "",
        _md_table(flagged),
        "",
        "## Notes",
        "",
        *([f"- {n}" for n in notes] or ["- No coupons, deliveries or expiries fell in the window."]),
        "",
    ]
    (out / "replay.md").write_text("\n".join(lines))
    write_excel(out / "replay.xlsx", {"Daily": daily, "Flagged": flagged, "ByCause": by_cause})
    daily.to_csv(out / "daily.csv", index=False)
    flagged.to_csv(out / "flagged.csv", index=False)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Replay the desk run over a period")
    ap.add_argument("start", type=date.fromisoformat)
    ap.add_argument("end", type=date.fromisoformat)
    a = ap.parse_args()
    daily, flagged, notes = run(a.start, a.end)
    out = write(a.start, a.end, daily, flagged, notes)
    print(f"{len(daily)} days, {len(flagged)} flagged trade-days, largest remaining {flagged['remaining'].abs().max():,.0f}")
    print(f"report: {out.relative_to(ROOT)}/replay.md, .xlsx")


if __name__ == "__main__":
    main()
