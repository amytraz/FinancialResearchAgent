"""
main.py  —  ARA-1 CLI Entry Point
Usage:
  python main.py NVDA        (single ticker via arg)
  python main.py             (interactive prompt)
"""
import os
import sys
import json
import warnings
import datetime

# Force UTF-8 output on Windows (fixes UnicodeEncodeError with box-drawing chars)
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

# ── Suppress HuggingFace / tokenizer noise BEFORE any imports ──
os.environ["TOKENIZERS_PARALLELISM"]       = "false"
os.environ["TRANSFORMERS_VERBOSITY"]       = "error"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
warnings.filterwarnings("ignore")

from agent.core import ARA1Agent


# ═══════════════════════════════════════════════════════════
# TERMINAL REPORT RENDERER
# ═══════════════════════════════════════════════════════════
def _wrap(text: str, width: int = 62, indent: str = "  ") -> str:
    """Word-wraps text to width, indented."""
    words, line, out = text.split(), "", []
    for w in words:
        if len(line) + len(w) + 1 > width:
            out.append(indent + line)
            line = w
        else:
            line = (line + " " + w).strip()
    if line:
        out.append(indent + line)
    return "\n".join(out)


def _print_terminal_report(ticker: str, rj: dict):
    """Renders the full institutional report in the terminal."""
    DIV  = "═" * 70
    THIN = "─" * 70
    SEP  = "─" * 50

    rec    = (rj.get("recommendation") or "NEUTRAL").upper()
    conf   = (rj.get("confidence") or "N/A").upper()
    badge_map = {
        "BULLISH": "BULLISH  🟢  [LONG]",
        "BEARISH": "BEARISH  🔴  [AVOID / SHORT]",
        "NEUTRAL": "NEUTRAL  🟡  [HOLD / MONITOR]",
    }
    badge = badge_map.get(rec, f"{rec}")
    val_label = rj.get("valuation_label", "")
    enforced  = rj.get("enforced_override", False)

    print(f"\n{DIV}")
    print(f"  ARA-1  ·  INSTITUTIONAL EQUITY RESEARCH REPORT")
    print(f"  Ticker   : {ticker.upper()}")
    print(f"  Date     : {rj.get('date', str(datetime.date.today()))}")
    print(f"  Analyst  : ARA-1 Autonomous Research Agent v2.0")
    print(DIV)
    print(f"  VERDICT  : {badge}")
    print(f"  CONF.    : {conf}")
    print(f"  VALUATION: {val_label}")
    if enforced:
        print(f"  ⚠️  NOTE  : Rule-engine override applied (LLM bias corrected)")
    print(THIN)

    # ── Section 2: Data Quality Warnings ──────────────────
    dw = rj.get("data_warnings", [])
    if dw:
        print(f"\n  ── SECTION 2 · DATA QUALITY WARNINGS ──")
        print(f"  {SEP}")
        for w in dw:
            print(f"  {w}")
    else:
        print(f"\n  ── SECTION 2 · DATA QUALITY  ──  ✅ No anomalies")

    # ── Section 3: Key Financial Metrics ──────────────────
    print(f"\n  ── SECTION 3 · KEY FINANCIAL METRICS ──")
    print(f"  {SEP}")
    print(f"  {'Metric':<32} {'Value':>20}")
    print(f"  {'-'*32} {'-'*20}")

    def _fmt_val(v, prefix="", suffix="", na="N/A"):
        if v is None or v == 0.0:
            return na
        if isinstance(v, float):
            return f"{prefix}{v:,.2f}{suffix}"
        return f"{prefix}{v}{suffix}"

    rows = [
        ("Current Market Price",        _fmt_val(rj.get("current_price"), "$")),
        ("DCF Intrinsic Value / Share",  _fmt_val(rj.get("intrinsic_value_per_share"), "$") + "  (DCF)"),
        ("Margin of Safety",             _fmt_val(rj.get("margin_of_safety_pct"), suffix="%")),
        ("Valuation Assessment",         rj.get("valuation_label", "N/A")),
        ("P/E Ratio (TTM)",              _fmt_val(rj.get("pe_ratio"), suffix="x")),
        ("Forward P/E",                  _fmt_val(rj.get("forward_pe"), suffix="x")),
        ("EPS (TTM)",                    _fmt_val(rj.get("eps_ttm"), "$")),
        ("Annual Revenue (TTM)",         _fmt_val(rj.get("revenue_b"), "$", "B")),
        ("Net Income (TTM)",             _fmt_val(rj.get("net_income_b"), "$", "B")),
        ("Profit Margin",                _fmt_val(rj.get("profit_margin_pct"), suffix="%")),
        ("Revenue Growth YoY",           _fmt_val(rj.get("revenue_growth_pct"), suffix="%")),
        ("ROE",                          _fmt_val(rj.get("roe_pct"), suffix="%")),
        ("Debt-to-Equity",               _fmt_val(rj.get("debt_to_equity"), suffix="x")),
        ("Beta",                         _fmt_val(rj.get("beta"))),
        ("Analyst Consensus Target",     _fmt_val(rj.get("analyst_target_mean"), "$")),
        ("Upside to Analyst Target",     _fmt_val(rj.get("upside_pct"), suffix="%")),
    ]
    for label, val in rows:
        print(f"  {label:<32} {str(val):>20}")

    # ── Section 1: Executive Summary ──────────────────────
    summary = rj.get("executive_summary", "")
    if summary:
        print(f"\n  ── SECTION 1 · EXECUTIVE SUMMARY ──")
        print(f"  {SEP}")
        print(_wrap(summary))

    # ── Section 6: Risk Assessment ────────────────────────
    risks = rj.get("risks", [])
    if risks:
        print(f"\n  ── SECTION 6 · RISK ASSESSMENT ──")
        print(f"  {SEP}")
        for i, r in enumerate(risks, 1):
            print(f"  {i}. {r}")

    # ── Section 9: Investment Thesis ──────────────────────
    bull = rj.get("bull_case", "")
    bear = rj.get("bear_case", "")
    thesis = rj.get("investment_thesis", rj.get("rationale", ""))

    print(f"\n  ── SECTION 9 · INVESTMENT THESIS ──")
    print(f"  {SEP}")
    if bull:
        print("  🟢 BULL CASE:")
        print(_wrap(bull))
    if bear:
        print("  🔴 BEAR CASE:")
        print(_wrap(bear))
    if thesis and not (bull or bear):
        print(_wrap(thesis))

    # ── Section 10: Final Recommendation ──────────────────
    rationale = rj.get("rationale", "")
    print(f"\n  ── SECTION 10 · FINAL RECOMMENDATION ──")
    print(f"  {SEP}")
    print(f"  RECOMMENDATION : {badge}")
    print(f"  CONFIDENCE     : {conf}")
    if rationale:
        print(f"  RATIONALE      :")
        print(_wrap(rationale))

    # Contradiction log
    contradictions = rj.get("engine_contradictions", [])
    if contradictions:
        print(f"\n  ── ENGINE OVERRIDE LOG ──")
        for c in contradictions:
            print(f"  ⚠️  {c}")

    # Sources
    sources = rj.get("data_sources", [])
    if sources:
        print(f"\n  ── DATA SOURCES ──")
        for s in sources:
            print(f"  · {s}")

    print(f"\n{DIV}\n")


