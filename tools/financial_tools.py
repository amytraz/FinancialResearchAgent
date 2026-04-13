"""
tools/financial_tools.py
Consolidated financial metrics tool — pulls Price, P/E, Revenue, and margins
in a single yfinance call. This is the primary data tool for ARA-1.
"""
import yfinance as yf
from langchain_core.tools import tool


@tool
def get_financial_metrics(ticker: str) -> str:
    """Get a comprehensive snapshot of a stock including price, P/E ratio, revenue, profit margin, EPS, and market cap in one call. ticker is the stock symbol like NVDA or TSLA."""
    try:
        stock = yf.Ticker(ticker)
        info  = stock.info

        # Pull income statement for revenue
        try:
            income  = stock.income_stmt
            revenue = income.loc["Total Revenue"].iloc[0] if "Total Revenue" in income.index else None
            net_inc = income.loc["Net Income"].iloc[0]    if "Net Income"    in income.index else None
        except Exception:
            revenue = None
            net_inc = None

        rev_str = f"${revenue/1e9:.2f}B" if isinstance(revenue, (int, float)) else info.get("totalRevenue", "N/A")
        ni_str  = f"${net_inc/1e9:.2f}B" if isinstance(net_inc,  (int, float)) else "N/A"

        mktcap = info.get("marketCap", 0)
        mktcap_str = f"${mktcap/1e12:.2f}T" if mktcap > 1e12 else (f"${mktcap/1e9:.2f}B" if mktcap else "N/A")

        return (
            f"FINANCIAL METRICS FOR {ticker.upper()}:\n"
            f"  Current Price      : ${info.get('currentPrice', 'N/A')}\n"
            f"  Market Cap         : {mktcap_str}\n"
            f"  Annual Revenue     : {rev_str}\n"
            f"  Net Income         : {ni_str}\n"
            f"  P/E Ratio (TTM)    : {info.get('trailingPE', 'N/A')}\n"
            f"  Forward P/E        : {info.get('forwardPE', 'N/A')}\n"
            f"  EPS (TTM)          : ${info.get('trailingEps', 'N/A')}\n"
            f"  Profit Margin      : {round(info.get('profitMargins', 0)*100, 2)}%\n"
            f"  Revenue Growth YoY : {round(info.get('revenueGrowth', 0)*100, 2)}%\n"
            f"  ROE                : {round(info.get('returnOnEquity', 0)*100, 2)}%\n"
            f"  Debt-to-Equity     : {info.get('debtToEquity', 'N/A')}\n"
            f"  52-Week High       : ${info.get('fiftyTwoWeekHigh', 'N/A')}\n"
            f"  52-Week Low        : ${info.get('fiftyTwoWeekLow', 'N/A')}\n"
            f"  Beta               : {info.get('beta', 'N/A')}\n"
            f"\nSource: Yahoo Finance / yfinance (Tier 3)"
        )

    except Exception as e:
        return f"ERROR fetching financial metrics for {ticker}: {e}"
