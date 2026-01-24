"""
Uncertainty Scorer v1.0
Detects epistemic insecurity in model outputs.
"""

class UncertaintyScorer:
    MARKERS = {
        "maybe": 0.2, "possibly": 0.2, "perhaps": 0.2,
        "not sure": 0.5, "unclear": 0.4,
        "i think": 0.3, "it seems": 0.3,
        "as an ai": 0.9, "i cannot": 0.9, "sorry": 0.8
    }

    @staticmethod
    def scan(text: str) -> float:
        """Returns a score from 0.0 (Confident) to 1.0 (Refusal/Unknown)."""
        text_lower = text.lower()
        max_score = 0.0
        
        for phrase, weight in UncertaintyScorer.MARKERS.items():
            if phrase in text_lower:
                max_score = max(max_score, weight)
                
        return max_score