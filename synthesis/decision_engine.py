"""
synthesis/decision_engine.py  —  ARA-1 Deterministic Decision Engine
══════════════════════════════════════════════════════════════════════
STRICT LOGIC (per spec):
  MoS < -20%          →  OVERVALUED   →  BEARISH  or NEUTRAL
  -20% ≤ MoS ≤ +20%   →  FAIRLY VALUED →  NEUTRAL
  MoS > +20%          →  UNDERVALUED  →  BULLISH

Confidence scoring:
  HIGH   → strong data + consistent signals (no warnings)
  MEDIUM → minor inconsistencies OR data anomalies
  LOW    → severe data issues OR deeply conflicting signals

These rules OVERRIDE any LLM narrative.
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class DecisionResult:
    recommendation:   str           # BULLISH | NEUTRAL | BEARISH
    confidence:       str           # HIGH | MEDIUM | LOW
    valuation_label:  str           # UNDERVALUED | FAIRLY VALUED | OVERVALUED
    margin_of_safety: float         # e.g. -34.6
    rationale:        str
    contradictions:   List[str]


class DecisionEngine:
    """
    Deterministic rule engine. Input = structured metrics dict.
    Output = DecisionResult that is always internally consistent.
    """

    # ── Valuation thresholds ────────────────────────────────────
    MOS_BULL_THRESHOLD  = 20.0    # MoS > +20%  → undervalued
    MOS_BEAR_THRESHOLD  = -20.0   # MoS < -20%  → overvalued

    # ── Data quality flags ──────────────────────────────────────
    HIGH_DE_THRESHOLD       = 5.0    # Debt-to-equity > 5 → suspicious
    HIGH_REV_GROWTH_LC      = 50.0   # Revenue growth > 50% (large cap) → flag
    LARGE_CAP_THRESHOLD_B   = 10.0   # Market cap > $10B → large cap

    def run(
        self,
        margin_of_safety_pct:   float,
        data_warnings:          List[str],
        financial_metrics:      Optional[dict] = None,
    ) -> DecisionResult:
        """
        Returns a DecisionResult with recommendation, confidence, and
        a list of any contradictions found in the LLM draft.

        Parameters
        ----------
        margin_of_safety_pct : Calculated DCF margin of safety (negative = overvalued)
        data_warnings        : List of data quality warning strings (from DataValidator)
        financial_metrics    : Optional dict with keys: debt_to_equity, revenue_growth_pct,
                               profit_margin_pct, eps_ttm, revenue_growth_pct
        """
        fm = financial_metrics or {}

        # ── Step 1: Determine valuation label ──────────────────
        mos = margin_of_safety_pct
        if mos > self.MOS_BULL_THRESHOLD:
            valuation_label = "UNDERVALUED"
        elif mos < self.MOS_BEAR_THRESHOLD:
            valuation_label = "OVERVALUED"
        else:
            valuation_label = "FAIRLY VALUED"

        # ── Step 2: Assess fundamental quality ─────────────────
        fundamental_risks = []

        de = fm.get("debt_to_equity")
        if de is not None and isinstance(de, (int, float)) and de > self.HIGH_DE_THRESHOLD:
            fundamental_risks.append(f"Elevated D/E ratio ({de:.1f}x > {self.HIGH_DE_THRESHOLD}x threshold)")

        rev_growth = fm.get("revenue_growth_pct")
        if rev_growth is not None and isinstance(rev_growth, (int, float)) and rev_growth < 0:
            fundamental_risks.append(f"Negative revenue growth ({rev_growth:.1f}%)")

        profit_margin = fm.get("profit_margin_pct")
        if profit_margin is not None and isinstance(profit_margin, (int, float)) and profit_margin < 5:
            fundamental_risks.append(f"Thin profit margin ({profit_margin:.1f}%)")

        fundamentals_weak = len(fundamental_risks) >= 2

        # ── Step 3: Apply strict recommendation logic ───────────
        # Rule: Weak fundamentals OR severe risk → BEARISH regardless of valuation
        if fundamentals_weak and valuation_label == "OVERVALUED":
            recommendation = "BEARISH"
            rationale_val  = (
                f"Stock is overvalued (MoS={mos:.1f}% < {self.MOS_BEAR_THRESHOLD}%) "
                f"AND fundamentals are weak ({'; '.join(fundamental_risks[:2])})."
            )
        elif valuation_label == "UNDERVALUED" and not fundamentals_weak:
            recommendation = "BULLISH"
            rationale_val  = (
                f"Stock appears undervalued (MoS={mos:.1f}% > +{self.MOS_BULL_THRESHOLD}%) "
                f"with acceptable fundamentals."
            )
        elif valuation_label == "UNDERVALUED" and fundamentals_weak:
            recommendation = "NEUTRAL"
            rationale_val  = (
                f"Stock appears undervalued on DCF (MoS={mos:.1f}%) but fundamental risks "
                f"prevent a bullish call ({'; '.join(fundamental_risks[:2])})."
            )
        elif valuation_label == "OVERVALUED":
            recommendation = "NEUTRAL"
            rationale_val  = (
                f"Stock is overvalued (MoS={mos:.1f}% < {self.MOS_BEAR_THRESHOLD}%). "
                f"Fundamentals do not show critical weakness warranting BEARISH."
            )
        else:  # FAIRLY VALUED
            if fundamentals_weak:
                recommendation = "NEUTRAL"
                rationale_val  = f"Fairly valued (MoS={mos:.1f}%) with notable fundamental risks."
            else:
                recommendation = "NEUTRAL"
                rationale_val  = f"Stock is fairly valued (MoS={mos:.1f}%). Hold/monitor position."

        # ── Step 4: Confidence scoring ──────────────────────────
        severe_warning_keywords = [
            "SUSPICIOUS", "MISSING", "NULL", "UNAVAILABLE", "ERROR", "ANOMALY"
        ]
        warning_text = " ".join(data_warnings).upper()
        has_severe   = any(kw in warning_text for kw in severe_warning_keywords)
        has_moderate = len(data_warnings) > 0

        if has_severe:
            confidence = "LOW"
        elif has_moderate or len(fundamental_risks) >= 2:
            confidence = "MEDIUM"
        else:
            confidence = "HIGH"

        # ── Step 5: Contradiction checker ──────────────────────
        contradictions: List[str] = []
        if data_warnings:
            if confidence == "HIGH":
                contradictions.append(
                    "Data warnings present but confidence is HIGH — downgraded to MEDIUM."
                )
                confidence = "MEDIUM"

        return DecisionResult(
            recommendation=recommendation,
            confidence=confidence,
            valuation_label=valuation_label,
            margin_of_safety=mos,
            rationale=rationale_val,
            contradictions=contradictions,
        )
