# API Reference

Full API documentation for `bizradar`.

---

## `bizradar.Ticker`

```python
bizradar.Ticker(symbol: str)
```

The main interface for accessing financial data of a single company listed on the Warsaw Stock Exchange (GPW) via BiznesRadar.pl.

### Parameters

| Parameter | Type  | Description                                       |
|-----------|-------|---------------------------------------------------|
| `symbol`  | `str` | Ticker symbol as used on BiznesRadar (e.g. `"DNP"`, `"CDR"`, `"PKN"`) |

### Attributes

| Attribute      | Type           | Description                                     |
|----------------|----------------|-------------------------------------------------|
| `symbol`       | `str`          | Uppercased ticker symbol                        |
| `reports`      | `_Reports`     | Accessor for financial reports (see below)       |
| `indicators`   | `_Indicators`  | Accessor for financial indicators (see below)    |
| `market_data`  | `_MarketData`  | Accessor for market & company data (see below)   |

### Methods

#### `clear_cache()`

Clears all cached data, forcing fresh HTTP fetches on next property access.

```python
t = bizradar.Ticker("DNP")
_ = t.reports.income_statement   # fetched from network
t.clear_cache()
_ = t.reports.income_statement   # fetched again from network
```

---

## Reports — `Ticker.reports`

All report properties return a `pandas.DataFrame` with:
- **Index**: Financial line items (e.g. `"Przychody ze sprzedaży"`, `"Zysk netto"`)
- **Columns**: Periods (e.g. `"2024"`, `"2023"`, `"TTM"`)

### Properties

| Property                        | Period    | Description                   |
|---------------------------------|-----------|-------------------------------|
| `income_statement`              | Annual    | Income statement (Rachunek zysków i strat) |
| `balance_sheet`                 | Annual    | Balance sheet (Bilans)        |
| `cash_flow`                     | Annual    | Cash flow statement (Przepływy pieniężne) |
| `quarterly_income_statement`    | Quarterly | Income statement              |
| `quarterly_balance_sheet`       | Quarterly | Balance sheet                 |
| `quarterly_cash_flow`           | Quarterly | Cash flow statement           |

### Example

```python
import bizradar as br

t = br.Ticker("DNP")
income = t.reports.income_statement
print(income.loc["Przychody ze sprzedaży"])
```

```
Okres
2024    2.589576e+06
2023    2.100000e+06
2022    1.800000e+06
TTM     2.700000e+06
Name: Przychody ze sprzedaży, dtype: float64
```

---

## Indicators — `Ticker.indicators`

All indicator properties (except `rating`) return a `pandas.DataFrame` with the same structure as reports.

### Properties

| Property               | Description                                       |
|------------------------|---------------------------------------------------|
| `valuation`            | Market valuation ratios (P/E, P/BV, EV/EBIT, EV/EBITDA, …) |
| `profitability`        | Profitability ratios (ROE, ROA, margins, …)       |
| `cash_flow_indicators` | Cash flow-based indicators                        |
| `debt`                 | Debt ratios (Debt/Equity, Debt/EBITDA, …)         |
| `liquidity`            | Liquidity ratios (Current, Quick, …)              |
| `activity`             | Activity ratios (inventory/receivable cycles, …)  |
| `rating`               | Altman EM-Score & Piotroski F-Score (returns `dict`) |

### Rating dict structure

```python
{
    "altman_score": 5.85,           # float
    "altman_rating": "BB+",         # str
    "altman_details": pd.DataFrame,  # Indicator, Coefficient, Value
    "piotroski_score": 7,           # int
    "piotroski_details": pd.DataFrame,  # Indicator, Value, Score
}
```

### Example

```python
t = br.Ticker("CDR")

# Valuation ratios
pe = t.indicators.valuation
print(pe)

# Credit rating
rating = t.indicators.rating
print(f"Altman: {rating['altman_score']} ({rating['altman_rating']})")
print(f"Piotroski: {rating['piotroski_score']}")
```

