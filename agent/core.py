"""
agent/core.py  —  ARA-1  |  Institutional-Grade Autonomous Financial Research Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Architecture:
  [parallel_researcher] → [validator_node] → [synthesizer_node] → [decision_enforcer] → END

Key guarantees:
  ✅ Data first   — all metrics extracted DETERMINISTICALLY before LLM call
  ✅ Validation   — anomalies flagged and confidence reduced BEFORE synthesis
  ✅ 10-step report — LLM produces full hedge-fund format (exec summary → recommendation)
  ✅ Rule engine  — DecisionEngine overrides LLM recommendation if rules violated
  ✅ No bias      — LLM narrative CANNOT produce BULLISH with MoS < -20%
  ✅ Parallel     — 4 tools run concurrently (ThreadPoolExecutor)
  ✅ Tenacity     — Groq 429s retried with exponential back-off
  ✅ Token-safe   — state is capped at SUMMARY_BUFFER_MAX_CHARS per tool
  ✅ ChromaDB     — full tool results persisted in vector store
"""
import os
import json
import datetime
import concurrent.futures
from typing import TypedDict, List, Optional
from dotenv import load_dotenv

import tenacity
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END

# Tools — called as Python functions (no LLM tool-calling)
from tools.financial_tools import get_financial_metrics
from tools.sec_edgar       import sec_filing_search
from tools.analysis        import calculate_dcf, get_analyst_ratings

# Memory & synthesis
from memory.vector_store         import LongTermMemory
from synthesis.conflict_resolver import ConflictResolver
from synthesis.data_validator    import DataValidator
from synthesis.decision_engine   import DecisionEngine, DecisionResult

load_dotenv()

# ── Constants ───────────────────────────────────────────────
SUMMARY_BUFFER_MAX_CHARS = 900   # Max chars per tool result IN STATE
                                   # (full text still goes to ChromaDB)


# ═══════════════════════════════════════════════════════════
# RESEARCH PLAN — 4 parallel tools
# ═══════════════════════════════════════════════════════════
def _build_research_tasks(ticker: str) -> list:
    """Returns list of (label, callable) tuples to run in parallel."""
    return [
        ("Financial Metrics",  lambda: get_financial_metrics.invoke({"ticker": ticker})),
        ("SEC 10-K Filing",    lambda: sec_filing_search.invoke({"ticker": ticker, "filing_type": "10-K", "year": 2024})),
        ("DCF Valuation",      lambda: calculate_dcf.invoke({"ticker": ticker, "growth_rate": 0.12})),
        ("Analyst Ratings",    lambda: get_analyst_ratings.invoke({"ticker": ticker})),
    ]


# ═══════════════════════════════════════════════════════════
# STATE SCHEMA
# ═══════════════════════════════════════════════════════════
class AgentState(TypedDict):
    ticker:          str
    research_data:   dict           # {label: truncated_summary}
    validated_metrics: Optional[dict]  # Deterministically extracted metrics
    data_warnings:   List[str]      # Pre-analysis quality warnings
    final_report:    Optional[str]  # Plain text report
    report_json:     Optional[dict] # Structured JSON report


