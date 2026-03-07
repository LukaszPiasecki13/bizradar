# Examples

Practical examples of using `bizradar` for financial analysis of companies listed on the Warsaw Stock Exchange (GPW).

---

## Quick Start

```python
import bizradar as br

t = br.Ticker("DNP")  # Dino Polska
```

---

## Financial Reports

### Annual Income Statement

```python
income = t.reports.income_statement
print(income)
```

### Quarterly Balance Sheet

```python
balance = t.reports.quarterly_balance_sheet
print(balance)
```

### Compare Revenue Growth

```python
income = t.reports.income_statement
revenue = income.loc["Przychody ze sprzedaży"]
growth = revenue.pct_change() * 100
print("Revenue YoY growth (%):")
print(growth.dropna())
```

---

## Financial Indicators

### Valuation Ratios

```python
val = t.indicators.valuation
print(val)
```

### Profitability Over Time

```python
prof = t.indicators.profitability
print(prof)
```

### All Indicator Categories

```python
# Available categories:
# valuation, profitability, cash_flow_indicators, debt, liquidity, activity
for cat in ["valuation", "profitability", "debt", "liquidity"]:
    df = getattr(t.indicators, cat)
    print(f"\n--- {cat.upper()} ---")
    print(df)
```

---

## Credit Rating

### Altman EM-Score & Piotroski F-Score

```python
rating = t.indicators.rating

print(f"Altman EM-Score: {rating['altman_score']}")
print(f"Altman Rating:   {rating['altman_rating']}")
print(rating["altman_details"])

print(f"\nPiotroski F-Score: {rating['piotroski_score']}")
print(rating["piotroski_details"])
```

---

## Market Data

### Historical Prices

```python
hist = t.market_data.history
print(hist.tail(10))

# Plot closing prices (requires matplotlib)
hist["Zamknięcie"].plot(title=f"{t.symbol} — Closing Price", figsize=(12, 5))
```

### Dividend History

```python
div = t.market_data.dividends
print(div[["Year", "DPS_PLN", "Status", "Payment_Date"]])
```

### Shareholder Structure

```python
shareholders = t.market_data.shareholders
print(shareholders[["Akcjonariusz", "Udział (%)", "Liczba akcji"]])
```

### Corporate Actions

```python
actions = t.market_data.corporate_actions
print(actions)
```

### Company Profile

```python
profile = t.market_data.profile
for key, value in profile.items():
    print(f"{key}: {value}")
```

---

## Multi-Ticker Analysis

```python
import pandas as pd
import bizradar as br

tickers = ["DNP", "CDR", "PKN", "KGH", "PZU"]
pe_data = {}

for symbol in tickers:
    t = br.Ticker(symbol)
    try:
        val = t.indicators.valuation
        # Get the latest P/E value (first column)
        pe_row = val.loc[val.index.str.contains("P/E", case=False)]
        if not pe_row.empty:
            pe_data[symbol] = pe_row.iloc[0, 0]
    except Exception as e:
        print(f"{symbol}: {e}")

pe_series = pd.Series(pe_data, name="P/E")
print(pe_series.sort_values())
```

---

## Export to Excel

```python
import bizradar as br

t = br.Ticker("DNP")

with pd.ExcelWriter("dino_financials.xlsx") as writer:
    t.reports.income_statement.to_excel(writer, sheet_name="Income Statement")
    t.reports.balance_sheet.to_excel(writer, sheet_name="Balance Sheet")
    t.reports.cash_flow.to_excel(writer, sheet_name="Cash Flow")
    t.indicators.valuation.to_excel(writer, sheet_name="Valuation")
    t.market_data.history.to_excel(writer, sheet_name="History")

print("Exported to dino_financials.xlsx")
```

---

## Jupyter Notebook Tips

```python
import bizradar as br

t = br.Ticker("DNP")

# Interactive display of available properties
t                          # shows all accessor groups
t.reports                  # shows available report types
t.indicators               # shows available indicator types
t.market_data              # shows available market data

# Rich HTML display in Jupyter
t.reports                  # renders as an HTML table
```
