"""Tests for internal helper functions in bizradar._scraper."""

import pytest
from bs4 import BeautifulSoup

from bizradar._scraper import (
    _build_indicator_url,
    _build_url,
    _parse_period,
    _parse_value,
    _text_to_number,
)
from bizradar._constants import BASE_URL, DISPLAY_MODE


# ---------------------------------------------------------------------------
# _text_to_number
# ---------------------------------------------------------------------------

class TestTextToNumber:
    """Tests for _text_to_number helper."""

    def test_plain_integer(self):
        assert _text_to_number("123") == 123.0

    def test_space_separated_thousands(self):
        assert _text_to_number("2 589 576") == 2589576.0

    def test_nbsp_thousands(self):
        assert _text_to_number("1\xa0200\xa0300") == 1200300.0

    def test_comma_decimal(self):
        assert _text_to_number("16,13") == 16.13

    def test_percentage(self):
        assert _text_to_number("16,13%") == 16.13

    def test_negative(self):
        assert _text_to_number("-50 000") == -50000.0

    def test_dash_returns_none(self):
        assert _text_to_number("-") is None

    def test_empty_string_returns_none(self):
        assert _text_to_number("") is None

    def test_non_numeric_returns_none(self):
        assert _text_to_number("abc") is None

    def test_zero(self):
        assert _text_to_number("0") == 0.0

    def test_decimal_only(self):
        assert _text_to_number("0,55") == 0.55

    def test_large_number(self):
        assert _text_to_number("12 345 678 901") == 12345678901.0


# ---------------------------------------------------------------------------
# _parse_period
# ---------------------------------------------------------------------------

class TestParsePeriod:
    """Tests for _parse_period helper."""

    def test_annual(self):
        assert _parse_period("2024(gru 24)") == "2024"

    def test_quarterly(self):
        assert _parse_period("2025/Q3(wrz 25)") == "2025/Q3"

    def test_ttm_o4k(self):
        assert _parse_period("O4K(wrz 25)*") == "TTM"

    def test_ttm_o4q(self):
        assert _parse_period("O4Q(wrz 25)") == "TTM"

    def test_plain_year(self):
        assert _parse_period("2023") == "2023"

    def test_whitespace_stripped(self):
        assert _parse_period("  2022(gru 22)  ") == "2022"

    def test_unknown_format_returns_text(self):
        assert _parse_period("Something weird") == "Something weird"


# ---------------------------------------------------------------------------
# _parse_value
# ---------------------------------------------------------------------------

class TestParseValue:
    """Tests for _parse_value helper."""

    def test_normal_value(self):
        html = '<td class="h"><span class="value"><span class="pv"><span>2 589 576</span></span></span></td>'
        cell = BeautifulSoup(html, "html.parser").find("td")
        assert _parse_value(cell) == 2589576.0

    def test_negative_value(self):
        html = '<td class="h"><span class="value"><span class="pv"><span>-50 000</span></span></span></td>'
        cell = BeautifulSoup(html, "html.parser").find("td")
        assert _parse_value(cell) == -50000.0

    def test_percentage_value(self):
        html = '<td class="h"><span class="value"><span class="pv"><span>16,13%</span></span></span></td>'
        cell = BeautifulSoup(html, "html.parser").find("td")
        assert _parse_value(cell) == 16.13

    def test_no_value_span_returns_none(self):
        html = '<td class="h">some text</td>'
        cell = BeautifulSoup(html, "html.parser").find("td")
        assert _parse_value(cell) is None

    def test_no_pv_span_returns_none(self):
        html = '<td class="h"><span class="value"><span>123</span></span></td>'
        cell = BeautifulSoup(html, "html.parser").find("td")
        assert _parse_value(cell) is None

    def test_premium_locked_no_digits(self):
        html = '<td class="h"><span class="value"><span class="premium-value">Dane premium</span></span></td>'
        cell = BeautifulSoup(html, "html.parser").find("td")
        assert _parse_value(cell) is None

    def test_dash_value(self):
        html = '<td class="h"><span class="value"><span class="pv"><span>-</span></span></span></td>'
        cell = BeautifulSoup(html, "html.parser").find("td")
        assert _parse_value(cell) is None


# ---------------------------------------------------------------------------
# _build_url / _build_indicator_url
# ---------------------------------------------------------------------------

class TestBuildUrl:
    """Tests for URL builder helpers."""

    def test_build_url_income_statement(self):
        url = _build_url("income_statement", "DNP", "Y")
        assert url == f"{BASE_URL}/raporty-finansowe-rachunek-zyskow-i-strat/DNP,Y,{DISPLAY_MODE}"

    def test_build_url_balance_sheet(self):
        url = _build_url("balance_sheet", "CDR", "Q")
        assert url == f"{BASE_URL}/raporty-finansowe-bilans/CDR,Q,{DISPLAY_MODE}"

    def test_build_url_cash_flow(self):
        url = _build_url("cash_flow", "PKN", "Y")
        assert url == f"{BASE_URL}/raporty-finansowe-przeplywy-pieniezne/PKN,Y,{DISPLAY_MODE}"

    def test_build_indicator_url_valuation(self):
        url = _build_indicator_url("valuation", "DNP")
        assert url == f"{BASE_URL}/wskazniki-wartosci-rynkowej/DNP"

    def test_build_indicator_url_profitability(self):
        url = _build_indicator_url("profitability", "CDR")
        assert url == f"{BASE_URL}/wskazniki-rentownosci/CDR"
