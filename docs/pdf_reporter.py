"""
docs/pdf_reporter.py  —  Legacy stub.
PDF generation is now handled by the FastAPI endpoint in api.py
POST /api/download-pdf  →  returns a streaming PDF via ReportLab
"""

def generate_pdf(ticker: str, report_text: str, research_data: dict, report_json: dict) -> str:
    """Legacy PDF generation stub. Use the /api/download-pdf endpoint instead."""
    raise NotImplementedError(
        "PDF generation has moved to the FastAPI endpoint. "
        "Use POST /api/download-pdf with the report_json payload."
    )