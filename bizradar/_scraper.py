"""Core scraping logic for BiznesRadar financial reports."""

from __future__ import annotations

import re
from contextlib import contextmanager
from typing import TYPE_CHECKING

import pandas as pd
import requests
from bs4 import BeautifulSoup

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

if TYPE_CHECKING:
    from collections.abc import Generator

    from bs4 import Tag


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


@contextmanager
def _managed_session(
    session: requests.Session | None,
) -> Generator[requests.Session, None, None]:
    """Yield an existing session or create (and auto-close) a temporary one."""
    if session is not None:
        yield session
    else:
        s = requests.Session()
        try:
            yield s
        finally:
            s.close()


def _build_url(report_type: str, ticker: str, period: str) -> str:
    """Build full URL for a given report type, ticker and period."""
    segment = REPORT_URLS[report_type]
    return f"{BASE_URL}/{segment}/{ticker},{period},{DISPLAY_MODE}"


def _build_indicator_url(indicator_type: str, ticker: str) -> str:
    """Build full URL for an indicator page (no period suffix needed)."""
    segment = INDICATOR_URLS[indicator_type]
    return f"{BASE_URL}/{segment}/{ticker}"


def _fetch_html(url: str, session: requests.Session) -> BeautifulSoup:
    """Fetch a page and return parsed BeautifulSoup object."""
    response = session.get(url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def _parse_period(header_text: str) -> str:
    """Extract clean period label from header cell text.

    Examples:
        '2024(gru 24)'  -> '2024'
        '2025/Q3(wrz 25)' -> '2025/Q3'
        'O4K(wrz 25)*' -> 'TTM'
    """
    text = header_text.strip()
    if text.startswith("O4K") or text.startswith("O4Q"):
        return "TTM"
    match = re.match(r"^([\d/Q]+)", text)
    return match.group(1) if match else text


def _parse_value(cell: Tag) -> float | None:
    """Extract numeric value from a table data cell.

    Returns None for premium-locked or empty cells.
    """
    value_span = cell.select_one("span.value")
    if value_span is None:
        return None

    # Check if value is premium-locked
    premium = value_span.select_one(".premium-value")
    if premium:
        # Premium values still contain data in the HTML but are meant for
        # premium subscribers. We skip the "Data publikacji" row anyway,
        # but for actual financial rows premium-locked means no free data.
        # Check if it looks like a financial number vs date/text
        raw = premium.get_text(strip=True)
        if not re.search(r"[\d]", raw):
            return None

    # Get the text from the value span (first span.pv child)
    pv = value_span.select_one("span.pv")
    if pv is None:
        return None

    raw_text = pv.find("span").get_text(strip=True) if pv.find("span") else pv.get_text(strip=True)
    return _text_to_number(raw_text)


def _text_to_number(text: str) -> float | None:
    """Convert BiznesRadar number text to float.

    Handles space-separated thousands (e.g., '2 589 576'), negative values,
    and percentage values (e.g., '16,13%' -> 16.13).
    """
    cleaned = text.replace("\xa0", "").replace(" ", "").replace(",", ".")
    cleaned = cleaned.rstrip("%")
    if not cleaned or cleaned == "-":
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


_UNIT_MULTIPLIERS = {
    "tys": 1_000,
    "mln": 1_000_000,
    "mld": 1_000_000_000,
}


def _parse_unit_multiplier(soup: BeautifulSoup) -> int:
    """Extract the numeric multiplier from the report disclaimer.

    Looks for text like 'dane w tys. PLN' in ``div.report-disclaimer-above``
    and returns the corresponding multiplier (e.g. 1000).
    Falls back to 1 if not found.
    """
    disclaimer = soup.select_one("div.report-disclaimer-above")
    if disclaimer is None:
        return 1
    text = disclaimer.get_text(strip=True).lower()
    for key, mult in _UNIT_MULTIPLIERS.items():
        if key in text:
            return mult
    return 1


def _parse_report_table(soup: BeautifulSoup) -> pd.DataFrame:
    """Parse the main report table from a BiznesRadar financial page.

    Returns a DataFrame with period columns and financial item rows.
    """
    table = soup.select_one("table.report-table")
    if table is None:
        raise ValueError("Could not find report table (table.report-table) on the page.")

    rows = table.find_all("tr")
    if len(rows) < 2:
        raise ValueError("Report table has insufficient rows.")

    # --- Parse header row to get periods ---
    header_cells = rows[0].find_all(["th", "td"])
    periods: list[str] = []
    for cell in header_cells:
        classes = cell.get("class", [])
        if "thq" in classes:
            periods.append(_parse_period(cell.get_text(strip=True)))

    # --- Parse data rows ---
    data: dict[str, list[float | None]] = {}
    for row in rows[1:]:
        cells = row.find_all(["th", "td"])
        if not cells:
            continue

        # First cell is the label
        label_cell = cells[0]
        if "f" not in label_cell.get("class", []):
            continue

        label = label_cell.get_text(strip=True)
        if not label or label == "Data publikacji":
            continue

        # Extract values from data cells (skip label and chart cells)
        values: list[float | None] = []
        for cell in cells[1:]:
            classes = cell.get("class", [])
            if "h" in classes:
                values.append(_parse_value(cell))

        # Ensure values list matches periods length
        if len(values) != len(periods):
            # Pad or trim
            if len(values) < len(periods):
                values.extend([None] * (len(periods) - len(values)))
            else:
                values = values[: len(periods)]

        data[label] = values

    df = pd.DataFrame(data, index=periods).T
    df.index.name = "Pozycja"
    df.columns.name = "Okres"
    return df


def fetch_report(
    ticker: str,
    report_type: str,
    period: str = PERIOD_ANNUAL,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    """Fetch and parse a financial report from BiznesRadar.

    Args:
        ticker: Stock ticker symbol (e.g., 'DNP').
        report_type: One of 'income_statement', 'balance_sheet', 'cash_flow'.
        period: PERIOD_ANNUAL ('Y') or PERIOD_QUARTERLY ('Q').
        session: Optional requests.Session for connection reuse.

    Returns:
        DataFrame with periods as columns and financial line items as rows.
        Values are converted to base currency (PLN) from the original unit
        shown on the page (typically thousands).
    """
    if report_type not in REPORT_URLS:
        raise ValueError(
            f"Unknown report_type '{report_type}'. "
            f"Must be one of: {list(REPORT_URLS.keys())}"
        )

    with _managed_session(session) as s:
        url = _build_url(report_type, ticker, period)
        soup = _fetch_html(url, s)
        multiplier = _parse_unit_multiplier(soup)
        df = _parse_report_table(soup)
        if multiplier != 1:
            df = df.apply(lambda col: col * multiplier)
        return df


def fetch_indicator(
    ticker: str,
    indicator_type: str,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    """Fetch and parse a financial indicator table from BiznesRadar.

    Args:
        ticker: Stock ticker symbol (e.g., 'DNP').
        indicator_type: One of 'valuation', 'profitability',
            'cash_flow_indicators', 'debt', 'liquidity', 'activity'.
        session: Optional requests.Session for connection reuse.

    Returns:
        DataFrame with periods as columns and indicator rows.
    """
    if indicator_type not in INDICATOR_URLS:
        raise ValueError(
            f"Unknown indicator_type '{indicator_type}'. "
            f"Must be one of: {list(INDICATOR_URLS.keys())}"
        )

    with _managed_session(session) as s:
        url = _build_indicator_url(indicator_type, ticker)
        soup = _fetch_html(url, s)
        return _parse_report_table(soup)


# ---------------------------------------------------------------------------
# History, shareholders, corporate actions
# ---------------------------------------------------------------------------


def _parse_history_page(soup: BeautifulSoup) -> list[dict]:
    """Parse a single page of historical quotes."""
    table = soup.select_one("table.qTableFull")
    if table is None:
        return []
    rows = table.find_all("tr")[1:]  # skip header
    records: list[dict] = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 7:
            continue
        texts = [c.get_text(strip=True) for c in cells]
        records.append(
            {
                "Data": texts[0],
                "Otwarcie": _text_to_number(texts[1]),
                "Max": _text_to_number(texts[2]),
                "Min": _text_to_number(texts[3]),
                "Zamknięcie": _text_to_number(texts[4]),
                "Wolumen": _text_to_number(texts[5]),
                "Obrót": _text_to_number(texts[6]),
            }
        )
    return records


def fetch_history(
    ticker: str,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    """Fetch full historical daily OHLCV data.

    Returns a DataFrame indexed by date with columns:
    Otwarcie, Max, Min, Zamknięcie, Wolumen, Obrót.
    """
    with _managed_session(session) as s:
        all_records: list[dict] = []
        page = 1
        while True:
            if page == 1:
                url = f"{BASE_URL}/notowania-historyczne/{ticker}"
            else:
                url = f"{BASE_URL}/notowania-historyczne/{ticker},{page}"
            soup = _fetch_html(url, s)
            records = _parse_history_page(soup)
            if not records:
                break
            all_records.extend(records)
            pager = soup.select(".pages a.pages_pos")
            page_nums = [
                int(a.get_text(strip=True))
                for a in pager
                if a.get_text(strip=True).isdigit()
            ]
            if not page_nums or page >= max(page_nums):
                break
            page += 1

        if not all_records:
            return pd.DataFrame()

        df = pd.DataFrame(all_records)
        df["Data"] = pd.to_datetime(df["Data"], format="%d.%m.%Y")
        return df.sort_values("Data").set_index("Data")


def fetch_shareholders(
    ticker: str,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    """Fetch shareholder (akcjonariat) data.

    Returns a DataFrame with columns:
    Akcjonariusz, Udział (%), Liczba akcji, Wartość rynkowa,
    Udział na WZA (%), Liczba głosów, Data aktualizacji.
    """
    with _managed_session(session) as s:
        url = f"{BASE_URL}/akcjonariat/{ticker}"
        soup = _fetch_html(url, s)

        tables = soup.select("table.qTableFull")
        all_records: list[dict] = []
        for table in tables:
            rows = table.find_all("tr")[1:]  # skip header
            for row in rows:
                cells = row.find_all("td")
                if len(cells) < 7:
                    continue
                texts = [c.get_text(strip=True) for c in cells]
                name = texts[0]
                if name.lower() == "razem":
                    continue
                all_records.append(
                    {
                        "Akcjonariusz": name,
                        "Udział (%)": _text_to_number(texts[1].replace("%", "")),
                        "Liczba akcji": _text_to_number(texts[2]),
                        "Wartość rynkowa": _text_to_number(texts[3]),
                        "Udział na WZA (%)": _text_to_number(texts[4].replace("%", "")),
                        "Liczba głosów": _text_to_number(texts[5]),
                        "Data aktualizacji": texts[6] if texts[6] else None,
                    }
                )

        return pd.DataFrame(all_records)


def fetch_corporate_actions(
    ticker: str,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    """Fetch corporate actions (splits, etc.) from the operacje page.

    Returns a DataFrame with columns: Data, Typ, Nominalnie, Dzielnik.
    """
    with _managed_session(session) as s:
        url = f"{BASE_URL}/operacje/{ticker}"
        soup = _fetch_html(url, s)

        table = soup.select_one("table.qTableFull")
        if table is None:
            return pd.DataFrame()

        rows = table.find_all("tr")[1:]  # skip header
        records: list[dict] = []
        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 4:
                continue
            texts = [c.get_text(strip=True) for c in cells]
            records.append(
                {
                    "Data": texts[0],
                    "Typ": texts[1],
                    "Nominalnie": texts[2] if texts[2] != "-" else None,
                    "Dzielnik": _text_to_number(texts[3]),
                }
            )

        if not records:
            return pd.DataFrame()

        df = pd.DataFrame(records)
        df["Data"] = pd.to_datetime(df["Data"], format="%d.%m.%Y")
        return df.sort_values("Data").reset_index(drop=True)


def fetch_profile(
    ticker: str,
    session: requests.Session | None = None,
) -> dict[str, str | float]:
    """Fetch basic company profile info (ISIN, name, address, sector, etc.).
    
    Numeric fields (Liczba akcji, Kapitalizacja, Enterprise Value) are converted to float.
    """
    # Fields that should be converted from strings to numbers
    NUMERIC_FIELDS = {"Liczba akcji", "Kapitalizacja", "Enterprise Value"}
    
    with _managed_session(session) as s:
        url = f"{BASE_URL}/akcjonariat/{ticker}"
        soup = _fetch_html(url, s)

        info: dict[str, str | float] = {}
        for table in soup.select("table.profileSummary"):
            for row in table.find_all("tr"):
                cells = row.find_all(["th", "td"])
                if len(cells) == 2:
                    key = cells[0].get_text(strip=True).rstrip(":")
                    val = cells[1].get_text(strip=True)
                    if val:
                        # Try to convert numeric fields
                        if key in NUMERIC_FIELDS:
                            num_val = _text_to_number(val)
                            info[key] = num_val if num_val is not None else val
                        else:
                            info[key] = val
        return info


def fetch_dividends(
    ticker: str,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    """Fetch dividend history from the /dywidenda/ page.

    Returns a DataFrame with columns:
    Year, Advance_PLN, DPS_PLN, Total_Value_PLN, From_Reserve_PLN,
    Status, WZA_Date, Ex_Dividend_Date, Payment_Date.

    Monetary values are in PLN. Dividend yield is premium-locked and not included.
    """
    with _managed_session(session) as s:
        url = f"{BASE_URL}/{DIVIDEND_URL_SEGMENT}/{ticker}"
        soup = _fetch_html(url, s)

        # The first <table> on the page is the dividend table
        table = soup.select_one("table")
        if table is None:
            return pd.DataFrame()

        rows = table.find_all("tr")
        if len(rows) < 2:
            return pd.DataFrame()

        records: list[dict] = []
        for row in rows[1:]:  # skip header
            cells = row.find_all(["th", "td"])
            if len(cells) < 10:
                continue
            texts = [c.get_text(strip=True) for c in cells]

            year = _text_to_number(texts[0])
            if year is None:
                continue

            def _val(t: str) -> float | None:
                return None if t == "-" else _text_to_number(t)

            def _date(t: str) -> str | None:
                return t if t and t != "-" else None

            total_val = _val(texts[3])
            reserve_val = _val(texts[4])
            records.append(
                {
                    "Year": int(year),
                    "Advance_PLN": _val(texts[1]),
                    "DPS_PLN": _val(texts[2]),
                    "Total_Value_PLN": total_val * 1000 if total_val is not None else None,
                    "From_Reserve_PLN": reserve_val * 1000 if reserve_val is not None else None,
                    # texts[5] = stopa dywidendy (premium-locked)
                    "Status": texts[6] if texts[6] != "-" else None,
                    "WZA_Date": _date(texts[7]),
                    "Ex_Dividend_Date": _date(texts[8]),
                    "Payment_Date": _date(texts[9]),
                }
            )

        if not records:
            return pd.DataFrame()

        df = pd.DataFrame(records)
        return df.sort_values("Year", ascending=False).reset_index(drop=True)


def adjust_for_splits(
    history: pd.DataFrame,
    actions: pd.DataFrame,
) -> pd.DataFrame:
    """Adjust historical OHLCV data for stock splits.

    Divides prices and multiplies volume for all data points before each split date.
    Multiple splits are handled cumulatively.
    """
    if history.empty or actions.empty:
        return history

    splits = actions[actions["Dzielnik"].notna() & (actions["Dzielnik"] != 1.0)]
    if splits.empty:
        return history

    df = history.copy()
    price_cols = [c for c in ("Otwarcie", "Max", "Min", "Zamknięcie") if c in df.columns]

    for _, split in splits.iterrows():
        split_date = split["Data"]
        divisor = split["Dzielnik"]
        mask = df.index < split_date
        if not mask.any():
            continue
        df.loc[mask, price_cols] = df.loc[mask, price_cols] / divisor
        if "Wolumen" in df.columns:
            df.loc[mask, "Wolumen"] = df.loc[mask, "Wolumen"] * divisor

    return df


def fetch_rating(
    ticker: str,
    session: requests.Session | None = None,
) -> dict:
    """Fetch Altman EM-Score and Piotroski F-Score from the /rating/ page.

    Returns a dict with keys:
      - altman_score (float)
      - altman_rating (str, e.g. 'BB+')
      - altman_details (DataFrame: Indicator, Coefficient, Value)
      - piotroski_score (int)
      - piotroski_details (DataFrame: Indicator, Value, Score)
    """
    with _managed_session(session) as s:
        url = f"{BASE_URL}/{RATING_URL_SEGMENT}/{ticker}"
        soup = _fetch_html(url, s)

        result: dict = {
            "altman_score": None,
            "altman_rating": None,
            "altman_details": pd.DataFrame(),
            "piotroski_score": None,
            "piotroski_details": pd.DataFrame(),
        }

        tables = soup.select("table.rating-table")

        for table in tables:
            rows = table.find_all("tr")
            if not rows:
                continue

            title = rows[0].get_text(strip=True)

            if "Altman" in title:
                data_rows = [r for r in rows if "data" in r.get("class", [])]
                records = []
                for r in data_rows:
                    cells = [c.get_text(strip=True) for c in r.find_all(["th", "td"])]
                    if len(cells) == 3:
                        records.append(
                            {
                                "Indicator": cells[0],
                                "Coefficient": _text_to_number(cells[1]),
                                "Value": _text_to_number(cells[2]),
                            }
                        )
                result["altman_details"] = pd.DataFrame(records)

                # Summary rows (not class=data): score and rating
                for r in rows:
                    if "data" in r.get("class", []):
                        continue
                    cells = [c.get_text(strip=True) for c in r.find_all(["th", "td"])]
                    if len(cells) == 3:
                        if cells[0] == "Altman EM-Score":
                            result["altman_score"] = _text_to_number(cells[2])
                        elif cells[0] == "Rating":
                            result["altman_rating"] = cells[2]

            elif "Piotroski" in title:
                data_rows = [r for r in rows if "data" in r.get("class", [])]
                records = []
                for r in data_rows:
                    cells = r.find_all(["th", "td"])
                    if len(cells) == 3:
                        indicator = cells[0].get_text(strip=True)
                        # Value cell may contain "poprzedni okres:" suffix
                        val_text = cells[1].get_text(strip=True)
                        val_text = re.split(r"poprzedni okres:", val_text)[0]
                        score_text = cells[2].get_text(strip=True)
                        records.append(
                            {
                                "Indicator": indicator,
                                "Value": val_text,
                                "Score": int(score_text) if score_text.isdigit() else None,
                            }
                        )
                result["piotroski_details"] = pd.DataFrame(records)

                # Summary row
                for r in rows:
                    if "data" in r.get("class", []):
                        continue
                    cells = [c.get_text(strip=True) for c in r.find_all(["th", "td"])]
                    if len(cells) == 3 and cells[0] == "Piotroski F-Score":
                        val = _text_to_number(cells[2])
                        result["piotroski_score"] = int(val) if val is not None else None

        return result
