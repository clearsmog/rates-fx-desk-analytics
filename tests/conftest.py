from datetime import date
from pathlib import Path

import pytest

from rates_fx_desk_analytics.market import build_market
from rates_fx_desk_analytics.trades import load_portfolio

ASOF, PRIOR = date(2026, 10, 15), date(2026, 10, 14)
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def mkt():
    return build_market(ASOF)


@pytest.fixture(scope="session")
def trades():
    return load_portfolio(ROOT / "data" / "trades" / "client_portfolio.csv")
