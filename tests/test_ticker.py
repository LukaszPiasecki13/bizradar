"""Tests for the Ticker class and its accessor sub-objects."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from bizradar.ticker import Ticker, _CachedAccessor, _Indicators, _MarketData, _Reports

# Patch targets — must patch where the names are looked up (bizradar.ticker module)
_PATCH_REPORT = "bizradar.ticker.fetch_report"
_PATCH_INDICATOR = "bizradar.ticker.fetch_indicator"
_PATCH_RATING = "bizradar.ticker.fetch_rating"
_PATCH_HISTORY = "bizradar.ticker.fetch_history"
_PATCH_DIVIDENDS = "bizradar.ticker.fetch_dividends"
_PATCH_SHAREHOLDERS = "bizradar.ticker.fetch_shareholders"
_PATCH_CORPORATE = "bizradar.ticker.fetch_corporate_actions"
_PATCH_PROFILE = "bizradar.ticker.fetch_profile"
_PATCH_ADJUST = "bizradar.ticker.adjust_for_splits"


# ---------------------------------------------------------------------------
# Ticker initialization
# ---------------------------------------------------------------------------

class TestTickerInit:
    """Tests for Ticker construction."""

    def test_symbol_uppercased(self):
        t = Ticker("dnp")
        assert t.symbol == "DNP"
        t._session.close()

    def test_has_reports_accessor(self):
        t = Ticker("DNP")
        assert isinstance(t.reports, _Reports)
        t._session.close()

    def test_has_indicators_accessor(self):
        t = Ticker("DNP")
        assert isinstance(t.indicators, _Indicators)
        t._session.close()

    def test_has_market_data_accessor(self):
        t = Ticker("DNP")
        assert isinstance(t.market_data, _MarketData)
        t._session.close()

    def test_repr(self):
        t = Ticker("DNP")
        r = repr(t)
        assert "bizradar.Ticker('DNP')" in r
        assert ".reports" in r
        assert ".indicators" in r
        assert ".market_data" in r
        t._session.close()

    def test_cache_starts_empty(self):
        t = Ticker("DNP")
        assert t._cache == {}
        t._session.close()


# ---------------------------------------------------------------------------
# Cache behavior
# ---------------------------------------------------------------------------

class TestCache:
    """Tests for caching mechanism."""

    def test_clear_cache(self):
        t = Ticker("DNP")
        t._cache["test_key"] = "test_value"
        t.clear_cache()
        assert t._cache == {}
        t._session.close()

    @patch(_PATCH_REPORT)
    def test_report_cached_on_second_access(self, mock_fetch):
        mock_fetch.return_value = pd.DataFrame({"2024": [1, 2]})
        t = Ticker("DNP")
        _ = t.reports.income_statement
        _ = t.reports.income_statement
        mock_fetch.assert_called_once()
        t._session.close()

    @patch(_PATCH_INDICATOR)
    def test_indicator_cached(self, mock_fetch):
        mock_fetch.return_value = pd.DataFrame({"2024": [10]})
        t = Ticker("DNP")
        _ = t.indicators.valuation
        _ = t.indicators.valuation
        mock_fetch.assert_called_once()
        t._session.close()

    @patch(_PATCH_ADJUST)
    @patch(_PATCH_CORPORATE)
    @patch(_PATCH_HISTORY)
    def test_history_cached(self, mock_history, mock_actions, mock_adjust):
        mock_history.return_value = pd.DataFrame()
        mock_actions.return_value = pd.DataFrame()
        mock_adjust.return_value = pd.DataFrame()
        t = Ticker("DNP")
        _ = t.market_data.history
        _ = t.market_data.history
        mock_history.assert_called_once()
        t._session.close()

    @patch(_PATCH_REPORT)
    def test_clear_cache_forces_refetch(self, mock_fetch):
        mock_fetch.return_value = pd.DataFrame({"2024": [1]})
        t = Ticker("DNP")
        _ = t.reports.income_statement
        t.clear_cache()
        _ = t.reports.income_statement
        assert mock_fetch.call_count == 2
        t._session.close()


# ---------------------------------------------------------------------------
# _Reports accessor
# ---------------------------------------------------------------------------

class TestReportsAccessor:
    """Tests for the _Reports sub-object."""

    @patch(_PATCH_REPORT)
    def test_income_statement_annual(self, mock_fetch):
        mock_fetch.return_value = pd.DataFrame({"2024": [100]})
        t = Ticker("DNP")
        df = t.reports.income_statement
        mock_fetch.assert_called_once_with("DNP", "income_statement", "Y", session=t._session)
        assert isinstance(df, pd.DataFrame)
        t._session.close()

    @patch(_PATCH_REPORT)
    def test_balance_sheet_annual(self, mock_fetch):
        mock_fetch.return_value = pd.DataFrame()
        t = Ticker("DNP")
        _ = t.reports.balance_sheet
        mock_fetch.assert_called_once_with("DNP", "balance_sheet", "Y", session=t._session)
        t._session.close()

    @patch(_PATCH_REPORT)
    def test_cash_flow_annual(self, mock_fetch):
        mock_fetch.return_value = pd.DataFrame()
        t = Ticker("DNP")
        _ = t.reports.cash_flow
        mock_fetch.assert_called_once_with("DNP", "cash_flow", "Y", session=t._session)
        t._session.close()

    @patch(_PATCH_REPORT)
    def test_quarterly_income_statement(self, mock_fetch):
        mock_fetch.return_value = pd.DataFrame()
        t = Ticker("DNP")
        _ = t.reports.quarterly_income_statement
        mock_fetch.assert_called_once_with("DNP", "income_statement", "Q", session=t._session)
        t._session.close()

    @patch(_PATCH_REPORT)
    def test_quarterly_balance_sheet(self, mock_fetch):
        mock_fetch.return_value = pd.DataFrame()
        t = Ticker("DNP")
        _ = t.reports.quarterly_balance_sheet
        mock_fetch.assert_called_once_with("DNP", "balance_sheet", "Q", session=t._session)
        t._session.close()

    @patch(_PATCH_REPORT)
    def test_quarterly_cash_flow(self, mock_fetch):
        mock_fetch.return_value = pd.DataFrame()
        t = Ticker("DNP")
        _ = t.reports.quarterly_cash_flow
        mock_fetch.assert_called_once_with("DNP", "cash_flow", "Q", session=t._session)
        t._session.close()

    def test_unknown_attribute_raises(self):
        t = Ticker("DNP")
        with pytest.raises(AttributeError):
            _ = t.reports.nonexistent
        t._session.close()

    def test_repr(self):
        t = Ticker("DNP")
        r = repr(t.reports)
        assert "income_statement" in r
        assert "balance_sheet" in r
        t._session.close()

    def test_repr_html(self):
        t = Ticker("DNP")
        html = t.reports._repr_html_()
        assert "<table>" in html
        assert "income_statement" in html
        t._session.close()


# ---------------------------------------------------------------------------
# _Indicators accessor
# ---------------------------------------------------------------------------

class TestIndicatorsAccessor:
    """Tests for the _Indicators sub-object."""

    @patch(_PATCH_INDICATOR)
    def test_valuation(self, mock_fetch):
        mock_fetch.return_value = pd.DataFrame()
        t = Ticker("DNP")
        _ = t.indicators.valuation
        mock_fetch.assert_called_once_with("DNP", "valuation", session=t._session)
        t._session.close()

    @patch(_PATCH_INDICATOR)
    def test_profitability(self, mock_fetch):
        mock_fetch.return_value = pd.DataFrame()
        t = Ticker("DNP")
        _ = t.indicators.profitability
        mock_fetch.assert_called_once_with("DNP", "profitability", session=t._session)
        t._session.close()

    @patch(_PATCH_INDICATOR)
    def test_debt(self, mock_fetch):
        mock_fetch.return_value = pd.DataFrame()
        t = Ticker("DNP")
        _ = t.indicators.debt
        mock_fetch.assert_called_once()
        t._session.close()

    @patch(_PATCH_INDICATOR)
    def test_liquidity(self, mock_fetch):
        mock_fetch.return_value = pd.DataFrame()
        t = Ticker("DNP")
        _ = t.indicators.liquidity
        mock_fetch.assert_called_once()
        t._session.close()

    @patch(_PATCH_INDICATOR)
    def test_activity(self, mock_fetch):
        mock_fetch.return_value = pd.DataFrame()
        t = Ticker("DNP")
        _ = t.indicators.activity
        mock_fetch.assert_called_once()
        t._session.close()

    @patch(_PATCH_INDICATOR)
    def test_cash_flow_indicators(self, mock_fetch):
        mock_fetch.return_value = pd.DataFrame()
        t = Ticker("DNP")
        _ = t.indicators.cash_flow_indicators
        mock_fetch.assert_called_once()
        t._session.close()

    @patch(_PATCH_RATING)
    def test_rating(self, mock_fetch):
        mock_fetch.return_value = {"altman_score": 5.0}
        t = Ticker("DNP")
        result = t.indicators.rating
        mock_fetch.assert_called_once_with("DNP", session=t._session)
        assert result["altman_score"] == 5.0
        t._session.close()

    def test_unknown_attribute_raises(self):
        t = Ticker("DNP")
        with pytest.raises(AttributeError):
            _ = t.indicators.nonexistent
        t._session.close()


# ---------------------------------------------------------------------------
# _MarketData accessor
# ---------------------------------------------------------------------------

class TestMarketDataAccessor:
    """Tests for the _MarketData sub-object."""

    @patch(_PATCH_ADJUST)
    @patch(_PATCH_CORPORATE)
    @patch(_PATCH_HISTORY)
    def test_history(self, mock_history, mock_actions, mock_adjust):
        raw = pd.DataFrame({"Zamknięcie": [100.0]})
        actions_df = pd.DataFrame()
        adjusted = pd.DataFrame({"Zamknięcie": [10.0]})
        mock_history.return_value = raw
        mock_actions.return_value = actions_df
        mock_adjust.return_value = adjusted
        t = Ticker("DNP")
        result = t.market_data.history
        mock_history.assert_called_once_with("DNP", session=t._session)
        mock_actions.assert_called_once_with("DNP", session=t._session)
        mock_adjust.assert_called_once_with(raw, actions_df)
        pd.testing.assert_frame_equal(result, adjusted)
        t._session.close()

    def test_dividends(self):
        mock_fn = MagicMock(return_value=pd.DataFrame())
        t = Ticker("DNP")
        with patch.dict(_MarketData._FETCH_MAP, {"dividends": mock_fn}):
            _ = t.market_data.dividends
        mock_fn.assert_called_once_with("DNP", session=t._session)
        t._session.close()

    def test_shareholders(self):
        mock_fn = MagicMock(return_value=pd.DataFrame())
        t = Ticker("DNP")
        with patch.dict(_MarketData._FETCH_MAP, {"shareholders": mock_fn}):
            _ = t.market_data.shareholders
        mock_fn.assert_called_once_with("DNP", session=t._session)
        t._session.close()

    def test_corporate_actions(self):
        mock_fn = MagicMock(return_value=pd.DataFrame())
        t = Ticker("DNP")
        with patch.dict(_MarketData._FETCH_MAP, {"corporate_actions": mock_fn}):
            _ = t.market_data.corporate_actions
        mock_fn.assert_called_once_with("DNP", session=t._session)
        t._session.close()

    def test_profile(self):
        mock_fn = MagicMock(return_value={"Nazwa": "Test"})
        t = Ticker("DNP")
        with patch.dict(_MarketData._FETCH_MAP, {"profile": mock_fn}):
            result = t.market_data.profile
        mock_fn.assert_called_once_with("DNP", session=t._session)
        assert result["Nazwa"] == "Test"
        t._session.close()

    def test_unknown_attribute_raises(self):
        t = Ticker("DNP")
        with pytest.raises(AttributeError):
            _ = t.market_data.nonexistent
        t._session.close()


class TestHistorySplitAdjustment:
    """Tests for the split-adjustment integration in _MarketData.history."""

    @patch(_PATCH_ADJUST)
    @patch(_PATCH_CORPORATE)
    @patch(_PATCH_HISTORY)
    def test_corporate_actions_fetched_alongside_history(self, mock_history, mock_actions, mock_adjust):
        """Accessing history also fetches corporate_actions for split data."""
        mock_history.return_value = pd.DataFrame()
        mock_actions.return_value = pd.DataFrame()
        mock_adjust.return_value = pd.DataFrame()
        t = Ticker("DNP")
        _ = t.market_data.history
        mock_actions.assert_called_once_with("DNP", session=t._session)
        t._session.close()

    @patch(_PATCH_ADJUST)
    @patch(_PATCH_CORPORATE)
    @patch(_PATCH_HISTORY)
    def test_history_reuses_cached_corporate_actions(self, mock_history, mock_actions, mock_adjust):
        """If corporate_actions was already cached, history should not re-fetch it."""
        mock_history.return_value = pd.DataFrame()
        mock_actions.return_value = pd.DataFrame()
        mock_adjust.return_value = pd.DataFrame()
        t = Ticker("DNP")
        _ = t.market_data.corporate_actions  # warm the cache
        mock_actions.reset_mock()
        _ = t.market_data.history            # should NOT call fetch_corporate_actions again
        mock_actions.assert_not_called()
        t._session.close()

    @patch(_PATCH_ADJUST)
    @patch(_PATCH_CORPORATE)
    @patch(_PATCH_HISTORY)
    def test_corporate_actions_cached_after_history_access(self, mock_history, mock_actions, mock_adjust):
        """Accessing history should populate the corporate_actions cache."""
        mock_history.return_value = pd.DataFrame()
        mock_actions.return_value = pd.DataFrame()
        mock_adjust.return_value = pd.DataFrame()
        t = Ticker("DNP")
        _ = t.market_data.history        # fetches both; caches corporate_actions
        mock_actions.reset_mock()
        _ = t.market_data.corporate_actions  # should come from cache
        mock_actions.assert_not_called()
        t._session.close()

    @patch(_PATCH_ADJUST)
    @patch(_PATCH_CORPORATE)
    @patch(_PATCH_HISTORY)
    def test_adjust_for_splits_receives_correct_args(self, mock_history, mock_actions, mock_adjust):
        raw = pd.DataFrame({"Zamknięcie": [500.0, 100.0]})
        actions_df = pd.DataFrame({"Data": pd.to_datetime(["2025-07-31"]), "Dzielnik": [10.0]})
        mock_history.return_value = raw
        mock_actions.return_value = actions_df
        mock_adjust.return_value = raw.copy()
        t = Ticker("DNP")
        _ = t.market_data.history
        args, _ = mock_adjust.call_args
        pd.testing.assert_frame_equal(args[0], raw)
        pd.testing.assert_frame_equal(args[1], actions_df)
        t._session.close()


# ---------------------------------------------------------------------------
# _CachedAccessor base
# ---------------------------------------------------------------------------

class TestCachedAccessor:
    """Tests for the base accessor class."""

    def test_dir_includes_props(self):
        t = Ticker("DNP")
        d = dir(t.reports)
        assert "income_statement" in d
        assert "balance_sheet" in d
        t._session.close()
