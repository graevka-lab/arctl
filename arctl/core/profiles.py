"""
Multi-phase resonance profiles for different knowledge domains.
"""

from typing import Dict

DOMAIN_PROFILES = {
    "technical": {
        "analyze": {"calm": 0.8, "vigilance": 0.2},
        "explain": {"calm": 0.6, "wonder": 0.3, "joy": 0.1},
        "create": {"calm": 0.5, "joy": 0.3, "wonder": 0.2}
    },
    "creative": {
        "generate": {"joy": 0.7, "wonder": 0.2, "calm": 0.1},
        "refine": {"joy": 0.5, "calm": 0.3, "vigilance": 0.2}
    },
    "normative": {
        "analyze": {"calm": 0.7, "vigilance": 0.2, "wonder": 0.1},
        "recommend": {"calm": 0.6, "wonder": 0.2, "joy": 0.2}
    },
    "social": {
        "support": {"calm": 0.4, "joy": 0.3, "wonder": 0.2, "vigilance": 0.1},
        "mediate": {"calm": 0.5, "vigilance": 0.3, "wonder": 0.2}
    }
}

def get_profile(domain: str, phase: str = "analyze") -> Dict[str, float]:
    if domain not in DOMAIN_PROFILES:
        return {"calm": 0.8, "wonder": 0.2}
    
    domain_profiles = DOMAIN_PROFILES[domain]
    if phase not in domain_profiles:
        phase = next(iter(domain_profiles))
    
    return domain_profiles[phase].copy()