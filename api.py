"""
api.py  —  ARA-1 FastAPI Backend
Provides:
  POST /api/research          → SSE streaming of agent progress + final JSON
  GET  /api/reports           → List all saved report JSONs
  GET  /api/report/{ticker}   → Fetch latest JSON report for a ticker
  POST /api/download-pdf      → Stream back a server-generated PDF (via reportlab)
"""
import os
import sys
import json
import glob
import datetime
import warnings
import asyncio
import io

# Suppress noise
os.environ["TOKENIZERS_PARALLELISM"]       = "false"
os.environ["TRANSFORMERS_VERBOSITY"]       = "error"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
warnings.filterwarnings("ignore")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

app = FastAPI(title="ARA-1 Financial Research Agent", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request models ────────────────────────────────────────────
class ResearchRequest(BaseModel):
    ticker: str

class PDFRequest(BaseModel):
    report_json: dict


# ── SSE helpers ──────────────────────────────────────────────
def _sse(event: str, data: dict) -> str:
    payload = json.dumps({"event": event, **data})
    return f"data: {payload}\n\n"


# ── Research streaming endpoint ──────────────────────────────
@app.post("/api/research")
async def research_stream(req: ResearchRequest):
    ticker = req.ticker.strip().upper()

    async def generator():
        loop = asyncio.get_event_loop()

        # Step 1: Import
        yield _sse("status", {"phase": "BOOT", "message": f"Initialising ARA-1 for {ticker}…", "step": 0})
        await asyncio.sleep(0.1)

        try:
            from agent.core import ARA1Agent
        except Exception as e:
            yield _sse("error", {"message": f"Import error: {e}"})
            return

        yield _sse("status", {"phase": "BOOT", "message": "Agent loaded. Building LangGraph…", "step": 1})
        await asyncio.sleep(0.1)

        # Build agent in thread (blocking)
        bot = ARA1Agent()
        graph = bot.build_graph()
        initial_state = {
            "ticker":            ticker,
            "research_data":     {},
            "validated_metrics": None,
            "data_warnings":     [],
            "final_report":      None,
            "report_json":       None,
        }

        yield _sse("status", {"phase": "OBSERVE", "message": "Launching 4 parallel research tools…", "step": 2})

        # Run graph in thread pool
        final_state = {}

        def _run_graph():
            nonlocal final_state
            config = {"recursion_limit": 15}
            for output in graph.stream(initial_state, config=config):
                for node_name, value in output.items():
                    final_state[node_name] = value

        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            # Kick off in background
            fut = loop.run_in_executor(pool, _run_graph)

            # Emit heartbeats while running
            phases = [
                (3,  "OBSERVE",  "Collecting financial metrics, SEC filings, DCF & analyst data…"),
                (4,  "ORIENT",   "Validating data quality & extracting metrics deterministically…"),
                (5,  "DECIDE",   "LLM synthesising 10-section institutional report…"),
                (6,  "ACT",      "Deterministic Decision Engine enforcing MoS rules…"),
            ]
            delay_per_phase = 8  # seconds between status ticks

            for step, phase, msg in phases:
                # Wait a bit, re-check if done
                for _ in range(delay_per_phase * 2):
                    if fut.done():
                        break
                    yield _sse("status", {"phase": phase, "message": msg, "step": step})
                    await asyncio.sleep(0.5)
                if fut.done():
                    break

            # Ensure complete
            await asyncio.wrap_future(fut)

        # Get report from final state
        report_json = None
        for node_name in ["enforcer", "synthesizer", "validator", "researcher"]:
            v = final_state.get(node_name, {})
            if v.get("report_json"):
                report_json = v["report_json"]
                break

        if not report_json:
            yield _sse("error", {"message": "No report generated. Check API keys and try again."})
            return

        # Save JSON
        os.makedirs("docs/reports", exist_ok=True)
        today = str(datetime.date.today())
        json_path = f"docs/reports/{ticker}_{today}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report_json, f, indent=2, ensure_ascii=False)

        yield _sse("complete", {"report": report_json, "saved_path": json_path})

    return StreamingResponse(generator(), media_type="text/event-stream")


# ── List all reports ─────────────────────────────────────────
@app.get("/api/reports")
async def list_reports():
    files = sorted(glob.glob("docs/reports/*.json"), reverse=True)
    reports = []
    for f in files:
        try:
            with open(f, encoding="utf-8") as fh:
                data = json.load(fh)
            reports.append({
                "filename": os.path.basename(f),
                "ticker": data.get("ticker", ""),
                "date": data.get("date", ""),
                "recommendation": data.get("recommendation", ""),
                "confidence": data.get("confidence", ""),
                "current_price": data.get("current_price"),
                "margin_of_safety_pct": data.get("margin_of_safety_pct"),
            })
        except Exception:
            pass
    return JSONResponse(content=reports)


# ── Get single report ─────────────────────────────────────────
@app.get("/api/report/{ticker}")
async def get_report(ticker: str):
    ticker = ticker.upper()
    files = sorted(glob.glob(f"docs/reports/{ticker}_*.json"), reverse=True)
    if not files:
        raise HTTPException(status_code=404, detail=f"No report found for {ticker}")
    with open(files[0], encoding="utf-8") as f:
        return JSONResponse(content=json.load(f))


# ── PDF generation endpoint ──────────────────────────────────
@app.post("/api/download-pdf")
async def download_pdf(req: PDFRequest):
    rj = req.report_json
    ticker     = rj.get("ticker", "UNKNOWN")
    date_str   = rj.get("date", str(datetime.date.today()))
    rec        = (rj.get("recommendation") or "NEUTRAL").upper()
    conf       = (rj.get("confidence") or "N/A").upper()

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        )
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            rightMargin=1.8*cm, leftMargin=1.8*cm,
            topMargin=2*cm, bottomMargin=2*cm,
        )

        # ── Colour palette ──
        DARK_BG     = colors.HexColor("#0D1117")
        ACCENT      = colors.HexColor("#00D4FF")
        GOLD        = colors.HexColor("#FFD700")
        GREEN       = colors.HexColor("#00FF88")
        RED         = colors.HexColor("#FF4444")
        YELLOW      = colors.HexColor("#FFB800")
        TEXT        = colors.HexColor("#E6EDF3")
        MUTED       = colors.HexColor("#8B949E")
        TABLE_HDR   = colors.HexColor("#161B22")
        TABLE_ROW   = colors.HexColor("#0D1117")
        TABLE_ALT   = colors.HexColor("#111820")

        rec_color = {"BULLISH": GREEN, "BEARISH": RED, "NEUTRAL": YELLOW}.get(rec, ACCENT)

        styles = getSampleStyleSheet()

        def style(name, **kw):
            s = ParagraphStyle(name, **{"fontName": "Helvetica", "textColor": TEXT, **kw})
            return s

        TITLE   = style("title_s", fontSize=22, textColor=ACCENT, spaceAfter=4, alignment=TA_CENTER, fontName="Helvetica-Bold")
        SUB     = style("sub_s",   fontSize=11, textColor=MUTED,   spaceAfter=2, alignment=TA_CENTER)
        SEC_HDR = style("sec_hdr", fontSize=13, textColor=ACCENT,  spaceBefore=14, spaceAfter=6, fontName="Helvetica-Bold")
        BODY    = style("body_s",  fontSize=10, textColor=TEXT,    spaceAfter=4, leading=15)
        MUTED_S = style("muted_s", fontSize=9,  textColor=MUTED,   spaceAfter=2)
        REC_S   = style("rec_s",   fontSize=18, textColor=rec_color, alignment=TA_CENTER, fontName="Helvetica-Bold", spaceBefore=6, spaceAfter=6)

        def hr():
            return HRFlowable(width="100%", thickness=0.5, color=MUTED, spaceAfter=8, spaceBefore=4)

        def section(title):
            return [hr(), Paragraph(title, SEC_HDR)]

        def metric_table(rows, col_widths=None):
            col_widths = col_widths or [10*cm, 5.5*cm]
            data = [["Metric", "Value"]] + rows
            tbl = Table(data, colWidths=col_widths)
            tbl.setStyle(TableStyle([
                ("BACKGROUND",   (0,0), (-1,0), TABLE_HDR),
                ("TEXTCOLOR",    (0,0), (-1,0), ACCENT),
                ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
                ("FONTSIZE",     (0,0), (-1,-1), 9),
                ("TEXTCOLOR",    (0,1), (-1,-1), TEXT),
                ("BACKGROUND",   (0,1), (-1,-1), TABLE_ROW),
                ("ROWBACKGROUNDS",(0,1),(-1,-1), [TABLE_ROW, TABLE_ALT]),
                ("GRID",         (0,0), (-1,-1), 0.3, MUTED),
                ("LEFTPADDING",  (0,0), (-1,-1), 8),
                ("RIGHTPADDING", (0,0), (-1,-1), 8),
                ("TOPPADDING",   (0,0), (-1,-1), 5),
                ("BOTTOMPADDING",(0,0), (-1,-1), 5),
                ("ALIGN",        (1,0), (1,-1), "RIGHT"),
            ]))
            return tbl

        def _f(v, prefix="", suffix="", na="N/A"):
            if v is None or v == 0.0:
                return na
            if isinstance(v, float):
                return f"{prefix}{v:,.2f}{suffix}"
            return f"{prefix}{v}{suffix}"

        story = []

        # ── Header ──
        story += [
            Spacer(1, 0.3*cm),
            Paragraph("ARA-1  ·  INSTITUTIONAL EQUITY RESEARCH", TITLE),
            Paragraph(f"{ticker}  |  {date_str}  |  Analyst: ARA-1 Autonomous Agent v2.0", SUB),
            Spacer(1, 0.4*cm),
        ]

        # ── Verdict banner ──
        badge = {"BULLISH": "BULLISH  ●  LONG", "BEARISH": "BEARISH  ●  AVOID / SHORT", "NEUTRAL": "NEUTRAL  ●  HOLD / MONITOR"}.get(rec, rec)
        story += [
            Paragraph(f"VERDICT:  {badge}", REC_S),
            Paragraph(f"Confidence: {conf}   |   Valuation: {rj.get('valuation_label','N/A')}", SUB),
            Spacer(1, 0.3*cm),
        ]

        if rj.get("enforced_override"):
            story.append(Paragraph("⚠  Rule-engine override applied — LLM bias corrected by DecisionEngine", MUTED_S))

        # ── Section 1: Executive Summary ──
        story += section("1. EXECUTIVE SUMMARY")
        story.append(Paragraph(rj.get("executive_summary", "N/A"), BODY))

        # ── Section 2: Data Warnings ──
        story += section("2. DATA QUALITY WARNINGS")
        dw = rj.get("data_warnings", [])
        if dw:
            for w in dw:
                story.append(Paragraph(f"• {w}", BODY))
        else:
            story.append(Paragraph("✅  No data quality anomalies detected.", BODY))

        # ── Section 3: Financial Metrics ──
        story += section("3. FINANCIAL METRICS")
        rows = [
            ["Current Market Price",       _f(rj.get("current_price"), "$")],
            ["DCF Intrinsic Value / Share", _f(rj.get("intrinsic_value_per_share"), "$") + "  (DCF)"],
            ["Margin of Safety",            _f(rj.get("margin_of_safety_pct"), suffix="%")],
            ["Valuation Assessment",        rj.get("valuation_label","N/A")],
            ["P/E Ratio (TTM)",             _f(rj.get("pe_ratio"), suffix="x")],
            ["Forward P/E",                 _f(rj.get("forward_pe"), suffix="x")],
            ["EPS (TTM)",                   _f(rj.get("eps_ttm"), "$")],
            ["Annual Revenue (TTM)",        _f(rj.get("revenue_b"), "$", "B")],
            ["Net Income (TTM)",            _f(rj.get("net_income_b"), "$", "B")],
            ["Profit Margin",               _f(rj.get("profit_margin_pct"), suffix="%")],
            ["Revenue Growth YoY",          _f(rj.get("revenue_growth_pct"), suffix="%")],
            ["ROE",                         _f(rj.get("roe_pct"), suffix="%")],
            ["Debt-to-Equity",              _f(rj.get("debt_to_equity"), suffix="x")],
            ["Beta",                        _f(rj.get("beta"))],
            ["Analyst Consensus Target",    _f(rj.get("analyst_target_mean"), "$")],
            ["Upside to Analyst Target",    _f(rj.get("upside_pct"), suffix="%")],
        ]
        story.append(metric_table(rows))

        # ── Section 6: Risk Assessment ──
        story += section("6. RISK ASSESSMENT")
        risks = rj.get("risks", [])
        if risks:
            for r in risks:
                story.append(Paragraph(f"• {r}", BODY))

        # ── Section 9: Investment Thesis ──
        story += section("9. INVESTMENT THESIS")
        if rj.get("bull_case"):
            story.append(Paragraph("🟢 Bull Case:", style("bh", fontSize=10, textColor=GREEN, fontName="Helvetica-Bold")))
            story.append(Paragraph(rj["bull_case"], BODY))
        if rj.get("bear_case"):
            story.append(Paragraph("🔴 Bear Case:", style("rh", fontSize=10, textColor=RED, fontName="Helvetica-Bold")))
            story.append(Paragraph(rj["bear_case"], BODY))

        # ── Section 10: Final Recommendation ──
        story += section("10. FINAL RECOMMENDATION")
        story += [
            Paragraph(f"RECOMMENDATION: {badge}", REC_S),
            Paragraph(f"Confidence: {conf}", SUB),
        ]
        if rj.get("rationale"):
            story.append(Paragraph(f"Rationale: {rj['rationale']}", BODY))

        # ── Data Sources ──
        story += section("DATA SOURCES")
        for s in rj.get("data_sources", []):
            story.append(Paragraph(f"• {s}", MUTED_S))

        # ── Footer note ──
        story += [
            Spacer(1, 0.5*cm),
            hr(),
            Paragraph(
                "This report is generated by ARA-1 Autonomous Financial Research Agent v2.0. "
                "Not financial advice. For informational purposes only.",
                MUTED_S
            ),
        ]

        doc.build(story)
        buf.seek(0)
        filename = f"ARA1_{ticker}_{date_str}.pdf"
        return StreamingResponse(
            buf,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="reportlab not installed. Run: pip install reportlab"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Health check ─────────────────────────────────────────────
@app.get("/api/health")
async def health():
    return {"status": "ok", "agent": "ARA-1 v2.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
