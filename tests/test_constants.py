"""Tests for bizradar._constants module."""

from bizradar._constants import (
    BASE_URL,
    DISPLAY_MODE,
    DIVIDEND_URL_SEGMENT,
    INDICATOR_URLS,
    PERIOD_ANNUAL,
    PERIOD_QUARTERLY,
    RATING_URL_SEGMENT,
    REPORT_URLS,
    REQUEST_HEADERS,
    REQUEST_TIMEOUT,
)


class TestConstants:
    """Verify constant values and structure."""

    def test_base_url(self):
        assert BASE_URL == "https://www.biznesradar.pl"

    def test_report_urls_keys(self):
        expected = {"income_statement", "balance_sheet", "cash_flow"}
        assert set(REPORT_URLS.keys()) == expected

    def test_indicator_urls_keys(self):
        expected = {"valuation", "profitability", "cash_flow_indicators",
                    "debt", "liquidity", "activity"}
        assert set(INDICATOR_URLS.keys()) == expected

    def test_periods(self):
        assert PERIOD_ANNUAL == "Y"
        assert PERIOD_QUARTERLY == "Q"

    def test_display_mode(self):
        assert DISPLAY_MODE == "0"

    def test_headers_has_user_agent(self):
        assert "User-Agent" in REQUEST_HEADERS

    def test_timeout_positive(self):
        assert REQUEST_TIMEOUT > 0

    def test_dividend_url_segment(self):
        assert DIVIDEND_URL_SEGMENT == "dywidenda"

    def test_rating_url_segment(self):
        assert RATING_URL_SEGMENT == "rating"
