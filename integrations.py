# arctl/integrations.py
def estimate_metrics_from_text(text: str, query: str) -> dict:
    # Simple heuristics for demo
    repetition = text.count(" ") / max(len(text), 1)
    entropy = len(set(text)) / max(len(text), 1)
    divergence = abs(len(text) - len(query)) / max(len(query), 1)
    return {
        "entropy": min(entropy, 1.0),
        "divergence": min(divergence, 1.0),
        "repetition": min(repetition, 1.0)
    }