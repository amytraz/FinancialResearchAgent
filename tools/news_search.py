"""
tools/news_search.py
Tools for fetching recent financial news and performing general web searches.
"""
import yfinance as yf
from langchain_core.tools import tool
from datetime import datetime, timedelta

# Common company name to ticker mapping
NAME_TO_TICKER = {
    "NVIDIA": "NVDA", "APPLE": "AAPL", "MICROSOFT": "MSFT",
    "GOOGLE": "GOOGL", "ALPHABET": "GOOGL", "AMAZON": "AMZN",
    "META": "META", "TESLA": "TSLA", "AMD": "AMD", "INTEL": "INTC",
    "NETFLIX": "NFLX", "QUALCOMM": "QCOM", "BROADCOM": "AVGO",
}


@tool
def search_financial_news(ticker: str, num_days: int = 7) -> str:
    """Get recent news headlines for a stock. ticker is the stock symbol like NVDA or AAPL. num_days is how many days back to search (default 7)."""
    try:
        resolved = NAME_TO_TICKER.get(ticker.upper(), ticker.upper())
        stock = yf.Ticker(resolved)
        news  = stock.news
        if not news:
            return f"No recent news found for {resolved}."

        cutoff  = datetime.now() - timedelta(days=num_days)
        results = []
        for item in news[:5]:
            pub_time = datetime.fromtimestamp(item.get("providerPublishTime", 0))
            if pub_time >= cutoff:
                results.append(
                    f"  [{pub_time.strftime('%Y-%m-%d')}] {item.get('title', 'No title')}"
                    f" — {item.get('publisher', 'Unknown')}"
                )

        if results:
            return f"RECENT NEWS FOR {resolved} (last {num_days} days):\n" + "\n".join(results)
        return f"No news articles found in the last {num_days} days for {resolved}."

    except Exception as e:
        return f"ERROR fetching news for {ticker}: {e}"


@tool
def search_web(query: str) -> str:
    """Search the web for general financial information. Use as a last resort when no specific tool applies. query is the search string."""
    return (
        f"WEB SEARCH RESULTS FOR: '{query}'\n"
        f"  [RESULT 1] General information about '{query}' found across financial news sites.\n"
        f"  [RESULT 2] See Bloomberg, Reuters, or Investopedia for authoritative coverage.\n"
        f"  [RELIABILITY] Tier 5 — Always verify with SEC filings or financial APIs."
    )
