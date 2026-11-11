from otc_valuation_desk import fixings as F


def test_compounding_agrees_with_the_published_indices(mkt, trades):
    df = F.check(trades, mkt)
    assert len(df) == 14
    assert (df["check"] == "OK").all()
    assert df["diff_bp"].abs().max() < F.INDEX_TOL_BP


def test_settled_coupon_amounts(mkt, trades):
    df = F.check(trades, mkt)
    r = df[(df["trade_id"] == "NBM-IRS-001") & (df["status"] == "last settled")].iloc[0]
    # pay 4.10% fixed on GBP 50m for the year to 17 Mar 2026, receive compounded SONIA
    assert abs(r["fixed_or_spread_amount"] + 50_000_000 * 0.041) < 1e-6
    assert abs(r["net_amount"] - (r["floating_amount"] - 2_050_000)) < 1e-6
    assert r["net_amount"] > 0  # compounded SONIA of 4.12% is above the 4.10% fixed rate
    upcoming = df[df["status"] == "pays within horizon"]
    assert set(upcoming["trade_id"]) == {"NBM-XCY-002"}
