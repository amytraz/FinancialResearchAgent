"""
tools/analysis.py
Advanced financial analysis tools:
  - calculate_dcf     : Discounted Cash Flow valuation
  - compare_competitors: Peer comparison table
  - get_analyst_ratings: Analyst consensus ratings
All use yfinance as the data source (free tier).
"""
import yfinance as yf
from langchain_core.tools import tool


@tool
def calculate_dcf(ticker: str, growth_rate: float = 0.10) -> str:
    """Run a Discounted Cash Flow valuation for a stock. ticker is the stock symbol. growth_rate is the expected annual FCF growth rate as a decimal like 0.10 for 10 percent."""
    try:
        stock      = yf.Ticker(ticker)
        cashflow   = stock.cashflow
        info       = stock.info

        shares_out = info.get("sharesOutstanding", None)

        # Get most recent Free Cash Flow
        if "Free Cash Flow" in cashflow.index:
            fcf = cashflow.loc["Free Cash Flow"].iloc[0]
        elif "Operating Cash Flow" in cashflow.index:
            fcf = cashflow.loc["Operating Cash Flow"].iloc[0] * 0.85  # Rough FCF estimate
        else:
            return f"ERROR: Could not retrieve cash flow data for {ticker}."

        # DCF Calculation (simplified Gordon Growth / 5-year DCF)
        discount_rate  = 0.10
        terminal_growth = 0.03
        projected_fcf  = []
        for year in range(1, 6):
            projected_fcf.append(fcf * ((1 + growth_rate) ** year) / ((1 + discount_rate) ** year))

        terminal_value = (projected_fcf[-1] * (1 + terminal_growth)) / (discount_rate - terminal_growth)
        terminal_pv    = terminal_value / ((1 + discount_rate) ** 5)
        total_value    = sum(projected_fcf) + terminal_pv

        intrinsic_per_share = (total_value / shares_out) if shares_out else "N/A"
        current_price       = info.get("currentPrice", "N/A")

        return (
            f"DCF VALUATION FOR {ticker.upper()}:\n"
            f"  Base FCF (Latest)        : ${fcf:,.0f}\n"
            f"  Growth Rate Assumed      : {growth_rate*100:.1f}%\n"
            f"  Discount Rate (WACC)     : 10.0%\n"
            f"  Sum of PV (5-year FCFs)  : ${sum(projected_fcf):,.0f}\n"
            f"  Terminal Value (PV)      : ${terminal_pv:,.0f}\n"
            f"  Total Intrinsic Value    : ${total_value:,.0f}\n"
            f"  Intrinsic Value/Share    : ${intrinsic_per_share:,.2f}\n"
            f"  Current Market Price     : ${current_price}\n"
            f"  Verdict                  : {'UNDERVALUED ✅' if isinstance(intrinsic_per_share, float) and isinstance(current_price, (int, float)) and intrinsic_per_share > current_price else 'OVERVALUED ⚠️'}"
        )

    except Exception as e:
        return f"ERROR performing DCF for {ticker}: {e}"


@tool
def compare_competitors(ticker: str, competitors: str = "") -> str:
    """Compare a stock against competitors on price, P/E, market cap, and margins. ticker is the main stock symbol. competitors is a comma-separated list like AMD,INTC."""
    try:
        peer_list = [t.strip().upper() for t in competitors.split(",") if t.strip()] if competitors else []
        all_tickers = [ticker.upper()] + peer_list

        rows   = []
        header = f"{'Ticker':<8} | {'Price':>10} | {'P/E':>8} | {'Mkt Cap':>14} | {'Rev Growth':>11} | {'Profit Margin':>14}"
        rows.append(header)
        rows.append("─" * len(header))

        for t in all_tickers:
            try:
                info = yf.Ticker(t).info
                price   = f"${info.get('currentPrice', 'N/A')}"
                pe      = f"{info.get('trailingPE', 'N/A')}"
                mktcap  = f"${info.get('marketCap', 0)/1e9:.1f}B"
                rev_g   = f"{info.get('revenueGrowth', 'N/A')}"
                margin  = f"{info.get('profitMargins', 'N/A')}"
                rows.append(f"{t:<8} | {price:>10} | {pe:>8} | {mktcap:>14} | {rev_g:>11} | {margin:>14}")
            except Exception:
                rows.append(f"{t:<8} | ERROR retrieving data")

        return "COMPETITOR COMPARISON:\n" + "\n".join(rows)

    except Exception as e:
        return f"ERROR comparing competitors: {e}"


@tool
def get_analyst_ratings(ticker: str) -> str:
    """Get analyst buy/hold/sell consensus rating and price targets for a stock. ticker is the stock symbol."""
    try:
        stock = yf.Ticker(ticker)
        info  = stock.info

        rating_summary = (
            f"ANALYST RATINGS FOR {ticker.upper()}:\n"
            f"  Recommendation     : {info.get('recommendationKey', 'N/A').upper()}\n"
            f"  Mean Target Price  : ${info.get('targetMeanPrice', 'N/A')}\n"
            f"  Low Target Price   : ${info.get('targetLowPrice', 'N/A')}\n"
            f"  High Target Price  : ${info.get('targetHighPrice', 'N/A')}\n"
            f"  Number of Analysts : {info.get('numberOfAnalystOpinions', 'N/A')}\n"
        )

        try:
            recs = stock.recommendations
            if recs is not None and not recs.empty and isinstance(recs, __import__('pandas').DataFrame):
                rating_summary += "\n  RECENT RATING CHANGES:\n"
                for _, row in recs.tail(5).iterrows():
                    # Defensive date parsing — index may be int, Timestamp, or datetime
                    idx = row.name
                    if hasattr(idx, 'date'):
                        date_str = idx.date().isoformat()
                    elif hasattr(idx, 'strftime'):
                        date_str = idx.strftime('%Y-%m-%d')
                    else:
                        date_str = str(idx)
                    firm  = row.get('Firm', row.get('firm', 'N/A'))
                    grade = row.get('To Grade', row.get('toGrade', 'N/A'))
                    rating_summary += f"    {date_str} | {firm} | {grade}\n"
        except Exception:
            rating_summary += "  (Recent rating changes unavailable)\n"

        rating_summary += "\nSource: Yahoo Finance / yfinance (Tier 3)"
        return rating_summary

    except Exception as e:
        return f"ERROR fetching analyst ratings for {ticker}: {e}"
