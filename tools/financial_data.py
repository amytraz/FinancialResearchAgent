"""
tools/financial_data.py
Tools for retrieving real-time stock prices, financial statements, and key metrics.
Data source: yfinance (free, no API key required).
"""
import yfinance as yf
from langchain_core.tools import tool


@tool
def get_stock_price(ticker: str) -> str:
    """Get the current stock price, market cap, and 52-week range. ticker is the stock symbol like NVDA or AAPL."""
    try:
        stock = yf.Ticker(ticker)
        info  = stock.info
        return (
            f"STOCK PRICE DATA FOR {ticker.upper()}:\n"
            f"  Current Price : ${info.get('currentPrice', 'N/A')}\n"
            f"  Market Cap    : ${info.get('marketCap', 'N/A'):,}\n"
            f"  52-Week High  : ${info.get('fiftyTwoWeekHigh', 'N/A')}\n"
            f"  52-Week Low   : ${info.get('fiftyTwoWeekLow', 'N/A')}\n"
            f"  Volume        : {info.get('volume', 'N/A'):,}\n"
            f"  Beta          : {info.get('beta', 'N/A')}"
        )
    except Exception as e:
        return f"ERROR fetching stock price for {ticker}: {e}"


@tool
def get_financial_statements(ticker: str, period: str = "annual") -> str:
    """Get income statement, balance sheet, and cash flow data. ticker is the stock symbol. period is 'annual' or 'quarterly'."""
    try:
        stock = yf.Ticker(ticker)
        if period == "quarterly":
            income = stock.quarterly_income_stmt
            balance = stock.quarterly_balance_sheet
        else:
            income = stock.income_stmt
            balance = stock.balance_sheet

        # Extract top-level rows
        revenue    = income.loc["Total Revenue"].iloc[0]       if "Total Revenue"    in income.index else "N/A"
        net_income = income.loc["Net Income"].iloc[0]          if "Net Income"       in income.index else "N/A"
        total_assets = balance.loc["Total Assets"].iloc[0]     if "Total Assets"     in balance.index else "N/A"
        total_debt   = balance.loc["Total Debt"].iloc[0]       if "Total Debt"       in balance.index else "N/A"

        return (
            f"FINANCIAL STATEMENTS FOR {ticker.upper()} ({period.upper()}):\n"
            f"  Revenue      : ${revenue:,.0f}\n"
            f"  Net Income   : ${net_income:,.0f}\n"
            f"  Total Assets : ${total_assets:,.0f}\n"
            f"  Total Debt   : ${total_debt:,.0f}"
        )
    except Exception as e:
        return f"ERROR fetching financial statements for {ticker}: {e}"


@tool
def get_key_metrics(ticker: str) -> str:
    """Get key valuation and profitability metrics: P/E ratio, EPS, ROE, profit margin, and debt-to-equity. ticker is the stock symbol."""
    try:
        stock = yf.Ticker(ticker)
        info  = stock.info
        return (
            f"KEY METRICS FOR {ticker.upper()}:\n"
            f"  P/E Ratio         : {info.get('trailingPE', 'N/A')}\n"
            f"  Forward P/E       : {info.get('forwardPE', 'N/A')}\n"
            f"  EPS (TTM)         : ${info.get('trailingEps', 'N/A')}\n"
            f"  ROE               : {info.get('returnOnEquity', 'N/A')}\n"
            f"  Profit Margin     : {info.get('profitMargins', 'N/A')}\n"
            f"  Debt-to-Equity    : {info.get('debtToEquity', 'N/A')}\n"
            f"  Revenue Growth    : {info.get('revenueGrowth', 'N/A')}\n"
            f"  Earnings Growth   : {info.get('earningsGrowth', 'N/A')}"
        )
    except Exception as e:
        return f"ERROR fetching key metrics for {ticker}: {e}"
