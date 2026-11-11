from otc_valuation_desk import pricing as P
from otc_valuation_desk import risk as R
from otc_valuation_desk.trades import OISSwap

from conftest import ASOF, PRIOR


def test_ladder_adds_up_to_all_quotes_moved_together(mkt, trades):
    ladder = R.delta_ladder(trades, mkt)
    for ccy in ("GBP", "USD"):
        d = ladder.loc[ladder["ccy"] == ccy, "delta_usd_per_bp"]
        assert abs(d.sum() - R.parallel_delta(trades, mkt, ccy)) < 1e-3 * d.abs().sum()


def test_swap_delta_sits_at_its_maturity(mkt, trades):
    # NBM-IRS-003: a two-year GBP swap starting on the valuation date
    swap = next(t for t in trades if t.trade_id == "NBM-IRS-003")
    ladder = R.delta_ladder([swap], mkt).set_index(["ccy", "tenor"])["delta_usd_per_bp"]
    assert abs(ladder["GBP", "2y"]) > 0.99 * ladder.abs().sum()
    # paying fixed gains when rates rise
    assert ladder["GBP", "2y"] > 0


def test_ladder_sum_is_close_to_the_zero_curve_pv01(mkt, trades):
    swaps = [t for t in trades if isinstance(t, OISSwap) and t.ccy == "GBP"]
    ladder = R.delta_ladder(swaps, mkt)
    zero_pv01 = sum(P.to_usd(P.sensitivities(t, mkt)["pv01_GBP"], "GBP", mkt) for t in swaps)
    assert abs(ladder["delta_usd_per_bp"].sum() - zero_pv01) < 0.05 * abs(zero_pv01)


def test_change_from_new_trades_matches_the_trades_booked_today(mkt, trades):
    from otc_valuation_desk.market import build_market

    change = R.ladder_change(trades, mkt, build_market(PRIOR))
    new = [t for t in R.book_on(trades, ASOF) if t not in R.book_on(trades, PRIOR)]
    assert {t.trade_id for t in new} == {"NBM-IRS-008", "NBM-IRS-009"}
    assert abs(change["from_new_trades"].sum() - R.delta_ladder(new, mkt)["delta_usd_per_bp"].sum()) < 1e-6
    assert abs((change["change"] - change["from_new_trades"] - change["from_market_and_time"]).abs().max()) < 1e-9


def test_vega_table_covers_every_live_option(mkt, trades):
    assert R.vega_table(trades, mkt)["trades"].sum() == 9
