"""Tests for scraper functions that fetch and parse data from BiznesRadar."""

import pandas as pd
import pytest
import requests

from bizradar._scraper import (
    _managed_session,
    _parse_report_table,
    fetch_corporate_actions,
    fetch_dividends,
    fetch_history,
    fetch_indicator,
    fetch_profile,
    fetch_rating,
    fetch_report,
    fetch_shareholders,
)

from .conftest import (
    CORPORATE_ACTIONS_EMPTY_HTML,
    CORPORATE_ACTIONS_HTML,
    DIVIDEND_EMPTY_HTML,
    DIVIDEND_HTML,
    HISTORY_EMPTY_HTML,
    HISTORY_HTML,
    HISTORY_PAGE2_HTML,
    INCOME_STATEMENT_HTML,
    INCOME_STATEMENT_MLD_HTML,
    INCOME_STATEMENT_MLN_HTML,
    INCOME_STATEMENT_NO_UNIT_HTML,
    INCOME_STATEMENT_TYS_HTML,
    MockSession,
    PROFILE_HTML,
    RATING_HTML,
    REPORT_EMPTY_ROWS_HTML,
    REPORT_NO_TABLE_HTML,
    SHAREHOLDERS_HTML,
)


# ---------------------------------------------------------------------------
# _managed_session
# ---------------------------------------------------------------------------

class TestManagedSession:
    """Tests for session context manager."""

    def test_uses_provided_session(self):
        s = requests.Session()
        with _managed_session(s) as result:
            assert result is s
        s.close()

    def test_creates_new_session_when_none(self):
        with _managed_session(None) as s:
            assert isinstance(s, requests.Session)


# ---------------------------------------------------------------------------
# _parse_report_table
# ---------------------------------------------------------------------------

class TestParseReportTable:
    """Tests for the main report table parser."""

    def test_no_table_raises(self):
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(REPORT_NO_TABLE_HTML, "html.parser")
        with pytest.raises(ValueError, match="Could not find report table"):
            _parse_report_table(soup)

    def test_insufficient_rows_raises(self):
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(REPORT_EMPTY_ROWS_HTML, "html.parser")
        with pytest.raises(ValueError, match="insufficient rows"):
            _parse_report_table(soup)

    def test_parses_periods_correctly(self):
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(INCOME_STATEMENT_HTML, "html.parser")
        df = _parse_report_table(soup)
        assert list(df.columns) == ["2024", "2023", "2022", "TTM"]

    def test_parses_rows_correctly(self):
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(INCOME_STATEMENT_HTML, "html.parser")
        df = _parse_report_table(soup)
        assert "Przychody ze sprzedaży" in df.index
        assert "Zysk netto" in df.index

    def test_skips_data_publikacji_row(self):
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(INCOME_STATEMENT_HTML, "html.parser")
        df = _parse_report_table(soup)
        assert "Data publikacji" not in df.index

    def test_values_parsed_numerically(self):
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(INCOME_STATEMENT_HTML, "html.parser")
        df = _parse_report_table(soup)
        assert df.loc["Przychody ze sprzedaży", "2024"] == 2589576.0
        assert df.loc["Zysk netto", "2022"] == -50000.0

    def test_percentage_values(self):
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(INCOME_STATEMENT_HTML, "html.parser")
        df = _parse_report_table(soup)
        assert df.loc["Marża zysku brutto", "2024"] == 16.13

    def test_dash_becomes_none(self):
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(INCOME_STATEMENT_HTML, "html.parser")
        df = _parse_report_table(soup)
        assert pd.isna(df.loc["Marża zysku brutto", "2022"])


# ---------------------------------------------------------------------------
# fetch_report
# ---------------------------------------------------------------------------

class TestFetchReport:
    """Tests for fetch_report."""

    def test_invalid_report_type_raises(self):
        with pytest.raises(ValueError, match="Unknown report_type"):
            fetch_report("DNP", "nonexistent")

    def test_returns_dataframe(self):
        session = MockSession(INCOME_STATEMENT_HTML)
        df = fetch_report("DNP", "income_statement", session=session)
        assert isinstance(df, pd.DataFrame)
        assert not df.empty

    def test_annual_period_default(self):
        session = MockSession(INCOME_STATEMENT_HTML)
        df = fetch_report("DNP", "income_statement", session=session)
        assert "2024" in df.columns

    def test_quarterly_period(self):
        session = MockSession(INCOME_STATEMENT_HTML)
        df = fetch_report("DNP", "income_statement", period="Q", session=session)
        assert isinstance(df, pd.DataFrame)

    def test_tys_unit_applied(self):
        """Values from a 'dane w tys. PLN' page must be multiplied by 1000."""
        session = MockSession(INCOME_STATEMENT_TYS_HTML)
        df = fetch_report("DNP", "income_statement", session=session)
        # Raw HTML value = 2000, expected after ×1000
        assert df.loc["Przychody ze sprzedaży", "2024"] == 2_000_000.0
        assert df.loc["Przychody ze sprzedaży", "2023"] == 1_000_000.0

    def test_mln_unit_applied(self):
        """Values from a 'dane w mln. PLN' page must be multiplied by 1_000_000."""
        session = MockSession(INCOME_STATEMENT_MLN_HTML)
        df = fetch_report("DNP", "income_statement", session=session)
        assert df.loc["Przychody ze sprzedaży", "2024"] == 5_000_000.0

    def test_mld_unit_applied(self):
        """Values from a 'dane w mld. PLN' page must be multiplied by 1_000_000_000."""
        session = MockSession(INCOME_STATEMENT_MLD_HTML)
        df = fetch_report("DNP", "income_statement", session=session)
        assert df.loc["Przychody ze sprzedaży", "2024"] == 3_000_000_000.0

    def test_no_unit_disclaimer_no_multiplication(self):
        """Without a disclaimer the values should be returned as-is."""
        session = MockSession(INCOME_STATEMENT_NO_UNIT_HTML)
        df = fetch_report("DNP", "income_statement", session=session)
        assert df.loc["Wskaźnik", "2024"] == 42.0


