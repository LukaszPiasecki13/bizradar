"""Shared pytest fixtures and HTML fixtures for bizradar tests."""

import pytest
import requests


# ---------------------------------------------------------------------------
# HTML fixture snippets (replicating BiznesRadar page structures)
# ---------------------------------------------------------------------------

INCOME_STATEMENT_HTML = """
<html><body>
<table class="report-table">
  <tr>
    <th class="f">Pozycja</th>
    <td class="thq">2024(gru 24)</td>
    <td class="thq">2023(gru 23)</td>
    <td class="thq">2022(gru 22)</td>
    <td class="thq">O4K(wrz 25)*</td>
  </tr>
  <tr>
    <td class="f">Przychody ze sprzedaży</td>
    <td class="h"><span class="value"><span class="pv"><span>2 589 576</span></span></span></td>
    <td class="h"><span class="value"><span class="pv"><span>2 100 000</span></span></span></td>
    <td class="h"><span class="value"><span class="pv"><span>1 800 000</span></span></span></td>
    <td class="h"><span class="value"><span class="pv"><span>2 700 000</span></span></span></td>
  </tr>
  <tr>
    <td class="f">Zysk netto</td>
    <td class="h"><span class="value"><span class="pv"><span>150 000</span></span></span></td>
    <td class="h"><span class="value"><span class="pv"><span>120 000</span></span></span></td>
    <td class="h"><span class="value"><span class="pv"><span>-50 000</span></span></span></td>
    <td class="h"><span class="value"><span class="pv"><span>160 000</span></span></span></td>
  </tr>
  <tr>
    <td class="f">Data publikacji</td>
    <td class="h"><span class="value"><span class="pv"><span>2025-03-15</span></span></span></td>
    <td class="h"><span class="value"><span class="pv"><span>2024-03-15</span></span></span></td>
    <td class="h"><span class="value"><span class="pv"><span>2023-03-15</span></span></span></td>
    <td class="h"><span class="value"><span class="pv"><span>-</span></span></span></td>
  </tr>
  <tr>
    <td class="f">Marża zysku brutto</td>
    <td class="h"><span class="value"><span class="pv"><span>16,13%</span></span></span></td>
    <td class="h"><span class="value"><span class="pv"><span>14,50%</span></span></span></td>
    <td class="h"><span class="value"><span class="pv"><span>-</span></span></span></td>
    <td class="h"><span class="value"><span class="pv"><span>17,00%</span></span></span></td>
  </tr>
</table>
</body></html>
"""

HISTORY_HTML = """
<html><body>
<table class="qTableFull">
  <tr><th>Data</th><th>Otwarcie</th><th>Max</th><th>Min</th><th>Zamknięcie</th><th>Wolumen</th><th>Obrót</th></tr>
  <tr>
    <td>03.03.2025</td><td>135,00</td><td>137,50</td><td>134,00</td><td>136,80</td><td>12 500</td><td>1 710 000</td>
  </tr>
  <tr>
    <td>28.02.2025</td><td>133,00</td><td>136,00</td><td>132,50</td><td>135,00</td><td>10 200</td><td>1 377 000</td>
  </tr>
</table>
<div class="pages">
  <a class="pages_pos" href="#">1</a>
</div>
</body></html>
"""

HISTORY_PAGE2_HTML = """
<html><body>
<table class="qTableFull">
  <tr><th>Data</th><th>Otwarcie</th><th>Max</th><th>Min</th><th>Zamknięcie</th><th>Wolumen</th><th>Obrót</th></tr>
  <tr>
    <td>27.02.2025</td><td>130,00</td><td>134,00</td><td>129,50</td><td>133,00</td><td>8 000</td><td>1 064 000</td>
  </tr>
</table>
<div class="pages">
  <a class="pages_pos" href="#">1</a>
  <a class="pages_pos" href="#">2</a>
</div>
</body></html>
"""

HISTORY_EMPTY_HTML = """<html><body><div>No data</div></body></html>"""

SHAREHOLDERS_HTML = """
<html><body>
<table class="qTableFull">
  <tr><th>Akcjonariusz</th><th>Udział</th><th>Akcje</th><th>Wartość</th><th>WZA</th><th>Głosy</th><th>Data</th></tr>
  <tr>
    <td>Jan Kowalski</td><td>25,50%</td><td>10 000 000</td><td>1 368 000 000</td><td>30,00%</td><td>15 000 000</td><td>2024-12-31</td>
  </tr>
  <tr>
    <td>Razem</td><td>100%</td><td>39 215 686</td><td>5 364 545 000</td><td>100%</td><td>50 000 000</td><td></td>
  </tr>
</table>
</body></html>
"""

CORPORATE_ACTIONS_HTML = """
<html><body>
<table class="qTableFull">
  <tr><th>Data</th><th>Typ</th><th>Nominalnie</th><th>Dzielnik</th></tr>
  <tr><td>15.06.2020</td><td>Split</td><td>1:5</td><td>5</td></tr>
  <tr><td>10.01.2015</td><td>Split</td><td>1:10</td><td>10</td></tr>
</table>
</body></html>
"""

CORPORATE_ACTIONS_EMPTY_HTML = """<html><body><div>Brak danych</div></body></html>"""

