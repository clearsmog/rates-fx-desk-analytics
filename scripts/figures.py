"""README figures (light and dark SVG) and the data file for the website page.

    uv run python scripts/figures.py

Reads the desk report for 2026-10-15 and the replay for 2026-08-19 to
2026-10-15 from ``outputs/`` and writes ``docs/img/*.svg`` and
``outputs/web/rates-fx-desk.json``.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("svg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DESK = ROOT / "outputs" / "2026-10-15" / "desk_report.xlsx"
REPLAY = ROOT / "outputs" / "replay_2026-08-19_2026-10-15"
IMG = ROOT / "docs" / "img"

THEMES = {
    "light": dict(bg="#ffffff", text="#1d1d1f", muted="#6e6e73", grid="#e5e5ea", main="#0071e3", ref="#8e8e93"),
    "dark": dict(bg="#0d1117", text="#f5f5f7", muted="#a1a1a6", grid="#30363d", main="#2f8cf0", ref="#8e8e93"),
}
CAUSES = {
    "of_which_rate_convexity": "Rate convexity",
    "of_which_fx_gamma": "FX gamma",
    "of_which_rates_fx_cross": "Rates-FX cross",
    "of_which_curve_basis": "Curve basis",
    "remaining": "Left after the four causes",
}


def style(ax, t):
    ax.set_facecolor(t["bg"])
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(t["grid"])
    ax.tick_params(colors=t["muted"], length=0, labelsize=9)
    ax.grid(axis="y", color=t["grid"], linewidth=0.8)
    ax.set_axisbelow(True)


def k(v, _=None):
    return f"{v / 1000:,.0f}k" if abs(v) >= 1000 else f"{v:,.0f}"


def save(fig, name, theme):
    fig.savefig(IMG / f"{name}-{theme}.svg", facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)


def ladder_figure(ladder: pd.DataFrame, theme: str):
    t = THEMES[theme]
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.6), facecolor=t["bg"])
    for ax, ccy in zip(axes, ("GBP", "USD")):
        d = ladder[(ladder["ccy"] == ccy) & (ladder[["delta_usd_per_bp", "prior_close"]].abs().sum(axis=1) > 0.5)]
        x = range(len(d))
        ax.bar([i - 0.2 for i in x], d["prior_close"], 0.36, color=t["ref"], label="Prior close (14 Oct)")
        ax.bar([i + 0.2 for i in x], d["delta_usd_per_bp"], 0.36, color=t["main"], label="15 Oct")
        ax.axhline(0, color=t["muted"], linewidth=0.8)
        ax.set_xticks(list(x), d["tenor"])
        ax.yaxis.set_major_formatter(k)
        style(ax, t)
        ax.set_title(f"{ccy} delta, USD per +1bp on each par quote" + (" (Treasury proxy)" if ccy == "USD" else ""),
                     color=t["text"], fontsize=11, loc="left", pad=10)
    usd = ladder[ladder["ccy"] == "USD"].reset_index(drop=True)
    shown = usd[usd[["delta_usd_per_bp", "prior_close"]].abs().sum(axis=1) > 0.5].reset_index(drop=True)
    for tenor in ("2y", "7y"):
        i = shown.index[shown["tenor"] == tenor][0]
        v = shown.loc[i, "delta_usd_per_bp"]
        axes[1].annotate("new swap", (i + 0.2, v), xytext=(0, 6 if v > 0 else -12), textcoords="offset points",
                         ha="center", fontsize=8.5, color=t["text"])
    axes[0].legend(frameon=False, fontsize=9, labelcolor=t["text"], loc="upper left")
    fig.tight_layout(w_pad=3)
    save(fig, "delta-ladder", theme)


def replay_figure(daily: pd.DataFrame, theme: str):
    t = THEMES[theme]
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8), facecolor=t["bg"], gridspec_kw={"width_ratios": [1, 1.5]})
    ax = axes[0]
    lim = max(daily["predicted_from_risk"].abs().max(), daily["revalued"].abs().max()) * 1.08
    ax.plot([-lim, lim], [-lim, lim], color=t["ref"], linewidth=1)
    ax.scatter(daily["predicted_from_risk"], daily["revalued"], s=34, color=t["main"], edgecolor=t["bg"], linewidth=1.2, zorder=3)
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.xaxis.set_major_formatter(k)
    ax.yaxis.set_major_formatter(k)
    ax.set_xlabel("Predicted from the prior close's risk (USD)", color=t["muted"], fontsize=9)
    ax.set_ylabel("Revalued (USD)", color=t["muted"], fontsize=9)
    style(ax, t)
    ax.grid(axis="x", color=t["grid"], linewidth=0.8)
    ax.set_title("Daily P&L, one dot per day (line: predicted = revalued)", color=t["text"], fontsize=11, loc="left", pad=10)

    ax = axes[1]
    x = range(len(daily))
    ax.bar(x, daily["unexplained"], 0.62, color=t["main"])
    ax.axhline(0, color=t["muted"], linewidth=0.8)
    labels = [d.strftime("%-d %b") if i % 5 == 0 else "" for i, d in enumerate(pd.to_datetime(daily["date"]))]
    ax.set_xticks(list(x), labels)
    ax.yaxis.set_major_formatter(k)
    style(ax, t)
    worst = daily["unexplained"].abs().idxmax()
    ax.annotate(f"{daily.loc[worst, 'unexplained']:,.0f}\n{pd.to_datetime(daily.loc[worst, 'date']).strftime('%-d %b')}",
                (worst, daily.loc[worst, "unexplained"]), xytext=(0, 5), textcoords="offset points", ha="center",
                fontsize=8.5, color=t["text"])
    ax.set_ylim(top=daily["unexplained"].max() * 1.25)
    ax.set_title("Daily unexplained P&L, whole book (USD)", color=t["text"], fontsize=11, loc="left", pad=10)
    fig.tight_layout(w_pad=3)
    save(fig, "replay", theme)


def causes_figure(flagged: pd.DataFrame, theme: str):
    t = THEMES[theme]
    totals = pd.Series({label: flagged[col].abs().sum() for col, label in CAUSES.items()})[::-1]
    fig, ax = plt.subplots(figsize=(7.5, 2.9), facecolor=t["bg"])
    ax.barh(totals.index, totals.values, 0.55, color=[t["ref"]] + [t["main"]] * 4)
    for y, v in enumerate(totals.values):
        ax.text(v, y, f"  {v:,.0f}", va="center", fontsize=9, color=t["text"])
    style(ax, t)
    ax.grid(False)
    ax.spines["bottom"].set_visible(False)
    ax.set_xticks([])
    ax.tick_params(axis="y", colors=t["text"], labelsize=10)
    ax.set_xlim(0, totals.max() * 1.18)
    ax.set_title(f"What the {len(flagged)} flagged trade-days were made of (sum of absolute USD)", color=t["text"], fontsize=11, loc="left", pad=10)
    fig.tight_layout()
    save(fig, "causes", theme)


def web_data(sheets: dict[str, pd.DataFrame], daily: pd.DataFrame, flagged: pd.DataFrame) -> dict:
    ladder = sheets["DeltaLadder"]
    out_ladder = {}
    for ccy in ("GBP", "USD"):
        d = ladder[(ladder["ccy"] == ccy) & (ladder[["delta_usd_per_bp", "prior_close"]].abs().sum(axis=1) > 0.5)]
        out_ladder[ccy] = {
            "tenors": d["tenor"].tolist(),
            "today": d["delta_usd_per_bp"].round(0).tolist(),
            "prior": d["prior_close"].round(0).tolist(),
            "fromNew": d["from_new_trades"].round(0).tolist(),
        }
    fix = sheets["Fixings"]
    by_cause = (
        flagged.assign(main=flagged[list(CAUSES)[:4]].abs().idxmax(axis=1).map(CAUSES))
        .groupby(["product", "main"], as_index=False)
        .agg(tradeDays=("trade_id", "size"), largest=("unexplained", lambda s: round(s.abs().max())),
             remaining=("remaining", lambda s: round(s.abs().max())))
    )
    return {
        "asof": "2026-10-15",
        "prior": "2026-10-14",
        "ladder": out_ladder,
        "ladderCheck": sheets["LadderCheck"].round(1).to_dict("records"),
        "vega": sheets["Vega"].round(0).to_dict("records"),
        "pnlSummary": sheets["PnLSummary"].round(0).to_dict("records"),
        "fixings": [
            {**r, "period_start": str(r["period_start"])[:10], "period_end": str(r["period_end"])[:10]}
            for r in fix[["trade_id", "index", "period_start", "period_end", "status", "compounded_rate_pct",
                          "index_rate_pct", "diff_bp", "filled_fixings"]].round(6).to_dict("records")
        ],
        "replay": {
            "days": len(daily),
            "dates": [pd.to_datetime(d).strftime("%-d %b") for d in daily["date"]],
            "predicted": daily["predicted_from_risk"].round(0).tolist(),
            "revalued": daily["revalued"].round(0).tolist(),
            "unexplained": daily["unexplained"].round(0).tolist(),
            "flaggedTrades": daily["flagged_trades"].tolist(),
            "grossPnl": round(daily["revalued"].abs().sum()),
            "grossUnexplained": round(daily["unexplained"].abs().sum()),
            "largestUnexplained": round(daily["unexplained"].abs().max()),
            "flaggedTradeDays": len(flagged),
            "flaggedDays": int(flagged["date"].nunique()),
            "largestRemaining": round(flagged["remaining"].abs().max()),
            "causes": [{"label": label, "value": round(flagged[col].abs().sum())} for col, label in CAUSES.items()],
            "byCause": by_cause.to_dict("records"),
        },
    }


def main() -> None:
    IMG.mkdir(parents=True, exist_ok=True)
    sheets = pd.read_excel(DESK, sheet_name=None)
    daily = pd.read_csv(REPLAY / "daily.csv")
    flagged = pd.read_csv(REPLAY / "flagged.csv")
    for theme in THEMES:
        ladder_figure(sheets["DeltaLadder"], theme)
        replay_figure(daily, theme)
        causes_figure(flagged, theme)
    web = ROOT / "outputs" / "web"
    web.mkdir(parents=True, exist_ok=True)
    (web / "rates-fx-desk.json").write_text(json.dumps(web_data(sheets, daily, flagged), indent=1))
    print(f"figures: {IMG.relative_to(ROOT)}/, data: outputs/web/rates-fx-desk.json")


if __name__ == "__main__":
    main()