# ---------------------------------------------------------------------------
# fetch_indicator
# ---------------------------------------------------------------------------

class TestFetchIndicator:
    """Tests for fetch_indicator."""

    def test_invalid_indicator_type_raises(self):
        with pytest.raises(ValueError, match="Unknown indicator_type"):
            fetch_indicator("DNP", "nonexistent")

    def test_returns_dataframe(self):
        session = MockSession(INCOME_STATEMENT_HTML)
        df = fetch_indicator("DNP", "valuation", session=session)
        assert isinstance(df, pd.DataFrame)


# ---------------------------------------------------------------------------
# fetch_history
# ---------------------------------------------------------------------------

class TestFetchHistory:
    """Tests for fetch_history."""

    def test_returns_dataframe_with_ohlcv(self):
        session = MockSession(HISTORY_HTML)
        df = fetch_history("DNP", session=session)
        assert isinstance(df, pd.DataFrame)
        assert "Zamknięcie" in df.columns
        assert "Wolumen" in df.columns
        assert len(df) == 2

    def test_values_parsed(self):
        session = MockSession(HISTORY_HTML)
        df = fetch_history("DNP", session=session)
        row = df.iloc[-1]  # latest date
        assert row["Zamknięcie"] == 136.80
        assert row["Wolumen"] == 12500.0

    def test_date_index(self):
        session = MockSession(HISTORY_HTML)
        df = fetch_history("DNP", session=session)
        assert df.index.name == "Data"
        assert pd.api.types.is_datetime64_any_dtype(df.index)

    def test_sorted_ascending(self):
        session = MockSession(HISTORY_HTML)
        df = fetch_history("DNP", session=session)
        assert df.index[0] < df.index[-1]

    def test_empty_page_returns_empty_df(self):
        session = MockSession(HISTORY_EMPTY_HTML)
        df = fetch_history("DNP", session=session)
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    def test_pagination(self):
        """Test that pagination fetches multiple pages."""
        page_map = {
            "notowania-historyczne/DNP,2": HISTORY_HTML,  # page 2
            "notowania-historyczne/DNP": HISTORY_PAGE2_HTML,  # page 1 (shows 2 pages)
        }
        session = MockSession(page_map)
        df = fetch_history("DNP", session=session)
        assert len(df) == 3  # 1 from page1 + 2 from page2


# ---------------------------------------------------------------------------
# fetch_shareholders
# ---------------------------------------------------------------------------

class TestFetchShareholders:
    """Tests for fetch_shareholders."""

    def test_returns_dataframe(self):
        session = MockSession(SHAREHOLDERS_HTML)
        df = fetch_shareholders("DNP", session=session)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1  # "Razem" should be excluded

    def test_razem_excluded(self):
        session = MockSession(SHAREHOLDERS_HTML)
        df = fetch_shareholders("DNP", session=session)
        names = df["Akcjonariusz"].tolist()
        assert "Razem" not in names

    def test_columns_present(self):
        session = MockSession(SHAREHOLDERS_HTML)
        df = fetch_shareholders("DNP", session=session)
        expected_cols = {"Akcjonariusz", "Udział (%)", "Liczba akcji"}
        assert expected_cols.issubset(set(df.columns))

    def test_numeric_values(self):
        session = MockSession(SHAREHOLDERS_HTML)
        df = fetch_shareholders("DNP", session=session)
        row = df.iloc[0]
        assert row["Udział (%)"] == 25.50
        assert row["Liczba akcji"] == 10000000.0


# ---------------------------------------------------------------------------
# fetch_corporate_actions
# ---------------------------------------------------------------------------

