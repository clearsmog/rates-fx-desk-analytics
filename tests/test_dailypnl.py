from otc_valuation_desk.dailypnl import THRESHOLD_USD, daily_explain

from conftest import ASOF, PRIOR


def test_daily_explain_ties_out_and_the_ladder_explains_the_linear_trades(trades):
    per_trade, summary, moves, _ = daily_explain(PRIOR, ASOF, trades)
    s = summary.set_index("line")
    # every line's revalued amounts add up to the total move
    assert abs(s["revalued"].drop("total").sum() - s.loc["total", "revalued"]) < 1e-6
    assert abs(s.loc["total", "revalued"] - s.loc["total", "predicted_from_risk"] - s.loc["total", "unexplained"]) < 1e-6
    # swaps and forwards are close to linear over one day
    linear = per_trade[per_trade["product"].isin(["OIS", "FXFWD", "XCCY"])]
    assert linear["unexplained"].abs().max() < THRESHOLD_USD
    # what is flagged is optional, and rate convexity accounts for most of it
    flagged = per_trade[per_trade["flag"] != ""]
    assert set(flagged["product"]) <= {"SWPTN", "FXOPT"}
    for r in flagged.itertuples():
        assert abs(r.unexplained - r.of_which_rate_convexity) < 0.25 * abs(r.unexplained)
    assert len(moves) > 0
