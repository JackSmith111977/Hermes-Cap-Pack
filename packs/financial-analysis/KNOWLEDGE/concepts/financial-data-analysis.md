---
type: concept
domain: financial-analysis
keywords: [financial, analysis, data, stocks, reporting]
created: 2026-05-14
---

# Financial Data Analysis

## Definition

Financial Data Analysis is the process of collecting, processing, and interpreting financial data to support investment decisions, business intelligence, and economic forecasting. For AI agents, this involves fetching real-time and historical market data, computing financial indicators, generating visualizations (charts, reports), and producing actionable insights. The domain spans stock market analysis, portfolio management, financial reporting, and economic indicator tracking.

## Core Concepts

### Data Sources and Types

| Data Type | Sources | Use Case |
|:----------|:--------|:---------|
| **Price data** | Yahoo Finance, Alpha Vantage, exchanges | OHLCV, moving averages, trend analysis |
| **Fundamental data** | SEC filings, financial statements | P/E ratio, EPS, revenue growth |
| **Economic indicators** | Government/central bank APIs | GDP, inflation, unemployment, interest rates |
| **News/sentiment** | News APIs, social media | Sentiment analysis, event-driven trading |
| **Alternative data** | Satellite, web scraping | Supply chain, foot traffic analysis |

### Key Financial Metrics

- **Valuation ratios**: P/E, P/B, P/S, EV/EBITDA — compare company value to earnings/assets
- **Profitability metrics**: Gross margin, operating margin, ROE, ROA — efficiency of operations
- **Liquidity ratios**: Current ratio, quick ratio — ability to meet short-term obligations
- **Technical indicators**: Moving averages, RSI, MACD, Bollinger Bands — price pattern analysis
- **Risk metrics**: Beta, Sharpe ratio, Value at Risk (VaR) — risk-adjusted returns

### Visualization Patterns

- **Line charts**: Price trends over time (closing price history)
- **Candlestick charts**: OHLC data with bullish/bearish patterns
- **Area charts**: Volume overlaid on price (volume profile)
- **Scatter plots**: Risk vs return for portfolio optimization
- **Heatmaps**: Sector/industry performance comparison

## Relationships

- **Related to**: `financial-analyst` skill (agent-driven analysis workflow)
- **Works with**: Data fetching APIs and chart rendering tools
- **Depends on**: Understanding of financial terminology, market mechanics
- **Output for**: `data-fetch-pitfalls`, `chart-rendering-tips` (Experience docs)
