"""bizradar - Python library for scraping financial data from BiznesRadar.pl

Usage:
    import bizradar as br

    t = br.Ticker("DNP")
    t.reports.income_statement
    t.indicators.valuation
    t.market_data.history
"""

from bizradar.ticker import Ticker

__version__ = "0.2.0"
__all__ = ["Ticker"]
