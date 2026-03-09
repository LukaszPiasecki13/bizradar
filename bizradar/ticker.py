"""Ticker class - main public interface for BiznesRadar data."""

from __future__ import annotations

import pandas as pd
import requests

from bizradar._constants import PERIOD_ANNUAL, PERIOD_QUARTERLY
from bizradar._scraper import (
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


class _CachedAccessor:
    """Base for lazy-loaded, cached sub-objects on Ticker."""

    _PROPS: dict[str, str] = {}  # property_name -> description

    def __init__(self, ticker: Ticker) -> None:
        self._t = ticker

    def _cached(self, key: str, fetcher):
        if key not in self._t._cache:
            self._t._cache[key] = fetcher()
        return self._t._cache[key]

    def __dir__(self):
        return list(super().__dir__()) + list(self._PROPS.keys())

    def __repr__(self) -> str:
        props = ", ".join(self._PROPS)
        return f"[{props}]"

    def _repr_html_(self) -> str:
        rows = "".join(
            f"<tr><td><b>{name}</b></td><td>{desc}</td></tr>"
            for name, desc in self._PROPS.items()
        )
        return f"<table>{rows}</table>"


class _Reports(_CachedAccessor):
    """Financial reports (lazy-loaded)."""

    _PROPS = {
        "income_statement": "Income statement (annual)",
        "balance_sheet": "Balance sheet (annual)",
        "cash_flow": "Cash flow statement (annual)",
        "quarterly_income_statement": "Income statement (quarterly)",
        "quarterly_balance_sheet": "Balance sheet (quarterly)",
        "quarterly_cash_flow": "Cash flow statement (quarterly)",
    }

    _REPORT_MAP = {
        "income_statement":           ("income_statement", PERIOD_ANNUAL),
        "balance_sheet":              ("balance_sheet",    PERIOD_ANNUAL),
        "cash_flow":                  ("cash_flow",        PERIOD_ANNUAL),
        "quarterly_income_statement": ("income_statement", PERIOD_QUARTERLY),
        "quarterly_balance_sheet":    ("balance_sheet",    PERIOD_QUARTERLY),
        "quarterly_cash_flow":        ("cash_flow",        PERIOD_QUARTERLY),
    }

    def __getattr__(self, name):
        if name in self._REPORT_MAP:
            report_type, period = self._REPORT_MAP[name]
            return self._cached(name, lambda: fetch_report(
                self._t.symbol, report_type, period, session=self._t._session))
        raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")


class _Indicators(_CachedAccessor):
    """Financial indicators (lazy-loaded)."""

    _PROPS = {
        "valuation": "Valuation ratios (P/E, P/BV, EV/EBIT …)",
        "profitability": "Profitability ratios (ROE, ROA, margins)",
        "cash_flow_indicators": "Cash flow indicators",
        "debt": "Debt ratios",
        "liquidity": "Liquidity ratios",
        "activity": "Activity ratios (cycles, turnover)",
        "rating": "Altman EM-Score & Piotroski F-Score (dict)",
    }

    _INDICATOR_NAMES = {"valuation", "profitability", "cash_flow_indicators", "debt", "liquidity", "activity"}

    def __getattr__(self, name):
        if name in self._INDICATOR_NAMES:
            return self._cached(f"ind_{name}", lambda: fetch_indicator(
                self._t.symbol, name, session=self._t._session))
        if name == "rating":
            return self._cached("rating", lambda: fetch_rating(
                self._t.symbol, session=self._t._session))
        raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")


class _MarketData(_CachedAccessor):
    """Market data (lazy-loaded)."""

    _PROPS = {
        "history": "Historical OHLCV data",
        "dividends": "Dividend history",
        "shareholders": "Shareholder structure",
        "corporate_actions": "Corporate actions (splits, etc.)",
        "profile": "Company profile (dict)",
    }

    _FETCH_MAP = {
        "dividends": fetch_dividends,
        "shareholders": fetch_shareholders,
        "corporate_actions": fetch_corporate_actions,
        "profile": fetch_profile,
    }

    def __getattr__(self, name):
        if name == "history":
            return self._cached("history", self._fetch_adjusted_history)
        if name in self._FETCH_MAP:
            return self._cached(name, lambda: self._FETCH_MAP[name](
                self._t.symbol, session=self._t._session))
        raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")

    def _fetch_adjusted_history(self) -> pd.DataFrame:
        raw = fetch_history(self._t.symbol, session=self._t._session)
        actions = self._cached("corporate_actions", lambda: fetch_corporate_actions(
            self._t.symbol, session=self._t._session))
        return adjust_for_splits(raw, actions)


class Ticker:
    """Interface for fetching financial data of a single company from BiznesRadar.pl.

    Usage:
        t = Ticker("DNP")

        t.reports.income_statement          # Annual income statement
        t.reports.quarterly_balance_sheet   # Quarterly balance sheet
        t.indicators.valuation              # P/E, P/BV, EV/EBIT …
        t.indicators.debt                   # Debt ratios
        t.indicators.rating                 # Altman EM-Score & Piotroski F-Score
        t.market_data.history               # Historical OHLCV
        t.market_data.dividends             # Dividend history
        t.market_data.profile               # Company profile (dict)

    All properties are lazy-loaded and cached.
    """

    def __init__(self, symbol: str) -> None:
        self.symbol = symbol.upper()
        self._session = requests.Session()
        self._cache: dict[str, object] = {}

        self.reports = _Reports(self)
        self.indicators = _Indicators(self)
        self.market_data = _MarketData(self)

    def clear_cache(self) -> None:
        """Clear all cached data, forcing fresh fetches."""
        self._cache.clear()

    def __repr__(self) -> str:
        return (
            f"bizradar.Ticker('{self.symbol}')\n"
            f"  .reports      {self.reports}\n"
            f"  .indicators   {self.indicators}\n"
            f"  .market_data  {self.market_data}"
        )

    def __del__(self) -> None:
        self._session.close()