PROFILE_HTML = """
<html><body>
<table class="profileSummary">
  <tr><th>Nazwa:</th><td>Dino Polska S.A.</td></tr>
  <tr><th>ISIN:</th><td>PLDINPL00011</td></tr>
  <tr><th>Sektor:</th><td>Handel detaliczny</td></tr>
  <tr><th>Rynek:</th><td>GPW</td></tr>
</table>
</body></html>
"""

DIVIDEND_HTML = """
<html><body>
<table>
  <tr><th>Rok</th><th>Zaliczka</th><th>DPS</th><th>Wartość</th><th>Z rezerw</th><th>Stopa</th><th>Status</th><th>WZA</th><th>Ex-div</th><th>Wypłata</th></tr>
  <tr>
    <td>2024</td><td>-</td><td>5,30</td><td>207 843</td><td>-</td><td>-</td><td>Wypłacona</td><td>15.05.2024</td><td>20.05.2024</td><td>03.06.2024</td>
  </tr>
  <tr>
    <td>2023</td><td>-</td><td>4,80</td><td>188 235</td><td>-</td><td>-</td><td>Wypłacona</td><td>10.05.2023</td><td>15.05.2023</td><td>30.05.2023</td>
  </tr>
</table>
</body></html>
"""

DIVIDEND_EMPTY_HTML = """<html><body></body></html>"""

RATING_HTML = """
<html><body>
<table class="rating-table">
  <tr><th colspan="3">Altman EM-Score</th></tr>
  <tr class="data"><th>Working Capital / Total Assets</th><td>6,56</td><td>0,15</td></tr>
  <tr class="data"><th>Retained Earnings / Total Assets</th><td>3,26</td><td>0,40</td></tr>
  <tr><th>Altman EM-Score</th><td></td><td>5,85</td></tr>
  <tr><th>Rating</th><td></td><td>BB+</td></tr>
</table>
<table class="rating-table">
  <tr><th colspan="3">Piotroski F-Score</th></tr>
  <tr class="data"><th>ROA &gt; 0</th><td>0,08</td><td>1</td></tr>
  <tr class="data"><th>Operating Cash Flow &gt; 0</th><td>500 000</td><td>1</td></tr>
  <tr><th>Piotroski F-Score</th><td></td><td>7</td></tr>
</table>
</body></html>
"""

REPORT_NO_TABLE_HTML = """<html><body><div>No report</div></body></html>"""

REPORT_EMPTY_ROWS_HTML = """
<html><body>
<table class="report-table">
  <tr><th class="f">Pozycja</th></tr>
</table>
</body></html>
"""

INCOME_STATEMENT_TYS_HTML = """
<html><body>
<div class="report-disclaimer-above">dane w tys. PLN</div>
<table class="report-table">
  <tr>
    <th class="f">Pozycja</th>
    <td class="thq">2024(gru 24)</td>
    <td class="thq">2023(gru 23)</td>
  </tr>
  <tr>
    <td class="f">Przychody ze sprzedaży</td>
    <td class="h"><span class="value"><span class="pv"><span>2 000</span></span></span></td>
    <td class="h"><span class="value"><span class="pv"><span>1 000</span></span></span></td>
  </tr>
</table>
</body></html>
"""

INCOME_STATEMENT_MLN_HTML = """
<html><body>
<div class="report-disclaimer-above">dane w mln. PLN</div>
<table class="report-table">
  <tr>
    <th class="f">Pozycja</th>
    <td class="thq">2024(gru 24)</td>
  </tr>
  <tr>
    <td class="f">Przychody ze sprzedaży</td>
    <td class="h"><span class="value"><span class="pv"><span>5</span></span></span></td>
  </tr>
</table>
</body></html>
"""

INCOME_STATEMENT_MLD_HTML = """
<html><body>
<div class="report-disclaimer-above">dane w mld. PLN</div>
<table class="report-table">
  <tr>
    <th class="f">Pozycja</th>
    <td class="thq">2024(gru 24)</td>
  </tr>
  <tr>
    <td class="f">Przychody ze sprzedaży</td>
    <td class="h"><span class="value"><span class="pv"><span>3</span></span></span></td>
  </tr>
</table>
</body></html>
"""

INCOME_STATEMENT_NO_UNIT_HTML = """
<html><body>
<table class="report-table">
  <tr>
    <th class="f">Pozycja</th>
    <td class="thq">2024(gru 24)</td>
  </tr>
  <tr>
    <td class="f">Wskaźnik</td>
    <td class="h"><span class="value"><span class="pv"><span>42</span></span></span></td>
  </tr>
</table>
</body></html>
"""


# ---------------------------------------------------------------------------
# Mock response / session helpers
# ---------------------------------------------------------------------------


class MockResponse:
    """Fake requests.Response for testing."""

    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


class MockSession:
    """Fake requests.Session that returns pre-defined HTML."""

    def __init__(self, responses: dict[str, str] | str = ""):
        if isinstance(responses, str):
            self._default = responses
            self._map = {}
        else:
            self._default = ""
            self._map = responses

    def get(self, url, **kwargs):
        for key, html in self._map.items():
            if key in url:
                return MockResponse(html)
        return MockResponse(self._default)

    def close(self):
        pass


@pytest.fixture
def mock_session():
    """Factory fixture to create MockSession instances."""
    def _factory(responses):
        return MockSession(responses)
    return _factory
