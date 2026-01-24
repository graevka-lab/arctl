"""
Lexical Metrics v1.0
Calculates repetition and entropy proxies from raw text.
"""

from typing import List
from ..core.states import RawMetrics

class LexicalMetrics:
    @staticmethod
    def calculate(history_tokens: List[str], window: int = 50) -> RawMetrics:
        if not history_tokens:
            return RawMetrics(0.5, 0.0, 0.0)
            
        recent = history_tokens[-window:]
        
        # 1. Repetition (N-gram overlap)
        ngram_size = 3
        if len(recent) < ngram_size:
            rep_score = 0.0
        else:
            ngrams = [tuple(recent[i:i+ngram_size]) for i in range(len(recent)-ngram_size+1)]
            unique = len(set(ngrams))
            total = len(ngrams)
            rep_score = 1.0 - (unique / total) if total > 0 else 0.0

        # 2. Entropy Proxy (Vocabulary Diversity)
        vocab_size = len(set(recent))
        diversity = vocab_size / len(recent) if recent else 1.0
        ent_score = min(1.0, max(0.0, diversity * 1.5)) 

        return RawMetrics(
            entropy=ent_score,
            divergence=0.0, 
            repetition=rep_score
        )