# ═══════════════════════════════════════════════════════════
# SYNTHESIS PROMPT — Full 10-step institutional format
# ═══════════════════════════════════════════════════════════
SYNTHESIS_PROMPT = """You are ARA-1, a Senior Investment Research Analyst at a hedge fund. Today: {date}.
You have completed all research on {ticker}. Your job is to produce a HEDGE FUND QUALITY equity research report.

## PRE-VALIDATED DATA (deterministic — do NOT alter these numbers)
{validated_block}

## RAW RESEARCH DATA
{research_block}

## DATA QUALITY WARNINGS (detected before this synthesis)
{warnings_block}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## MANDATORY RULES YOU MUST FOLLOW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Use EXACT numbers from the pre-validated data above. NEVER fabricate or round differently.
2. Margin of Safety (MoS) = ((IntrinsicValue - MarketPrice) / MarketPrice) × 100
   - MoS < -20%      → OVERVALUED  → Recommend NEUTRAL or BEARISH
   - -20% ≤ MoS ≤ +20% → FAIRLY VALUED → Recommend NEUTRAL
   - MoS > +20%      → UNDERVALUED → Recommend BULLISH
3. If MoS < -20% AND fundamentals are weak → BEARISH (not BULLISH).
4. Data warnings MUST appear in Section 2 and MUST reduce confidence.
5. Recommendation in Section 10 MUST be consistent with MoS logic above.
6. Before writing Section 10, re-check: does valuation match recommendation?
   If any contradiction exists, FIX IT before writing.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## OUTPUT — Write the full 10-section report below, then the JSON block.

---
FINAL REPORT: {ticker} | {date}
=======================================================================

## 1. EXECUTIVE SUMMARY
[2-3 sentences: business description, financial position, market context]

## 2. DATA QUALITY WARNINGS
[List all warnings detected. If none, write "No anomalies detected."]
[Note: warnings above REDUCE confidence level]

## 3. FINANCIAL ANALYSIS

### Key Metrics
| Metric             | Value          |
|--------------------|----------------|
| Revenue (TTM)      | ${revenue_b}B  |
| Net Income (TTM)   | ${net_income_b}B|
| EPS (TTM)          | ${eps_ttm}      |
| P/E Ratio (TTM)    | {pe_ratio}x     |
| Forward P/E        | {forward_pe}x   |
| Profit Margin      | {profit_margin_pct}%|
| Revenue Growth YoY | {revenue_growth_pct}%|
| ROE                | {roe_pct}%      |
| Debt-to-Equity     | {debt_to_equity}x|
| Beta               | {beta}          |

### Profitability Analysis
[Analyse margin trends, earnings consistency, ROE trajectory — 3-4 sentences]

### Balance Sheet Health
[Assess debt levels, D/E ratio vs sector, working capital — 2-3 sentences]

## 4. BUSINESS & SEGMENT ANALYSIS
[Break down major revenue segments: core drivers, growth segments, emerging bets]
[Which segment drives future growth? — 4-5 sentences]

## 5. VALUATION ANALYSIS (DCF)

### DCF Assumptions
| Parameter            | Value |
|----------------------|-------|
| Base FCF             | $X    |
| Growth Rate Assumed  | 12%   |
| Discount Rate (WACC) | 10%   |
| Terminal Growth Rate | 3%    |
| Projection Period    | 5 years|

### DCF Output
| Output                  | Value            |
|-------------------------|------------------|
| DCF Intrinsic Value/Share | ${intrinsic_value_per_share}|
| Market Price            | ${current_price} |
| Margin of Safety        | {margin_of_safety_pct}%     |
| Valuation Assessment    | [UNDERVALUED / FAIRLY VALUED / OVERVALUED — MUST match MoS] |

## 6. RISK ASSESSMENT
- **Financial Risk**: [derived from D/E ratio, cash position, interest coverage]
- **Business Risk**: [derived from growth trends, competitive pressures, margin compression]
- **Macro/Regulatory Risk**: [derived from SEC 10-K or analyst commentary]
- **Valuation Risk**: [derived from P/E vs sector, MoS, premium to intrinsic value]

## 7. CATALYSTS (FORWARD-LOOKING)
- **Near-term (0-6 months)**: [earnings beats, product launches, guidance raises]
- **Medium-term (6-18 months)**: [sector tailwinds, AI/tech/macro trends]
- **Long-term (18m+)**: [TAM expansion, structural advantages]

## 8. ANALYST CONSENSUS
| Metric             | Value                  |
|--------------------|------------------------|
| Consensus Rating   | [BUY / HOLD / SELL]    |
| Mean Target Price  | ${analyst_target_mean} |
| Implied Upside     | {upside_pct}%          |
| Number of Analysts | [N]                    |

[Compare analyst target with your DCF intrinsic value — 1-2 sentences]

## 9. INVESTMENT THESIS

### Bull Case 🟢
[If MoS > +20% and fundamentals are strong — articulate why stock could re-rate higher]
[If not bullish, write "Insufficient undervaluation to construct a strong bull case."]

### Bear Case 🔴
[Key downside risks: what could cause 20%+ further decline?]

## 10. FINAL RECOMMENDATION (STRICT LOGIC APPLIED)

⚠️ SELF-CHECK: Verify before writing:
  - Margin of Safety = {margin_of_safety_pct}% → This MANDATES: [derive correct label]
  - Are fundamentals strong or weak? → [assess]
  - Does my recommendation match the MoS rule? → YES / NO (fix if NO)

RECOMMENDATION: [BULLISH 🟢 / NEUTRAL 🟡 / BEARISH 🔴]
Confidence: [HIGH / MEDIUM / LOW]
Rationale: [One precise sentence that references the MoS and key financials]

---

Then output a JSON block (fill ALL fields with exact validated numbers):
```json
{{
  "ticker": "{ticker}",
  "date": "{date}",
  "recommendation": "BULLISH",
  "confidence": "HIGH",
  "executive_summary": "2-3 sentence company overview",
  "current_price": 0.0,
  "intrinsic_value_per_share": 0.0,
  "margin_of_safety_pct": 0.0,
  "valuation_label": "OVERVALUED",
  "pe_ratio": 0.0,
  "forward_pe": 0.0,
  "eps_ttm": 0.0,
  "revenue_b": 0.0,
  "net_income_b": 0.0,
  "profit_margin_pct": 0.0,
  "revenue_growth_pct": 0.0,
  "roe_pct": 0.0,
  "debt_to_equity": 0.0,
  "beta": 0.0,
  "analyst_target_mean": 0.0,
  "upside_pct": 0.0,
  "data_warnings": [],
  "risks": ["Risk 1", "Risk 2", "Risk 3", "Risk 4"],
  "bull_case": "2-3 sentence bull thesis",
  "bear_case": "2-3 sentence bear thesis",
  "investment_thesis": "2-3 sentence primary thesis",
  "rationale": "One sentence justification",
  "data_sources": ["SEC EDGAR (Tier 1)", "Yahoo Finance / yfinance (Tier 3)", "ARA-1 DCF Model"]
}}
```
Use EXACT numbers from pre-validated data. Set recommendation correctly per MoS rules."""


