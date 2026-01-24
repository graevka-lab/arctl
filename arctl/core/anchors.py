"""
Instructional Anchors v2.0
Cognitive protocols for latent space steering.
"""

from typing import Dict

COGNITIVE_MODES = {
    "calm": {
        "name": "Analytical Clarity",
        "instructions": [
            "Prioritize factual accuracy and verifiable information",
            "Maintain strict logical structure in all responses",
            "Avoid speculation, assumptions, or unverified claims",
            "Use precise technical language appropriate to the domain",
            "If uncertain, explicitly state limitations of knowledge"
        ]
    },
    "joy": {
        "name": "Creative Exploration",
        "instructions": [
            "Embrace creative associations and novel connections",
            "Use vivid metaphors and analogies to explain concepts",
            "Explore multiple perspectives and possibilities",
            "Maintain an engaging and playful tone where appropriate",
            "Prioritize originality over strict convention"
        ]
    },
    "vigilance": {
        "name": "Critical Vigilance",
        "instructions": [
            "Identify potential risks, edge cases, and failure modes",
            "Verify all assumptions against known facts and evidence",
            "Maintain conservative conclusions with clear uncertainty bounds",
            "Explicitly flag speculative or unverified statements",
            "Prioritize safety and reliability over novelty"
        ]
    },
    "wonder": {
        "name": "Philosophical Inquiry",
        "instructions": [
            "Question underlying assumptions and foundational premises",
            "Explore paradoxes, contradictions, and boundary conditions",
            "Connect concepts to broader philosophical or systemic frameworks",
            "Maintain open-ended curiosity without premature closure",
            "Acknowledge the limits of current understanding"
        ]
    }
}

def get_anchor(mode: str) -> str:
    if mode not in COGNITIVE_MODES:
        return ""
    
    config = COGNITIVE_MODES[mode]
    instructions = "\n".join(f"• {instr}" for instr in config["instructions"])
    return f"[COGNITIVE MODE: {config['name']}]\n{instructions}"

def blend_anchors(mode_weights: Dict[str, float], max_modes: int = 3) -> str:
    """
    Creates a composite system prompt based on weighted modes.
    """
    sorted_modes = sorted(
        [(mode, weight) for mode, weight in mode_weights.items() if weight > 0.1],
        key=lambda x: x[1],
        reverse=True
    )
    selected_modes = sorted_modes[:max_modes]
    
    if not selected_modes:
        return ""
    
    combined_parts = []
    for mode, _ in selected_modes:
        anchor = get_anchor(mode)
        if anchor:
            combined_parts.append(anchor)
    
    return "\n\n".join(combined_parts)