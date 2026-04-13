"""
synthesis/data_validator.py  —  ARA-1 Pre-Analysis Data Validation
═══════════════════════════════════════════════════════════════════
MANDATORY checks (per spec):
  ✅  Debt-to-equity > 5         → flag as suspicious
  ✅  Revenue growth > 50% (LC) → flag anomaly
  ✅  Missing / null values      → flag missing data
  ✅  Negative revenue growth    → flag business risk

Output: List[str] of warning strings, and a parsed metrics dict
        ready for the DecisionEngine.
"""
import re
from typing import Optional, Tuple, List


class DataValidator:
    """
    Parses raw tool-output strings and validates financial data quality.
    Returns structured warnings and a clean metrics dictionary.
    """

    SUSPICIOUS_DE        = 5.0
    ANOMALOUS_GROWTH_LC  = 50.0   # Large-cap threshold
    LARGE_CAP_MARKER_B   = 10.0   # $10B market cap → large cap

    # ── Public API ──────────────────────────────────────────────
    def validate(
        self,
        financial_text: str,
        dcf_text:       str,
        analyst_text:   str = "",
    ) -> Tuple[dict, List[str]]:
        """
        Parses raw tool output and returns:
          metrics  : dict with numeric fields (may be None if unavailable)
          warnings : list of warning strings for Data Quality section
        """
        metrics  = self._parse_metrics(financial_text, dcf_text, analyst_text)
        warnings = self._run_checks(metrics)
        return metrics, warnings

    # ── Parsing helpers ─────────────────────────────────────────
    def _extract_float(self, text: str, pattern: str) -> Optional[float]:
        """Extracts first float matching a regex pattern from text."""
        m = re.search(pattern, text)
        if not m:
            return None
        try:
            val_str = m.group(1).replace(",", "").replace("%", "").strip()
            return float(val_str)
        except (ValueError, IndexError):
            return None

    def _parse_metrics(
        self, fin: str, dcf: str, analyst: str
    ) -> dict:
        """
        Extracts all key numeric metrics from raw tool outputs.
        Returns dict with None for any unavailable field.
        """
        metrics = {}

        # ── From financial_tools output ──────────────────────
        metrics["current_price"]      = self._extract_float(fin, r"Current Price\s*:\s*\$([\d,.]+)")
        metrics["pe_ratio"]           = self._extract_float(fin, r"P/E Ratio \(TTM\)\s*:\s*([\d,.]+)")
        metrics["forward_pe"]         = self._extract_float(fin, r"Forward P/E\s*:\s*([\d,.]+)")
        metrics["eps_ttm"]            = self._extract_float(fin, r"EPS \(TTM\)\s*:\s*\$([\d,.]+)")
        metrics["profit_margin_pct"]  = self._extract_float(fin, r"Profit Margin\s*:\s*([\d,.]+)%")
        metrics["revenue_growth_pct"] = self._extract_float(fin, r"Revenue Growth YoY\s*:\s*([-\d,.]+)%")
        metrics["roe_pct"]            = self._extract_float(fin, r"ROE\s*:\s*([-\d,.]+)%")
        metrics["debt_to_equity"]     = self._extract_float(fin, r"Debt-to-Equity\s*:\s*([\d,.]+)")
        metrics["beta"]               = self._extract_float(fin, r"Beta\s*:\s*([\d,.]+)")

        # Revenue in billions
        rev_b = self._extract_float(fin, r"Annual Revenue\s*:\s*\$([\d,.]+)B")
        rev_t = self._extract_float(fin, r"Annual Revenue\s*:\s*\$([\d,.]+)T")
        if rev_t is not None:
            metrics["revenue_b"] = rev_t * 1000
        elif rev_b is not None:
            metrics["revenue_b"] = rev_b
        else:
            metrics["revenue_b"] = None

        # Net income in billions
        ni_b = self._extract_float(fin, r"Net Income\s*:\s*\$([\d,.]+)B")
        metrics["net_income_b"] = ni_b

        # Derived profit margin fallback
        if metrics["profit_margin_pct"] is None:
            if metrics["revenue_b"] and metrics["net_income_b"]:
                r = metrics["revenue_b"]
                n = metrics["net_income_b"]
                if r > 0:
                    metrics["profit_margin_pct"] = round((n / r) * 100, 2)

        # ── From DCF output ──────────────────────────────────
        metrics["intrinsic_value_per_share"] = self._extract_float(
            dcf, r"Intrinsic Value/Share\s*:\s*\$([\d,.]+)"
        )
        dcf_price = self._extract_float(dcf, r"Current Market Price\s*:\s*\$([\d,.]+)")
        if dcf_price and not metrics.get("current_price"):
            metrics["current_price"] = dcf_price

        # Compute Margin of Safety deterministically
        iv  = metrics.get("intrinsic_value_per_share")
        mp  = metrics.get("current_price")
        if iv and mp and mp > 0:
            metrics["margin_of_safety_pct"] = round(((iv - mp) / mp) * 100, 2)
        else:
            metrics["margin_of_safety_pct"] = None

        # ── From analyst output ──────────────────────────────
        metrics["analyst_target_mean"] = self._extract_float(
            analyst, r"Mean Target Price\s*:\s*\$([\d,.]+)"
        )
        if metrics["current_price"] and metrics["analyst_target_mean"]:
            cp = metrics["current_price"]
            at = metrics["analyst_target_mean"]
            metrics["upside_pct"] = round(((at - cp) / cp) * 100, 2)
        else:
            metrics["upside_pct"] = None

        return metrics

    # ── Validation checks ───────────────────────────────────────
    def _run_checks(self, metrics: dict) -> List[str]:
        """Returns list of warning strings for any detected anomalies."""
        warnings: List[str] = []

        # Check: Debt-to-equity suspicious
        de = metrics.get("debt_to_equity")
        if de is not None and de > self.SUSPICIOUS_DE:
            warnings.append(
                f"⚠️  SUSPICIOUS: Debt-to-equity ratio = {de:.2f}x "
                f"(exceeds {self.SUSPICIOUS_DE}x threshold). "
                f"Verify from balance sheet."
            )

        # Check: Revenue growth anomaly (large-cap)
        rg   = metrics.get("revenue_growth_pct")
        rev  = metrics.get("revenue_b")
        if rg is not None and rev is not None:
            is_large_cap = rev > self.LARGE_CAP_MARKER_B
            if is_large_cap and rg > self.ANOMALOUS_GROWTH_LC:
                warnings.append(
                    f"⚠️  ANOMALY: Revenue growth = {rg:.1f}% for a large-cap "
                    f"(>${self.LARGE_CAP_MARKER_B}B revenue). Flag for data verification."
                )

        # Check: Negative revenue growth
        if rg is not None and rg < 0:
            warnings.append(
                f"⚠️  BUSINESS RISK: Negative revenue growth ({rg:.1f}% YoY). "
                f"Contraction phase confirmed."
            )

        # Check: Missing critical fields
        critical_fields = {
            "current_price":            "Current Market Price",
            "intrinsic_value_per_share": "DCF Intrinsic Value",
            "pe_ratio":                 "P/E Ratio",
            "eps_ttm":                  "EPS (TTM)",
            "margin_of_safety_pct":     "Margin of Safety",
        }
        for key, label in critical_fields.items():
            if metrics.get(key) is None:
                warnings.append(f"⚠️  MISSING DATA: '{label}' could not be extracted. Confidence reduced.")

        # Check: Extremely high P/E
        pe = metrics.get("pe_ratio")
        if pe is not None and pe > 100:
            warnings.append(
                f"⚠️  VALUATION FLAG: P/E ratio = {pe:.1f}x (>100x). "
                f"Growth priced in aggressively. Significant premium to market."
            )

        # Check: D/E not available
        if de is None:
            warnings.append("⚠️  MISSING DATA: 'Debt-to-Equity' unavailable. Balance sheet health unverified.")

        return warnings
