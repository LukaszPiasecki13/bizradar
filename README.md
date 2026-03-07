<p align="center">
  <h1 align="center">bizradar 📡</h1>
  <p align="center">
    <em>A Python library for financial data from BiznesRadar.pl</em>
  </p>
  <p align="center">
    <a href="https://github.com/your-username/bizradar"><img src="https://img.shields.io/badge/PyPI-v0.2.0-blue.svg" alt="PyPI version"></a>
    <a href="https://github.com/your-username/bizradar"><img src="https://img.shields.io/badge/python-3.10%2B-blue.svg" alt="Python versions"></a>
    <a href="https://github.com/your-username/bizradar/blob/main/LICENSE.txt"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License"></a>
    <img src="https://img.shields.io/badge/status-Beta-yellow.svg" alt="Project status">
  </p>
  <p align="center">
    <a href="#-installation">Installation</a> •
    <a href="#-quick-start">Quick Start</a> •
    <a href="#-features">Features</a> •
    <a href="#-documentation">Documentation</a> •
    <a href="#-license">License</a>
  </p>
</p>

---



**bizradar** is an **unofficial Python API wrapper and web scraper** for BiznesRadar.pl, providing **screen-scraped**  financial statements, key ratios, historical prices, dividends, and more for companies listed on the Warsaw Stock Exchange (GPW) from BiznesRadar.pl.

> [!IMPORTANT]
> **BiznesRadar.pl** is a trademark of Grupa Finansowa Media sp. z o.o.
>
> **bizradar** is **not affiliated, endorsed, or vetted** by BiznesRadar.pl or Grupa Finansowa Media sp. z o.o. It's an **open-source tool** that uses BiznesRadar.pl's **publicly available web pages**, and is intended for **research and educational purposes only**.
>
> You should refer to [BiznesRadar.pl's terms of use](https://www.biznesradar.pl/regulamin) for details on your rights to use the actual data downloaded. **The BiznesRadar.pl website is intended for personal use only.**

```python
import bizradar as br

t = br.Ticker("DNP")

t.reports.income_statement          # Annual income statement
t.indicators.valuation              # Valuation ratios (P/E, P/BV, ...)
t.market_data.history               # Full OHLCV history
t.market_data.dividends             # Dividend history
t.indicators.rating                 # Altman EM-Score and Piotroski F-Score
```

---

## Installation

### From source

```bash
git clone https://github.com/your-username/bizradar.git
cd bizradar
pip install .
```

### Requirements

- Python >= 3.10
- `requests` >= 2.28
- `beautifulsoup4` >= 4.12
- `pandas` >= 2.0

---

## Quick Start

```python
import bizradar as br

# Create a Ticker object for any GPW company
t = br.Ticker("CDR")  # CD Projekt

# Annual income statement
print(t.reports.income_statement)

# Quarterly balance sheet
print(t.reports.quarterly_balance_sheet)

# Profitability ratios
print(t.indicators.profitability)

# Historical price data
hist = t.market_data.history
print(hist.tail())
```

---

## Features

### Financial Reports

| Property | Description |
|----------|-------------|
| `reports.income_statement` | Annual income statement |
| `reports.balance_sheet` | Annual balance sheet |
| `reports.cash_flow` | Annual cash flow statement |
| `reports.quarterly_income_statement` | Quarterly income statement |
| `reports.quarterly_balance_sheet` | Quarterly balance sheet |
| `reports.quarterly_cash_flow` | Quarterly cash flow statement |

```python
income = t.reports.income_statement
revenue = income.loc["Przychody ze sprzedaży"]
print(revenue)
```

### Financial Indicators

| Property | Description |
|----------|-------------|
| `indicators.valuation` | Valuation ratios (P/E, P/BV, EV/EBIT, ...) |
| `indicators.profitability` | Profitability ratios (ROE, ROA, margins) |
| `indicators.cash_flow_indicators` | Cash flow indicators |
| `indicators.debt` | Debt ratios |
| `indicators.liquidity` | Liquidity ratios |
| `indicators.activity` | Activity ratios |
| `indicators.rating` | Altman EM-Score and Piotroski F-Score |

```python
# Valuation ratios
val = t.indicators.valuation
print(val)

# Credit score summary
rating = t.indicators.rating
print(f"Altman: {rating['altman_score']} ({rating['altman_rating']})")
print(f"Piotroski: {rating['piotroski_score']}")
```

### Market Data

| Property | Return Type | Description |
|----------|-------------|-------------|
| `market_data.history` | `DataFrame` | Full OHLCV history |
| `market_data.dividends` | `DataFrame` | Dividend history |
| `market_data.shareholders` | `DataFrame` | Shareholder structure |
| `market_data.corporate_actions` | `DataFrame` | Corporate actions (splits) |
| `market_data.profile` | `dict` | Company profile (ISIN, sector, ...) |

```python
# Historical prices
hist = t.market_data.history
hist["Zamknięcie"].plot(title="Closing Price", figsize=(12, 5))

# Dividends
div = t.market_data.dividends
print(div[["Year", "DPS_PLN", "Payment_Date"]])

# Company profile
profile = t.market_data.profile
print(f"{profile['Nazwa']} | ISIN: {profile['ISIN']}")
```


---

## License

**bizradar** is distributed under the **Apache Software License**. See the LICENSE.txt file in the release for details.

---

## ⚠️ Legal Disclaimer

**bizradar** is **not affiliated, endorsed, or vetted** by BiznesRadar.pl or Grupa Finansowa Media sp. z o.o.

It's an **open-source tool** that uses BiznesRadar.pl's publicly available web pages, and is intended for **research and educational purposes only**.

- This is a **hobby project** created for learning and non-commercial use
- Data is scraped from publicly accessible HTML pages
- Website structure may change at any time, breaking the parser
- No guarantees of accuracy, completeness, or availability
- **Use at your own risk**

You should refer to [BiznesRadar.pl's terms of use](https://www.biznesradar.pl/regulamin) for details on your rights to use the actual data downloaded.

**The BiznesRadar.pl website is intended for personal use only.**
