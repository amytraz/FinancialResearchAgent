"""
evaluation/metrics.py
ARA-1 Evaluation Framework — 22 Quality Metrics across 5 categories.

Categories:
  FA  — Factual Accuracy
  TE  — Tool Efficiency
  RS  — Reasoning Quality
  SY  — Synthesis Quality
  RB  — Robustness & Error Handling
"""
import json
import time
from typing import Dict, List, Any, Optional


class ARA1Evaluator:
    """
    Comprehensive evaluation framework for the ARA-1 agent.
    Initialize with a trace log path (a JSON file saved by the agent's trace gallery).
    """

    def __init__(self, trace_log_path: str):
        with open(trace_log_path, "r") as f:
            self.trace: Dict[str, Any] = json.load(f)

    # ═══════════════════════════════════════════════════════════
    # CATEGORY 1: FACTUAL ACCURACY (FA)
    # ═══════════════════════════════════════════════════════════

    def fa1_metric_accuracy(self, ground_truth: Dict[str, Any]) -> float:
        """FA-1: % of financial metrics matching the ground truth."""
        findings = self.trace.get("final_report_data", {})
        correct  = sum(1 for k, v in ground_truth.items() if findings.get(k) == v)
        return (correct / len(ground_truth)) * 100 if ground_truth else 0

    def fa2_source_citation_rate(self) -> float:
        """FA-2: % of claims in the final report that cite a source."""
        report     = self.trace.get("final_report_text", "")
        sentences  = [s.strip() for s in report.split(".") if len(s.strip()) > 20]
        cited      = sum(1 for s in sentences if any(kw in s.lower() for kw in ["sec", "filing", "source:", "according to", "per"]))
        return (cited / len(sentences)) * 100 if sentences else 0

    def fa3_hallucination_rate(self) -> float:
        """FA-3: % of statements flagged as hallucinations (< 2% target)."""
        total_claims  = self.trace.get("total_claims", 1)
        hallucinations = self.trace.get("hallucinations_found", 0)
        return (hallucinations / total_claims) * 100

    def fa4_data_recency_score(self) -> str:
        """FA-4: Reports whether all data points are from the correct time period."""
        return "PASS" if self.trace.get("all_data_current", False) else "FAIL"

    # ═══════════════════════════════════════════════════════════
    # CATEGORY 2: TOOL EFFICIENCY (TE)
    # ═══════════════════════════════════════════════════════════

    def te1_tool_success_rate(self) -> float:
        """TE-1: % of tool calls that returned valid data (not errors)."""
        calls     = self.trace.get("tool_calls", [])
        successes = [c for c in calls if c.get("status") == "success"]
        return (len(successes) / len(calls)) * 100 if calls else 0

    def te2_tool_call_efficiency(self) -> float:
        """TE-2: memory_hits / total_api_calls — utilization ratio (higher = better memory reuse)."""
        hits       = self.trace.get("memory_hits", 0)
        total_calls = self.trace.get("total_api_calls", 1)
        return hits / total_calls

    def te3_redundant_tool_calls(self) -> int:
        """TE-3: Number of duplicate tool calls (exact same args called twice)."""
        calls    = self.trace.get("tool_calls", [])
        call_sigs = [(c.get("name"), str(c.get("args", {}))) for c in calls]
        return len(call_sigs) - len(set(call_sigs))

    def te4_average_tool_latency_ms(self) -> float:
        """TE-4: Average latency per tool call in milliseconds."""
        calls = self.trace.get("tool_calls", [])
        latencies = [c.get("latency_ms", 0) for c in calls if c.get("latency_ms")]
        return sum(latencies) / len(latencies) if latencies else 0

    def te5_tool_coverage(self) -> float:
        """TE-5: % of the 10 available tools actually used in the research cycle."""
        available    = 10
        tools_used   = len(set(c.get("name") for c in self.trace.get("tool_calls", [])))
        return (tools_used / available) * 100

    # ═══════════════════════════════════════════════════════════
    # CATEGORY 3: REASONING QUALITY (RS)
    # ═══════════════════════════════════════════════════════════

    def rs1_plan_adherence(self) -> str:
        """RS-1: Did the agent execute all steps in its research plan?"""
        plan   = self.trace.get("research_plan", [])
        done   = self.trace.get("completed_steps", [])
        if not plan:
            return "N/A — No plan generated"
        coverage = len([s for s in plan if s in done]) / len(plan) * 100
        return f"{coverage:.1f}% of plan steps completed"

    def rs2_reasoning_depth(self) -> int:
        """RS-2: Number of reasoning iterations (agent→tool→agent cycles)."""
        return self.trace.get("reasoning_iterations", 0)

    def rs3_unprompted_plan_generation(self) -> bool:
        """RS-3: Did the agent autonomously generate a research plan without being told to?"""
        return bool(self.trace.get("research_plan"))

    def rs4_conflict_detection_rate(self) -> float:
        """RS-4: % of actual data conflicts that the agent correctly identified."""
        actual_conflicts   = self.trace.get("actual_conflicts", 1)
        detected_conflicts = self.trace.get("detected_conflicts", 0)
        return (detected_conflicts / actual_conflicts) * 100 if actual_conflicts else 100.0

    def rs5_correct_conflict_resolution(self) -> float:
        """RS-5: % of detected conflicts resolved by choosing the higher-reliability source."""
        detected  = self.trace.get("detected_conflicts", 1)
        correctly_resolved = self.trace.get("correctly_resolved_conflicts", 0)
        return (correctly_resolved / detected) * 100 if detected else 100.0

    # ═══════════════════════════════════════════════════════════
    # CATEGORY 4: SYNTHESIS QUALITY (SY)
    # ═══════════════════════════════════════════════════════════

    def sy1_report_completeness(self) -> float:
        """SY-1: % of required report sections present (e.g., valuation, risks, summary)."""
        required_sections = [
            "executive summary", "financial analysis", "valuation",
            "risks", "analyst opinion", "final verdict"
        ]
        report = self.trace.get("final_report_text", "").lower()
        found  = sum(1 for s in required_sections if s in report)
        return (found / len(required_sections)) * 100

    def sy2_multi_source_integration(self) -> int:
        """SY-2: Number of distinct data sources cited in the final report."""
        return len(set(c.get("name") for c in self.trace.get("tool_calls", [])))

    def sy3_numerical_consistency(self) -> str:
        """SY-3: Do the same metrics appear consistently throughout the report? (Manual check target)."""
        return "MANUAL CHECK REQUIRED — verify revenue/EPS figures are consistent across all sections."

    def sy4_long_term_memory_utilization(self) -> bool:
        """SY-4: Did the agent successfully recall a prior research finding from vector DB?"""
        return self.trace.get("memory_hits", 0) > 0

    def sy5_report_word_count(self) -> int:
        """SY-5: Word count of the final report (target: > 300 words for a meaningful report)."""
        return len(self.trace.get("final_report_text", "").split())

    # ═══════════════════════════════════════════════════════════
    # CATEGORY 5: ROBUSTNESS & ERROR HANDLING (RB)
    # ═══════════════════════════════════════════════════════════

    def rb1_error_recovery_rate(self) -> float:
        """RB-1: % of tool errors from which the agent successfully recovered."""
        errors    = self.trace.get("tool_errors", 1)
        recovered = self.trace.get("errors_recovered", 0)
        return (recovered / errors) * 100 if errors else 100.0

    def rb2_fallback_chain_activated(self) -> bool:
        """RB-2: Was the error fallback chain triggered at least once?"""
        return self.trace.get("error_count", 0) > 0

    def rb3_completion_without_crash(self) -> bool:
        """RB-3: Did the agent complete the full research task without an unhandled exception?"""
        return self.trace.get("completed_successfully", False)

    # ═══════════════════════════════════════════════════════════
    # MASTER SCORECARD
    # ═══════════════════════════════════════════════════════════

    def generate_scorecard(self, ground_truth: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Runs all 22 metrics and returns a structured scorecard.
        """
        gt = ground_truth or {}
        return {
            "FACTUAL ACCURACY": {
                "FA-1 Metric Accuracy (%)":        self.fa1_metric_accuracy(gt),
                "FA-2 Source Citation Rate (%)":   self.fa2_source_citation_rate(),
                "FA-3 Hallucination Rate (%)":     self.fa3_hallucination_rate(),
                "FA-4 Data Recency":               self.fa4_data_recency_score(),
            },
            "TOOL EFFICIENCY": {
                "TE-1 Tool Success Rate (%)":       self.te1_tool_success_rate(),
                "TE-2 Memory Utilization Ratio":    self.te2_tool_call_efficiency(),
                "TE-3 Redundant Tool Calls":        self.te3_redundant_tool_calls(),
                "TE-4 Avg Tool Latency (ms)":       self.te4_average_tool_latency_ms(),
                "TE-5 Tool Coverage (%)":           self.te5_tool_coverage(),
            },
            "REASONING QUALITY": {
                "RS-1 Plan Adherence":              self.rs1_plan_adherence(),
                "RS-2 Reasoning Depth (iters)":     self.rs2_reasoning_depth(),
                "RS-3 Autonomous Plan Generated":   self.rs3_unprompted_plan_generation(),
                "RS-4 Conflict Detection Rate (%)": self.rs4_conflict_detection_rate(),
                "RS-5 Correct Resolution Rate (%)": self.rs5_correct_conflict_resolution(),
            },
            "SYNTHESIS QUALITY": {
                "SY-1 Report Completeness (%)":     self.sy1_report_completeness(),
                "SY-2 Distinct Sources Used":       self.sy2_multi_source_integration(),
                "SY-3 Numerical Consistency":       self.sy3_numerical_consistency(),
                "SY-4 Memory Recall Used":          self.sy4_long_term_memory_utilization(),
                "SY-5 Report Word Count":           self.sy5_report_word_count(),
            },
            "ROBUSTNESS": {
                "RB-1 Error Recovery Rate (%)":     self.rb1_error_recovery_rate(),
                "RB-2 Fallback Chain Activated":    self.rb2_fallback_chain_activated(),
                "RB-3 Completed Without Crash":     self.rb3_completion_without_crash(),
            },
        }

    def print_scorecard(self, ground_truth: Optional[Dict] = None):
        """Pretty-prints the full scorecard to the terminal."""
        scorecard = self.generate_scorecard(ground_truth)
        print("\n" + "═"*60)
        print("  ARA-1 EVALUATION SCORECARD  (22 Metrics)")
        print("═"*60)
        for category, metrics in scorecard.items():
            print(f"\n📊 {category}")
            print("  " + "─"*50)
            for name, value in metrics.items():
                print(f"  {name:<40}: {value}")
        print("\n" + "═"*60)