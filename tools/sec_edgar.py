"""
tools/sec_edgar.py
Retrieves real SEC EDGAR filings using the free public EDGAR Full-Text Search API.
No API key required — only a User-Agent header (SEC policy).
"""
import os
import requests
from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()

EDGAR_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index?q={query}&dateRange=custom&startdt={start}&enddt={end}&forms={form}"
EDGAR_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
EDGAR_COMPANY_SEARCH = "https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22&forms={form}&dateRange=custom&startdt={start}&enddt={end}"


def _get_cik(ticker: str, user_agent: str) -> str | None:
    """Resolves a ticker to its SEC CIK number."""
    try:
        resp = requests.get(
            "https://www.sec.gov/cgi-bin/browse-edgar",
            params={"company": "", "CIK": ticker, "type": "", "dateb": "", "owner": "include", "count": "1", "search_text": "", "action": "getcompany", "output": "atom"},
            headers={"User-Agent": user_agent},
            timeout=10,
        )
        # Extract CIK from the atom feed
        import re
        match = re.search(r"CIK=(\d+)", resp.text)
        return match.group(1).zfill(10) if match else None
    except Exception:
        return None


@tool
def sec_filing_search(ticker: str, filing_type: str, year: int = 2024) -> str:
    """Search SEC EDGAR for real company filings. ticker is the stock symbol like NVDA. filing_type is '10-K', '10-Q', or '8-K'. year is the filing year."""
    user_agent = os.getenv("SEC_API_USER_AGENT", "ARA1ResearchAgent/1.0 (research@ara1agent.com)")
    headers    = {"User-Agent": user_agent, "Accept-Encoding": "gzip, deflate"}

    try:
        # Step 1: Get CIK for the ticker
        cik = _get_cik(ticker, user_agent)

        if cik:
            # Step 2: Pull submissions from EDGAR data API
            sub_url  = f"https://data.sec.gov/submissions/CIK{cik}.json"
            sub_resp = requests.get(sub_url, headers=headers, timeout=10)
            sub_data = sub_resp.json()

            company_name = sub_data.get("name", ticker.upper())
            filings      = sub_data.get("filings", {}).get("recent", {})

            forms        = filings.get("form", [])
            dates        = filings.get("filingDate", [])
            accessions   = filings.get("accessionNumber", [])
            descriptions = filings.get("primaryDocument", [])

            # Find matching filings for the requested type and year
            matches = []
            for i, form in enumerate(forms):
                if form == filing_type and str(year) in dates[i]:
                    acc = accessions[i].replace("-", "")
                    link = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/{descriptions[i]}"
                    matches.append(f"  Filing Date : {dates[i]}\n  Document    : {descriptions[i]}\n  URL         : {link}")
                    if len(matches) >= 2:
                        break

            if matches:
                return (
                    f"SEC EDGAR — {filing_type} FILINGS FOR {company_name} ({ticker.upper()}):\n"
                    + "\n\n".join(matches)
                    + f"\n\nSource: SEC EDGAR (Tier 1 — Audited regulatory filing)"
                )

        # Fallback: EDGAR full-text search
        start = f"{year}-01-01"
        end   = f"{year}-12-31"
        search_url = (
            f"https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22"
            f"&forms={filing_type}&dateRange=custom&startdt={start}&enddt={end}"
        )
        resp = requests.get(search_url, headers=headers, timeout=10)
        data = resp.json()
        hits = data.get("hits", {}).get("hits", [])

        if hits:
            result_lines = [f"SEC EDGAR SEARCH — {filing_type} for {ticker.upper()} ({year}):"]
            for hit in hits[:3]:
                src = hit.get("_source", {})
                result_lines.append(
                    f"  [{src.get('file_date', 'N/A')}] {src.get('display_names', [ticker])[0] if src.get('display_names') else ticker}"
                    f" | Form: {src.get('form_type', filing_type)}"
                    f"\n  URL: https://www.sec.gov{src.get('file_url', '')}"
                )
            return "\n".join(result_lines) + "\n\nSource: SEC EDGAR (Tier 1 — Audited regulatory filing)"

        return f"No {filing_type} filings found on SEC EDGAR for {ticker.upper()} in {year}. Try a different year or filing type."

    except Exception as e:
        return f"ERROR querying SEC EDGAR for {ticker} {filing_type}: {e}"
