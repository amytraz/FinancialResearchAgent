from typing import List, Dict, Any

class ConflictResolver:
    def __init__(self):
        # Professional Hierarchy: Tier 1 is absolute truth
        self.reliability_scores = {
            "sec_filing": 1.0,      # Tier 1: Audited
            "earnings_transcript": 0.8, # Tier 2: Management statement
            "financial_api": 0.7,   # Tier 3: Third-party data
            "major_news": 0.5,      # Tier 4: Reporting
            "web_search": 0.3       # Tier 5: General internet
        }

    def resolve(self, data_points: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Receives multiple data points for the same metric and picks the best one.
        Data format: {"source": "sec_filing", "value": 50.185, "metric": "revenue"}
        """
        if not data_points:
            return None
            
        # Sort by reliability score descending
        sorted_points = sorted(
            data_points, 
            key=lambda x: self.reliability_scores.get(x['source'], 0), 
            reverse=True
        )
        
        winner = sorted_points[0]
        conflicts = sorted_points[1:]
        
        return {
            "final_value": winner['value'],
            "source": winner['source'],
            "has_conflict": len(conflicts) > 0,
            "conflicting_sources": [c['source'] for c in conflicts]
        }