from datetime import date

from rates_fx_desk_analytics import replay as RP


def test_valuation_dates_skip_holidays():
    days = RP.valuation_dates(date(2026, 8, 28), date(2026, 9, 8))
    assert date(2026, 8, 31) not in days  # UK bank holiday: no Bank of England curve
    assert date(2026, 9, 7) not in days  # US Labor Day: no Treasury curve


def test_measured_causes_close_the_flagged_amounts():
    # 22 and 23 Sep 2026: the largest moves in the window (GBP 5y +15bp, USD +16bp, GBP/USD -0.7%)
    daily, flagged, notes = RP.run(date(2026, 9, 21), date(2026, 9, 23))
    assert len(daily) == 2 and not notes
    assert len(flagged) >= 10
    assert flagged["remaining"].abs().max() < 250  # FX options: third-order rates-spot terms
    assert (daily["predicted_from_risk"] + daily["unexplained"] - daily["revalued"]).abs().max() < 1e-6