---

## Market Data — `Ticker.market_data`

### Properties

| Property            | Returns          | Description                                    |
|---------------------|------------------|------------------------------------------------|
| `history`           | `pd.DataFrame`   | Full historical OHLCV data, indexed by date    |
| `dividends`         | `pd.DataFrame`   | Dividend history with DPS, dates, status       |
| `shareholders`      | `pd.DataFrame`   | Current shareholder structure                  |
| `corporate_actions` | `pd.DataFrame`   | Corporate actions (splits, etc.)               |
| `profile`           | `dict[str, str]` | Company profile (name, ISIN, sector, …)        |

### `history` columns

| Column      | Type    | Description          |
|-------------|---------|----------------------|
| `Otwarcie`  | `float` | Open price           |
| `Max`       | `float` | High price           |
| `Min`       | `float` | Low price            |
| `Zamknięcie`| `float` | Close price          |
| `Wolumen`   | `float` | Volume               |
| `Obrót`     | `float` | Turnover             |

Index: `Data` (`datetime64`)

### `dividends` columns

| Column             | Type         | Description                    |
|--------------------|--------------|--------------------------------|
| `Year`             | `int`        | Dividend year                  |
| `Advance_PLN`      | `float/None` | Advance payment per share      |
| `DPS_PLN`          | `float/None` | Dividend per share (PLN)       |
| `Total_Value_kPLN` | `float/None` | Total dividend value (thousands PLN) |
| `From_Reserve_kPLN`| `float/None` | Amount from reserves           |
| `Status`           | `str/None`   | Payment status                 |
| `WZA_Date`         | `str/None`   | General meeting date           |
| `Ex_Dividend_Date` | `str/None`   | Ex-dividend date               |
| `Payment_Date`     | `str/None`   | Payment date                   |

### `shareholders` columns

| Column              | Type         | Description                   |
|---------------------|--------------|-------------------------------|
| `Akcjonariusz`      | `str`        | Shareholder name              |
| `Udział (%)`        | `float`      | Ownership share (%)           |
| `Liczba akcji`      | `float`      | Number of shares              |
| `Wartość rynkowa`   | `float`      | Market value                  |
| `Udział na WZA (%)` | `float`      | Voting share at AGM (%)       |
| `Liczba głosów`     | `float`      | Number of votes               |
| `Data aktualizacji` | `str/None`   | Last update date              |

### Example

```python
t = br.Ticker("DNP")

# Historical prices
hist = t.market_data.history
print(hist.tail())

# Dividends
div = t.market_data.dividends
print(div[["Year", "DPS_PLN", "Payment_Date"]])

# Company profile
profile = t.market_data.profile
print(f"{profile['Nazwa']} | ISIN: {profile['ISIN']}")
```

---

## Caching

All data properties are **lazy-loaded** and **cached** in memory. The first access triggers an HTTP request; subsequent accesses return the cached result instantly.

```python
t = br.Ticker("DNP")

# First access — fetches from BiznesRadar
income = t.reports.income_statement

# Second access — returns cached DataFrame (no HTTP request)
income = t.reports.income_statement

# Force refresh
t.clear_cache()
income = t.reports.income_statement  # fetches again
```

---

## Session Management

Each `Ticker` instance creates its own `requests.Session` internally for HTTP connection reuse. The session is closed when the `Ticker` object is garbage-collected.

---

## Exceptions

| Exception       | When                                                    |
|-----------------|---------------------------------------------------------|
| `ValueError`    | Invalid `report_type` or `indicator_type`               |
| `ValueError`    | Report table not found on page or has insufficient rows |
| `requests.HTTPError` | HTTP error from BiznesRadar (4xx/5xx)              |
| `requests.ConnectionError` | Network connectivity issues                  |
| `AttributeError` | Accessing non-existent property on accessor            |
