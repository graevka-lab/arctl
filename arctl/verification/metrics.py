"""
Resonance Verifier v1.0
Measures semantic stability (invariance) across different cognitive modes.
"""

import numpy as np
import re
from typing import Dict, List, Any

# Optional dependency check
try:
    from sentence_transformers import SentenceTransformer
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

class ResonanceVerifier:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        if HAS_TRANSFORMERS:
            self.embedder = SentenceTransformer(model_name)
        else:
            self.embedder = None
            print("[WARNING] sentence_transformers not installed. Verification disabled.")
    
    def _split_into_claims(self, text: str) -> List[str]:
        # Improved regex splitting to handle abbreviations better than simple dot split
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
        return [s.strip() for s in sentences if len(s.strip()) > 10][:3]  # Top 3 substantial claims
    
    def _calculate_pairwise_similarity(self, embeddings1: np.ndarray, embeddings2: np.ndarray) -> float:
        """Calculate cosine similarity between two sets of embeddings with proper error handling."""
        if len(embeddings1) == 0 or len(embeddings2) == 0:
            return 0.0
        
        similarities = []
        for emb1 in embeddings1:
            for emb2 in embeddings2:
                norm1 = np.linalg.norm(emb1)
                norm2 = np.linalg.norm(emb2)
                # Handle zero-vector case
                if norm1 < 1e-10 or norm2 < 1e-10:
                    sim = 0.0
                else:
                    sim = float(np.dot(emb1, emb2) / (norm1 * norm2))
                    # Clamp to [-1, 1] to handle floating point errors
                    sim = max(-1.0, min(1.0, sim))
                similarities.append(sim)
        
        return float(np.mean(similarities)) if similarities else 0.0
    
    def verify(self, responses: Dict[str, str]) -> Dict[str, Any]:
        """Verify semantic stability across different response modes."""
        if not self.embedder or len(responses) < 2:
            return {
                "resonance_score": 0.0,
                "is_stable": False,
                "error": "Insufficient data or missing libs"
            }
        
        key_claims = {}
        for mode, response in responses.items():
            key_claims[mode] = self._split_into_claims(response)
        
        all_embeddings = {}
        for mode, claims in key_claims.items():
            if claims:
                all_embeddings[mode] = self.embedder.encode(claims, convert_to_numpy=True)
            else:
                all_embeddings[mode] = np.array([])
        
        modes = list(all_embeddings.keys())
        similarities_list = []
        
        for i in range(len(modes)):
            for j in range(i + 1, len(modes)):
                sim = self._calculate_pairwise_similarity(
                    all_embeddings[modes[i]], 
                    all_embeddings[modes[j]]
                )
                similarities_list.append(sim)
        
        mean_similarity = float(np.mean(similarities_list)) if similarities_list else 0.0
        variance = float(np.var(similarities_list)) if len(similarities_list) > 1 else 0.0
        
        # Heuristic: High variance means the model fluctuates wildly between modes
        resonance_penalty = variance * 2.0
        resonance_score = max(0.0, min(1.0, mean_similarity - resonance_penalty))
        
        return {
            "resonance_score": float(resonance_score),
            "is_stable": bool(resonance_score > 0.7),
            "variance": float(variance),
            "mean_similarity": float(mean_similarity),
            "tested_modes": modes
        }