"""The desk's daily run: risk, P&L explain and fixings.

    uv run python -m rates_fx_desk_analytics.desk 2026-10-15 --prior 2026-10-14

Writes ``outputs/<asof>/desk_report.md`` and ``.xlsx``:

1. delta ladder by par quote, against the prior close, with the part of the
   change that comes from trades booked today
2. vega by expiry and tenor, and FX delta
3. daily P&L: predicted from the prior close's risk against full revaluation,
   with unexplained amounts over the threshold listed
4. fixings and coupon settlement check against the published SONIA and SOFR
   compounded indices
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import pandas as pd

from . import dailypnl as DP
from . import fixings as F
from . import risk as R
from .cycle import PORTFOLIO, ROOT, _md_table, write_excel
from .market import build_market
from .trades import load_portfolio


def run(asof: date, prior: date, outdir: Path | None = None) -> dict[str, pd.DataFrame]:
    outdir = outdir or ROOT / "outputs" / str(asof)
    outdir.mkdir(parents=True, exist_ok=True)
    mkt, prior_mkt = build_market(asof), build_market(prior)
    trades = load_portfolio(PORTFOLIO)
    book = R.book_on(trades, asof)

    ladder = R.ladder_change(trades, mkt, prior_mkt)
    checks = pd.DataFrame(
        [
            {
                "ccy": ccy,
                "ladder_sum": ladder.loc[ladder["ccy"] == ccy, "delta_usd_per_bp"].sum(),
                "all_quotes_plus_1bp": R.parallel_delta(book, mkt, ccy),
            }
            for ccy in ("GBP", "USD")
        ]
    )
    checks["difference"] = checks["ladder_sum"] - checks["all_quotes_plus_1bp"]
    vega = R.vega_table(book, mkt)
    fx = pd.DataFrame(
        [
            {"measure": "FX delta, USD per +1% GBP/USD", "today": R.fx_delta(book, mkt),
             "prior_close": R.fx_delta(R.book_on(trades, prior), prior_mkt)}
        ]
    )
    per_trade, summary, moves, notes = DP.daily_explain(prior, asof, trades)
    fix = F.check(book, mkt)

    sheets = {
        "DeltaLadder": ladder.drop(columns=["tenor_m"]),
        "LadderCheck": checks,
        "Vega": vega,
        "FXDelta": fx,
        "PnLSummary": summary,
        "PnLByTrade": per_trade,
        "Moves": moves,
        "Fixings": fix,
    }
    write_markdown(outdir / "desk_report.md", asof, prior, len(book), sheets, notes)
    write_excel(outdir / "desk_report.xlsx", sheets)
    return sheets


def write_markdown(path: Path, asof: date, prior: date, n_trades: int, s: dict[str, pd.DataFrame], notes: list[str]) -> None:
    flagged = s["PnLByTrade"][s["PnLByTrade"]["flag"] != ""]
    fix = s["Fixings"]
    total = s["PnLSummary"].set_index("line").loc["total"]
    lines = [
        f"# Desk report — {asof} (prior close {prior})",
        "",
        f"Synthetic book ({n_trades} trades), own model, USD. GBP curve: Bank of England OIS. USD curve: US Treasury "
        "par yields as a SOFR OIS **proxy**. FX and swaption vols are **synthetic** and static.",
        "",
        "## Summary",
        "",
        f"- Daily P&L: {total['revalued']:,.0f} revalued, {total['predicted_from_risk']:,.0f} predicted from the "
        f"prior close's risk, {total['unexplained']:,.0f} unexplained",
        f"- Trades over the {DP.THRESHOLD_USD:,.0f} unexplained threshold: {len(flagged)}"
        + (f" ({', '.join(flagged['trade_id'])})" if len(flagged) else ""),
        f"- Fixings: {(fix['check'] == 'OK').sum()}/{len(fix)} periods agree with the published index within "
        f"{F.INDEX_TOL_BP}bp; {int(fix['filled_fixings'].sum())} fixings filled from the previous day",
        "",
        "## Delta ladder (USD per +1bp on each par quote)",
        "",
        _md_table(s["DeltaLadder"][s["DeltaLadder"][["delta_usd_per_bp", "prior_close"]].abs().sum(axis=1) > 0.5].drop(columns=["par_rate_pct"])),
        "",
        "Check: the ladder against all quotes moved together.",
        "",
        _md_table(s["LadderCheck"], ",.1f"),
        "",
        "## Vega and FX delta",
        "",
        _md_table(s["Vega"]),
        "",
        _md_table(s["FXDelta"]),
        "",
        "## Daily P&L explain",
        "",
        _md_table(s["PnLSummary"]),
        "",
        "Market moves (bp; spot in bp of the rate):",
        "",
        _md_table(s["Moves"], ",.1f"),
        "",
        "### Unexplained over threshold",
        "",
        _md_table(flagged[["trade_id", "product", "actual_pnl", "unexplained", "of_which_rate_convexity"]])
        if len(flagged)
        else "None.",
        "",
        *[f"- {n}" for n in notes],
        "",
        "### By trade",
        "",
        _md_table(s["PnLByTrade"].drop(columns=["status"])),
        "",
        "## Fixings and coupon settlement",
        "",
        _md_table(fix[["trade_id", "index", "period_start", "period_end", "status", "compounded_rate_pct", "index_rate_pct", "diff_bp", "filled_fixings", "check"]], ",.6f"),
        "",
        "Completed periods (amounts in the leg's currency; positive is a receipt):",
        "",
        _md_table(fix.loc[fix["status"] == "last settled", ["trade_id", "ccy", "period_end", "floating_amount", "fixed_or_spread_amount", "net_amount"]], ",.2f"),
        "",
    ]
    path.write_text("\n".join(lines))


def main() -> None:
    ap = argparse.ArgumentParser(description="Desk daily risk, P&L explain and fixings run")
    ap.add_argument("asof", type=date.fromisoformat)
    ap.add_argument("--prior", type=date.fromisoformat, required=True, help="previous business day")
    a = ap.parse_args()
    s = run(a.asof, a.prior)
    print(s["PnLSummary"].to_string(index=False, float_format=lambda x: f"{x:,.0f}"))
    print(s["Fixings"]["check"].value_counts().to_string())
    print(f"report: outputs/{a.asof}/desk_report.md, .xlsx")


if __name__ == "__main__":
    main()