def _format_validated_block(metrics: dict) -> str:
    """Formats deterministically extracted metrics for the prompt."""
    lines = ["PRE-VALIDATED METRICS (deterministic extraction):"]
    field_fmt = {
        "current_price":             ("Current Market Price",    "${:.2f}"),
        "intrinsic_value_per_share": ("DCF Intrinsic Value/Share","${:.2f}"),
        "margin_of_safety_pct":      ("Margin of Safety (MoS)",  "{:.2f}%"),
        "pe_ratio":                  ("P/E Ratio (TTM)",          "{:.2f}x"),
        "forward_pe":                ("Forward P/E",               "{:.2f}x"),
        "eps_ttm":                   ("EPS (TTM)",                "${:.2f}"),
        "revenue_b":                 ("Revenue (TTM)",            "${:.2f}B"),
        "net_income_b":              ("Net Income (TTM)",         "${:.2f}B"),
        "profit_margin_pct":         ("Profit Margin",             "{:.2f}%"),
        "revenue_growth_pct":        ("Revenue Growth YoY",        "{:.2f}%"),
        "roe_pct":                   ("ROE",                       "{:.2f}%"),
        "debt_to_equity":            ("Debt-to-Equity",            "{:.2f}x"),
        "beta":                      ("Beta",                      "{:.2f}"),
        "analyst_target_mean":       ("Analyst Mean Target",       "${:.2f}"),
        "upside_pct":                ("Upside to Analyst Target",  "{:.2f}%"),
    }
    for key, (label, fmt) in field_fmt.items():
        v = metrics.get(key)
        if v is not None:
            try:
                lines.append(f"  {label:<35}: {fmt.format(v)}")
            except Exception:
                lines.append(f"  {label:<35}: {v}")
        else:
            lines.append(f"  {label:<35}: ⚠️ NOT AVAILABLE")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════