# ═══════════════════════════════════════════════════════════
# MAIN RESEARCH RUNNER
# ═══════════════════════════════════════════════════════════
def run_research(ticker: str):
    print("\n" + "═"*70)
    print(f"  ARA-1  |  AUTONOMOUS FINANCIAL RESEARCH AGENT  v2.0")
    print(f"  Researching  : {ticker.upper()}")
    print(f"  Started      : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("═"*70)

    bot = ARA1Agent()
    app = bot.build_graph()

    initial_state = {
        "ticker":            ticker.upper(),
        "research_data":     {},
        "validated_metrics": None,
        "data_warnings":     [],
        "final_report":      None,
        "report_json":       None,
    }

    config     = {"recursion_limit": 15}
    final_state = None

    print("\n  [1/4] OBSERVE — Parallel Data Collection")
    print("  " + "─"*48)

    for output in app.stream(initial_state, config=config):
        for node_name, value in output.items():
            if node_name == "validator":
                print("\n  [2/4] ORIENT  — Data Validation Complete")
                print("  " + "─"*48)
            elif node_name == "synthesizer":
                print("\n  [3/4] DECIDE  — 10-Section Report Synthesized")
                print("  " + "─"*48)
            elif node_name == "enforcer":
                print("\n  [4/4] ACT     — Deterministic Rules Enforced")
                print("  " + "─"*48)
                final_state = value

    if not final_state or not final_state.get("report_json"):
        print("\n  No report generated. Check ChromaDB for raw research data.")
        return

    rj    = final_state.get("report_json") or {}
    today = str(datetime.date.today())

    # ── Terminal Report (structured) ───────────────────────
    _print_terminal_report(ticker, rj)

    # ── JSON Export ────────────────────────────────────────
    os.makedirs("docs/reports", exist_ok=True)
    json_path = f"docs/reports/{ticker.upper()}_{today}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(rj, f, indent=2, ensure_ascii=False)
    print(f"  [JSON] Saved  → {os.path.abspath(json_path)}")

    # ── JSON to terminal ───────────────────────────────────
    print("\n  STRUCTURED JSON OUTPUT")
    print("  " + "─"*48)
    print(json.dumps(rj, indent=2))

    # ── PDF Export ─────────────────────────────────────────
    print(f"\n  [PDF] Exporting...")
    try:
        from docs.pdf_reporter import generate_pdf
        # Get the full text from final state via LLM output
        report_text = ""
        for output in []:  # Already streamed above; placeholder
            pass
        pdf_path = generate_pdf(
            ticker=ticker,
            report_text=rj.get("investment_thesis", ""),
            research_data={},
            report_json=rj,
        )
        print(f"  [PDF] Saved  → {pdf_path}")
    except Exception as e:
        print(f"  [PDF] Failed → {e}")

    print("\n" + "═"*70)
    print("  RESEARCH COMPLETE")
    print("═"*70 + "\n")


# ═══════════════════════════════════════════════════════════
def main():
    print("\n  ARA-1  Autonomous Financial Research Agent  v2.0")
    print("  " + "─"*48)
    print("  Architecture: Observe → Orient → Decide → Act")
    print("  Rules: Deterministic DCF engine overrides LLM bias")
    print("  " + "─"*48)

    if len(sys.argv) > 1:
        ticker = sys.argv[1].strip().upper()
    else:
        ticker = input("\n  Enter stock ticker (e.g. NVDA, TSLA, AAPL): ").strip().upper()

    if not ticker:
        print("  No ticker provided. Exiting.")
        sys.exit(1)

    run_research(ticker)


if __name__ == "__main__":
    main()
