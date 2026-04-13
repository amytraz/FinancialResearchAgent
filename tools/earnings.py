"""
tools/earnings.py
Retrieves real earnings history data from yfinance.
Quarterly EPS actuals, estimates, and surprise percentages.
"""
import yfinance as yf
from langchain_core.tools import tool


@tool
def get_earnings_transcript(ticker: str, quarter: str = "Q4", year: int = 2024) -> str:
    """Get real historical earnings data including EPS actuals, estimates, and surprise percentages. ticker is the stock symbol. quarter is Q1 Q2 Q3 or Q4. year is the fiscal year."""
    try:
        stock = yf.Ticker(ticker)

        # --- Real earnings history (EPS beats/misses) ---
        earnings_hist = stock.earnings_history
        summary = f"EARNINGS HISTORY FOR {ticker.upper()}:\n"

        if earnings_hist is not None and not earnings_hist.empty:
            recent = earnings_hist.head(8)
            for idx, row in recent.iterrows():
                eps_actual   = row.get("epsActual",       "N/A")
                eps_estimate = row.get("epsEstimate",     "N/A")
                surprise     = row.get("surprisePercent", "N/A")
                beat = ""
                if isinstance(surprise, (int, float)):
                    beat = "✅ BEAT" if surprise > 0 else "❌ MISS"
                summary += (
                    f"  {idx.date() if hasattr(idx, 'date') else idx} | "
                    f"EPS Actual: ${eps_actual} | "
                    f"EPS Estimate: ${eps_estimate} | "
                    f"Surprise: {round(surprise, 2) if isinstance(surprise, float) else surprise}% {beat}\n"
                )
        else:
            summary += "  No earnings history data available from yfinance.\n"

        # --- Real annual earnings trend ---
        info = stock.info
        summary += f"\nKEY EARNINGS METRICS ({ticker.upper()}):\n"
        summary += f"  Trailing EPS      : ${info.get('trailingEps', 'N/A')}\n"
        summary += f"  Forward EPS       : ${info.get('forwardEps', 'N/A')}\n"
        summary += f"  Earnings Growth   : {info.get('earningsGrowth', 'N/A')}\n"
        summary += f"  Revenue Growth    : {info.get('revenueGrowth', 'N/A')}\n"
        summary += f"  Payout Ratio      : {info.get('payoutRatio', 'N/A')}\n"
        summary += "\nSource: Yahoo Finance / yfinance (Tier 3 — Third-party financial data)"

        return summary

    except Exception as e:
        return f"ERROR fetching earnings data for {ticker}: {e}"