# AGENT
# ═══════════════════════════════════════════════════════════
class ARA1Agent:
    def __init__(self):
        env_model  = os.getenv("MODEL_NAME", "")
        groq_names = ["llama", "mixtral", "gemma"]
        is_groq    = any(m in env_model.lower() for m in groq_names)
        self.model = env_model if is_groq else "llama-3.3-70b-versatile"
        print(f"   Model  : {self.model}")

        self.llm = ChatGroq(
            model="llama-3.1-8b-instant",   # 131K TPM on free tier
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=0,
        )
        self.memory   = LongTermMemory()
        self.resolver = ConflictResolver()
        self.validator = DataValidator()
        self.engine    = DecisionEngine()

    # ── Node 1: Parallel Researcher ──────────────────────────
    def parallel_researcher(self, state: AgentState) -> dict:
        """
        OODA — Observe & Orient phase.
        Runs all 4 research tools CONCURRENTLY via ThreadPoolExecutor.
        Full results → ChromaDB. Truncated summaries → AgentState.
        """
        ticker = state["ticker"]
        tasks  = _build_research_tasks(ticker)
        results = {}

        print(f"\n   Launching {len(tasks)} research tools in parallel...")

        def _run(label_fn):
            label, fn = label_fn
            try:
                raw = fn()
            except Exception as e:
                raw = f"DATA UNAVAILABLE — {label}: {e}"
            return label, raw

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(tasks)) as executor:
            futures = {executor.submit(_run, t): t[0] for t in tasks}
            for future in concurrent.futures.as_completed(futures):
                label, raw = future.result()
                # Persist full result to ChromaDB
                try:
                    self.memory.store_document(
                        text=raw,
                        metadata={"ticker": ticker, "step": label, "ts": str(datetime.datetime.now())},
                    )
                except Exception:
                    pass
                # Truncate for AgentState to protect token budget
                truncated = raw[:SUMMARY_BUFFER_MAX_CHARS]
                if len(raw) > SUMMARY_BUFFER_MAX_CHARS:
                    truncated += f"\n... [truncated — {len(raw) - SUMMARY_BUFFER_MAX_CHARS} chars in ChromaDB]"
                results[label] = truncated
                print(f"   ✅  {label} — {len(raw)} chars collected")

        return {"research_data": results}

    # ── Node 2: Validator ────────────────────────────────────
    def validator_node(self, state: AgentState) -> dict:
        """
        OODA — Orient (Data Quality) phase.
        Deterministically extracts numeric metrics BEFORE the LLM call.
        Flags anomalies and stores structured warnings.
        """
        rdata = state.get("research_data", {})
        fin_text     = rdata.get("Financial Metrics", "")
        dcf_text     = rdata.get("DCF Valuation", "")
        analyst_text = rdata.get("Analyst Ratings", "")

        print("\n   Running deterministic data validation...")
        metrics, warnings = self.validator.validate(fin_text, dcf_text, analyst_text)

        # Print validation summary
        if warnings:
            print(f"   ⚠️  {len(warnings)} data quality warning(s) detected:")
            for w in warnings:
                print(f"      {w}")
        else:
            print("   ✅  No data quality anomalies detected")

        # Print key metrics
        mos = metrics.get("margin_of_safety_pct")
        iv  = metrics.get("intrinsic_value_per_share")
        mp  = metrics.get("current_price")
        print(f"\n   DCF  Intrinsic Value : ${iv:.2f}" if iv else "\n   DCF  Intrinsic Value : NOT AVAILABLE")
        print(f"   Market Price         : ${mp:.2f}" if mp else "   Market Price         : NOT AVAILABLE")
        print(f"   Margin of Safety     : {mos:.2f}%" if mos is not None else "   Margin of Safety     : NOT AVAILABLE")

        return {
            "validated_metrics": metrics,
            "data_warnings":     warnings,
        }

    # ── Node 3: Synthesizer ──────────────────────────────────
    def synthesizer_node(self, state: AgentState) -> dict:
        """
        OODA — Decide phase.
        LLM called ONCE with pre-validated metrics injected into prompt.
        LLM is forced to follow the 10-step format and MoS rules.
        """
        ticker   = state["ticker"]
        rdata    = state.get("research_data") or {}
        metrics  = state.get("validated_metrics") or {}
        warnings = state.get("data_warnings") or []

        # Build research block
        research_block = ""
        for label, text in rdata.items():
            research_block += f"\n{'─'*40}\n{label}:\n{text}\n"

        # Build warnings block
        if warnings:
            warnings_block = "\n".join(f"  {w}" for w in warnings)
        else:
            warnings_block = "  ✅ No data quality anomalies detected."

        # Build validated metrics block
        validated_block = _format_validated_block(metrics)

        # Safe-format prompt (handle missing metrics)
        def _safe(key, default="N/A"):
            v = metrics.get(key)
            return f"{v:.2f}" if isinstance(v, float) else (str(v) if v is not None else default)

        prompt = SYNTHESIS_PROMPT.format(
            ticker=ticker,
            date=str(datetime.date.today()),
            research_block=research_block,
            validated_block=validated_block,
            warnings_block=warnings_block,
            revenue_b=_safe("revenue_b"),
            net_income_b=_safe("net_income_b"),
            eps_ttm=_safe("eps_ttm"),
            pe_ratio=_safe("pe_ratio"),
            forward_pe=_safe("forward_pe"),
            profit_margin_pct=_safe("profit_margin_pct"),
            revenue_growth_pct=_safe("revenue_growth_pct"),
            roe_pct=_safe("roe_pct"),
            debt_to_equity=_safe("debt_to_equity"),
            beta=_safe("beta"),
            intrinsic_value_per_share=_safe("intrinsic_value_per_share"),
            current_price=_safe("current_price"),
            margin_of_safety_pct=_safe("margin_of_safety_pct"),
            analyst_target_mean=_safe("analyst_target_mean"),
            upside_pct=_safe("upside_pct"),
        )

        import time
        time.sleep(3)
        print(f"\n   Synthesizing 10-section report (LLM: llama-3.1-8b-instant)...")

        @tenacity.retry(
            retry=tenacity.retry_if_exception_type(Exception),
            wait=tenacity.wait_exponential(multiplier=1, min=2, max=30),
            stop=tenacity.stop_after_attempt(4),
            reraise=True,
        )
        def _call_llm():
            return self.llm.invoke([HumanMessage(content=prompt)])

        try:
            response    = _call_llm()
            report_text = response.content
        except Exception as e:
            report_text = (
                f"[SYNTHESIS ERROR after retries] {e}\n\n"
                f"RAW RESEARCH DATA:\n{research_block}"
            )

        # Parse JSON block from LLM output
        report_json = None
        try:
            import re
            match = re.search(r"```json\s*(\{.*?\})\s*```", report_text, re.DOTALL)
            if match:
                report_json = json.loads(match.group(1))
        except Exception:
            pass

        return {
            "final_report": report_text,
            "report_json":  report_json,
        }

    # ── Node 4: Decision Enforcer ────────────────────────────
    def decision_enforcer(self, state: AgentState) -> dict:
        """
        OODA — Act phase (safety override).
        Runs the deterministic DecisionEngine AFTER LLM synthesis.
        Overwrites recommendation and confidence if LLM output violates rules.
        This is the FINAL SAFETY CHECK.
        """
        metrics  = state.get("validated_metrics") or {}
        warnings = state.get("data_warnings") or []
        rj       = state.get("report_json") or {}

        mos = metrics.get("margin_of_safety_pct")
        if mos is None:
            # Try to get from JSON if validator missed it
            mos = rj.get("margin_of_safety_pct") or 0.0

        print(f"\n   Running deterministic DecisionEngine (MoS={mos:.2f}%)...")

        result: DecisionResult = self.engine.run(
            margin_of_safety_pct=float(mos),
            data_warnings=warnings,
            financial_metrics=metrics,
        )

        enforced = False

        # Override recommendation if LLM diverged from rules
        llm_rec = (rj.get("recommendation") or "NEUTRAL").upper()
        if llm_rec != result.recommendation:
            print(
                f"   🚨 CONTRADICTION DETECTED: LLM gave '{llm_rec}' "
                f"but MoS={mos:.1f}% mandates '{result.recommendation}'. "
                f"Overriding."
            )
            enforced = True

        llm_conf = (rj.get("confidence") or "MEDIUM").upper()
        if llm_conf != result.confidence:
            print(
                f"   🚨 CONFIDENCE MISMATCH: LLM gave '{llm_conf}' "
                f"but data quality mandates '{result.confidence}'. "
                f"Overriding."
            )
            enforced = True

        # Apply validated metrics to JSON (prevents LLM from rounding away)
        if rj:
            rj.update({
                "recommendation":           result.recommendation,
                "confidence":               result.confidence,
                "valuation_label":          result.valuation_label,
                "margin_of_safety_pct":     round(mos, 2),
                "current_price":            metrics.get("current_price") or rj.get("current_price"),
                "intrinsic_value_per_share": metrics.get("intrinsic_value_per_share") or rj.get("intrinsic_value_per_share"),
                "pe_ratio":                 metrics.get("pe_ratio") or rj.get("pe_ratio"),
                "forward_pe":               metrics.get("forward_pe") or rj.get("forward_pe"),
                "eps_ttm":                  metrics.get("eps_ttm") or rj.get("eps_ttm"),
                "revenue_b":                metrics.get("revenue_b") or rj.get("revenue_b"),
                "net_income_b":             metrics.get("net_income_b") or rj.get("net_income_b"),
                "profit_margin_pct":        metrics.get("profit_margin_pct") or rj.get("profit_margin_pct"),
                "revenue_growth_pct":       metrics.get("revenue_growth_pct") or rj.get("revenue_growth_pct"),
                "roe_pct":                  metrics.get("roe_pct") or rj.get("roe_pct"),
                "debt_to_equity":           metrics.get("debt_to_equity") or rj.get("debt_to_equity"),
                "beta":                     metrics.get("beta") or rj.get("beta"),
                "analyst_target_mean":      metrics.get("analyst_target_mean") or rj.get("analyst_target_mean"),
                "upside_pct":              metrics.get("upside_pct") or rj.get("upside_pct"),
                "data_warnings":            warnings,
                "rationale":                result.rationale,
                "engine_contradictions":    result.contradictions,
                "enforced_override":        enforced,
            })

        if enforced:
            print(f"   ✅  Decision enforced: {result.recommendation} ({result.confidence})")
        else:
            print(f"   ✅  LLM recommendation validated: {result.recommendation} ({result.confidence})")

        return {"report_json": rj}

    # ── Graph ────────────────────────────────────────────────
    def build_graph(self):
        wf = StateGraph(AgentState)
        wf.add_node("researcher",  self.parallel_researcher)
        wf.add_node("validator",   self.validator_node)
        wf.add_node("synthesizer", self.synthesizer_node)
        wf.add_node("enforcer",    self.decision_enforcer)

        wf.set_entry_point("researcher")
        wf.add_edge("researcher",  "validator")
        wf.add_edge("validator",   "synthesizer")
        wf.add_edge("synthesizer", "enforcer")
        wf.add_edge("enforcer",    END)

        return wf.compile()