class TestFetchCorporateActions:
    """Tests for fetch_corporate_actions."""

    def test_returns_dataframe(self):
        session = MockSession(CORPORATE_ACTIONS_HTML)
        df = fetch_corporate_actions("DNP", session=session)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2

    def test_columns_present(self):
        session = MockSession(CORPORATE_ACTIONS_HTML)
        df = fetch_corporate_actions("DNP", session=session)
        assert "Typ" in df.columns
        assert "Dzielnik" in df.columns

    def test_dates_are_datetime(self):
        session = MockSession(CORPORATE_ACTIONS_HTML)
        df = fetch_corporate_actions("DNP", session=session)
        assert pd.api.types.is_datetime64_any_dtype(df["Data"])

    def test_sorted_by_date(self):
        session = MockSession(CORPORATE_ACTIONS_HTML)
        df = fetch_corporate_actions("DNP", session=session)
        assert df["Data"].iloc[0] < df["Data"].iloc[1]

    def test_empty_returns_empty_df(self):
        session = MockSession(CORPORATE_ACTIONS_EMPTY_HTML)
        df = fetch_corporate_actions("DNP", session=session)
        assert df.empty


# ---------------------------------------------------------------------------
# fetch_profile
# ---------------------------------------------------------------------------

class TestFetchProfile:
    """Tests for fetch_profile."""

    def test_returns_dict(self):
        session = MockSession(PROFILE_HTML)
        profile = fetch_profile("DNP", session=session)
        assert isinstance(profile, dict)

    def test_profile_content(self):
        session = MockSession(PROFILE_HTML)
        profile = fetch_profile("DNP", session=session)
        assert profile["Nazwa"] == "Dino Polska S.A."
        assert profile["ISIN"] == "PLDINPL00011"
        assert profile["Sektor"] == "Handel detaliczny"


# ---------------------------------------------------------------------------
# fetch_dividends
# ---------------------------------------------------------------------------

class TestFetchDividends:
    """Tests for fetch_dividends."""

    def test_returns_dataframe(self):
        session = MockSession(DIVIDEND_HTML)
        df = fetch_dividends("DNP", session=session)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2

    def test_columns_present(self):
        session = MockSession(DIVIDEND_HTML)
        df = fetch_dividends("DNP", session=session)
        assert "Year" in df.columns
        assert "DPS_PLN" in df.columns
        assert "Payment_Date" in df.columns

    def test_values(self):
        session = MockSession(DIVIDEND_HTML)
        df = fetch_dividends("DNP", session=session)
        row_2024 = df[df["Year"] == 2024].iloc[0]
        assert row_2024["DPS_PLN"] == 5.30
        assert row_2024["Status"] == "Wypłacona"

    def test_total_value_converted_to_pln(self):
        """Total_Value_PLN and From_Reserve_PLN must be raw HTML value ×1000."""
        session = MockSession(DIVIDEND_HTML)
        df = fetch_dividends("DNP", session=session)
        row_2024 = df[df["Year"] == 2024].iloc[0]
        # Raw HTML value = 207 843 (tys. zł) → expected 207 843 000 PLN
        assert row_2024["Total_Value_PLN"] == 207_843_000.0

    def test_columns_in_pln(self):
        """Ensure old kPLN column names are gone and PLN names are present."""
        session = MockSession(DIVIDEND_HTML)
        df = fetch_dividends("DNP", session=session)
        assert "Total_Value_PLN" in df.columns
        assert "From_Reserve_PLN" in df.columns
        assert "Total_Value_kPLN" not in df.columns
        assert "From_Reserve_kPLN" not in df.columns

    def test_sorted_descending_by_year(self):
        session = MockSession(DIVIDEND_HTML)
        df = fetch_dividends("DNP", session=session)
        assert df["Year"].iloc[0] > df["Year"].iloc[-1]

    def test_empty_returns_empty_df(self):
        session = MockSession(DIVIDEND_EMPTY_HTML)
        df = fetch_dividends("DNP", session=session)
        assert df.empty


# ---------------------------------------------------------------------------
# fetch_rating
# ---------------------------------------------------------------------------

class TestFetchRating:
    """Tests for fetch_rating."""

    def test_returns_dict(self):
        session = MockSession(RATING_HTML)
        result = fetch_rating("DNP", session=session)
        assert isinstance(result, dict)

    def test_altman_score(self):
        session = MockSession(RATING_HTML)
        result = fetch_rating("DNP", session=session)
        assert result["altman_score"] == 5.85
        assert result["altman_rating"] == "BB+"

    def test_altman_details(self):
        session = MockSession(RATING_HTML)
        result = fetch_rating("DNP", session=session)
        details = result["altman_details"]
        assert isinstance(details, pd.DataFrame)
        assert len(details) == 2

    def test_piotroski_score(self):
        session = MockSession(RATING_HTML)
        result = fetch_rating("DNP", session=session)
        assert result["piotroski_score"] == 7

    def test_piotroski_details(self):
        session = MockSession(RATING_HTML)
        result = fetch_rating("DNP", session=session)
        details = result["piotroski_details"]
        assert isinstance(details, pd.DataFrame)
        assert len(details) == 2
