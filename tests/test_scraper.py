"""Tests for scraper functions that fetch and parse data from BiznesRadar."""

import pandas as pd
import pytest
import requests

from bizradar._scraper import (
    _managed_session,
    _parse_report_table,
    adjust_for_splits,
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
    PROFILE_NUMERIC_HTML,
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

    def test_numeric_fields_are_float(self):
        session = MockSession(PROFILE_NUMERIC_HTML)
        profile = fetch_profile("DNP", session=session)
        assert isinstance(profile["Liczba akcji"], float)
        assert isinstance(profile["Kapitalizacja"], float)
        assert isinstance(profile["Enterprise Value"], float)

    def test_numeric_field_values(self):
        session = MockSession(PROFILE_NUMERIC_HTML)
        profile = fetch_profile("DNP", session=session)
        assert profile["Liczba akcji"] == 980_400_000.0
        assert profile["Kapitalizacja"] == 40_392_480_000.0
        assert profile["Enterprise Value"] == 40_675_037_000.0

    def test_text_fields_remain_str(self):
        session = MockSession(PROFILE_NUMERIC_HTML)
        profile = fetch_profile("DNP", session=session)
        assert isinstance(profile["ISIN"], str)
        assert isinstance(profile["Branża"], str)


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


# ---------------------------------------------------------------------------
# adjust_for_splits
# ---------------------------------------------------------------------------

class TestAdjustForSplits:
    """Tests for the adjust_for_splits function."""

    def _make_history(self, dates, opens, highs, lows, closes, volumes=None):
        data = {
            "Otwarcie": opens,
            "Max": highs,
            "Min": lows,
            "Zamknięcie": closes,
        }
        if volumes is not None:
            data["Wolumen"] = [float(v) for v in volumes]
        return pd.DataFrame(data, index=pd.to_datetime(dates))

    def _make_actions(self, dates, divisors):
        return pd.DataFrame({
            "Data": pd.to_datetime(dates),
            "Typ": ["Podział"] * len(dates),
            "Nominalnie": [None] * len(dates),
            "Dzielnik": [float(d) for d in divisors],
        })

    def test_empty_history_returns_empty(self):
        actions = self._make_actions(["2025-07-31"], [10.0])
        result = adjust_for_splits(pd.DataFrame(), actions)
        assert result.empty

    def test_empty_actions_returns_unchanged(self):
        h = self._make_history(["2025-01-01"], [100.0], [110.0], [90.0], [105.0])
        result = adjust_for_splits(h, pd.DataFrame())
        pd.testing.assert_frame_equal(result, h)

    def test_divisor_one_no_change(self):
        h = self._make_history(["2025-01-01"], [100.0], [110.0], [90.0], [105.0])
        actions = self._make_actions(["2025-07-31"], [1.0])
        result = adjust_for_splits(h, actions)
        pd.testing.assert_frame_equal(result, h)

    def test_nan_divisor_skipped(self):
        h = self._make_history(["2025-01-01"], [100.0], [110.0], [90.0], [105.0])
        actions = pd.DataFrame({
            "Data": pd.to_datetime(["2025-07-31"]),
            "Typ": ["Podział"],
            "Nominalnie": [None],
            "Dzielnik": [None],
        })
        result = adjust_for_splits(h, actions)
        pd.testing.assert_frame_equal(result, h)

    def test_prices_before_split_divided(self):
        h = self._make_history(
            ["2025-01-01", "2025-07-31", "2025-08-01"],
            [1000.0, 100.0, 100.0],
            [1100.0, 110.0, 110.0],
            [900.0,  90.0,  90.0],
            [1050.0, 105.0, 105.0],
        )
        result = adjust_for_splits(h, self._make_actions(["2025-07-31"], [10.0]))
        assert result.loc["2025-01-01", "Otwarcie"] == pytest.approx(100.0)
        assert result.loc["2025-01-01", "Max"]      == pytest.approx(110.0)
        assert result.loc["2025-01-01", "Min"]      == pytest.approx(90.0)
        assert result.loc["2025-01-01", "Zamknięcie"] == pytest.approx(105.0)

    def test_split_date_not_adjusted(self):
        h = self._make_history(
            ["2025-01-01", "2025-07-31", "2025-08-01"],
            [1000.0, 100.0, 100.0],
            [1000.0, 100.0, 100.0],
            [1000.0, 100.0, 100.0],
            [1000.0, 100.0, 100.0],
        )
        result = adjust_for_splits(h, self._make_actions(["2025-07-31"], [10.0]))
        assert result.loc["2025-07-31", "Zamknięcie"] == pytest.approx(100.0)
        assert result.loc["2025-08-01", "Zamknięcie"] == pytest.approx(100.0)

    def test_volume_before_split_multiplied(self):
        h = self._make_history(
            ["2025-01-01", "2025-08-01"],
            [1000.0, 100.0], [1000.0, 100.0],
            [1000.0, 100.0], [1000.0, 100.0],
            volumes=[500.0, 5000.0],
        )
        result = adjust_for_splits(h, self._make_actions(["2025-07-31"], [10.0]))
        assert result.loc["2025-01-01", "Wolumen"] == pytest.approx(5000.0)

    def test_volume_after_split_unchanged(self):
        h = self._make_history(
            ["2025-01-01", "2025-08-01"],
            [1000.0, 100.0], [1000.0, 100.0],
            [1000.0, 100.0], [1000.0, 100.0],
            volumes=[500.0, 5000.0],
        )
        result = adjust_for_splits(h, self._make_actions(["2025-07-31"], [10.0]))
        assert result.loc["2025-08-01", "Wolumen"] == pytest.approx(5000.0)

    def test_multiple_splits_cumulative(self):
        """Data before both splits is adjusted by the product of both divisors."""
        h = self._make_history(
            ["2020-01-01", "2022-01-01", "2025-08-01"],
            [1000.0, 500.0, 100.0],
            [1000.0, 500.0, 100.0],
            [1000.0, 500.0, 100.0],
            [1000.0, 500.0, 100.0],
        )
        # Split ×2 in 2021, split ×5 in 2024
        result = adjust_for_splits(h, self._make_actions(["2021-06-01", "2024-06-01"], [2.0, 5.0]))
        assert result.loc["2020-01-01", "Zamknięcie"] == pytest.approx(100.0)   # 1000/2/5
        assert result.loc["2022-01-01", "Zamknięcie"] == pytest.approx(100.0)   # 500/5
        assert result.loc["2025-08-01", "Zamknięcie"] == pytest.approx(100.0)   # unchanged

    def test_does_not_mutate_original(self):
        h = self._make_history(
            ["2025-01-01", "2025-08-01"],
            [1000.0, 100.0], [1000.0, 100.0],
            [1000.0, 100.0], [1000.0, 100.0],
        )
        original_price = h.loc["2025-01-01", "Otwarcie"]
        adjust_for_splits(h, self._make_actions(["2025-07-31"], [10.0]))
        assert h.loc["2025-01-01", "Otwarcie"] == original_price

    def test_missing_volume_column_handled(self):
        h = self._make_history(
            ["2025-01-01", "2025-08-01"],
            [1000.0, 100.0], [1000.0, 100.0],
            [1000.0, 100.0], [1000.0, 100.0],
        )
        result = adjust_for_splits(h, self._make_actions(["2025-07-31"], [10.0]))
        assert result.loc["2025-01-01", "Otwarcie"] == pytest.approx(100.0)
        assert "Wolumen" not in result.columns

    def test_split_before_all_data_has_no_effect(self):
        """If all history is after the split date (split already in the past), nothing is adjusted."""
        h = self._make_history(
            ["2026-01-01", "2026-06-01"],
            [100.0, 100.0], [100.0, 100.0],
            [100.0, 100.0], [100.0, 100.0],
        )
        result = adjust_for_splits(h, self._make_actions(["2020-01-01"], [10.0]))
        pd.testing.assert_frame_equal(result, h)
