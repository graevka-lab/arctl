"""
Resonance Synthesizer with Multi-Pass Generation capability.
"""

from typing import Dict, Any, Protocol
from arctl.core.anchors import blend_anchors
from arctl.core.profiles import get_profile

class ModelInterface(Protocol):
    """Protocol that any LLM wrapper must implement."""
    def generate(self, prompt: str) -> str:
        ...

class ResonanceSynthesizer:
    def __init__(self, model_interface: ModelInterface):
        self.model = model_interface
    
    def synthesize(self, prompt: str, domain: str, phase: str = "analyze") -> Dict[str, Any]:
        """
        Single-pass generation using a blended profile.
        Efficient for lower-end hardware.
        """
        profile = get_profile(domain, phase)
        anchor = blend_anchors(profile, max_modes=3)
        full_prompt = f"{anchor}\n\nUSER QUERY:\n{prompt}" if anchor else prompt
        primary_response = self.model.generate(full_prompt)
        
        return {
            "response": primary_response,
            "profile": profile,
            "anchor_used": bool(anchor)
        }
    
    def multi_synthesize(self, prompt: str, domain: str, phase: str = "analyze") -> Dict[str, Any]:
        """
        Multi-pass generation for high-fidelity resonance verification.
        Requires more compute.
        """
        modes_to_test = ["calm", "joy", "vigilance", "wonder"]
        responses = {}
        
        for mode in modes_to_test:
            single_profile = {mode: 1.0}
            anchor = blend_anchors(single_profile)
            test_prompt = f"{anchor}\n\nUSER QUERY:\n{prompt}" if anchor else prompt
            responses[mode] = self.model.generate(test_prompt)
        
        return {
            "responses": responses,
            "domain": domain,
            "phase": phase
        }