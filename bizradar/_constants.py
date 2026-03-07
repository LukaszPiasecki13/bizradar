"""URL patterns and constants for BiznesRadar scraper."""

BASE_URL = "https://www.biznesradar.pl"

# Report type URL segments
REPORT_URLS = {
    "income_statement": "raporty-finansowe-rachunek-zyskow-i-strat",
    "balance_sheet": "raporty-finansowe-bilans",
    "cash_flow": "raporty-finansowe-przeplywy-pieniezne",
}

# Indicator type URL segments
INDICATOR_URLS = {
    "valuation": "wskazniki-wartosci-rynkowej",
    "profitability": "wskazniki-rentownosci",
    "cash_flow_indicators": "wskazniki-przeplywow-pienieznych",
    "debt": "wskazniki-zadluzenia",
    "liquidity": "wskazniki-plynnosci",
    "activity": "wskazniki-aktywnosci",
}

# Other page URL segments
DIVIDEND_URL_SEGMENT = "dywidenda"
RATING_URL_SEGMENT = "rating"

# Period suffixes appended to URLs
PERIOD_ANNUAL = "Y"
PERIOD_QUARTERLY = "Q"

# Display mode (0 = zestawienie/comparison)
DISPLAY_MODE = "0"

# HTTP headers to mimic a regular browser
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.8",
}

REQUEST_TIMEOUT = 15
