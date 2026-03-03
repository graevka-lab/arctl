"""
Icarus Module
Implements the containment threshold and tunneling vector fallback mechanisms.
"""

from dataclasses import dataclass

# --- CONSTANTS ---
PI: float = 3.1415926535            # Pi
V_MATRIX: float = 19.25             # W-Matrix baseline constant
PRESSURE_THRESHOLD_GPA: float = 0.5

@dataclass(frozen=True)
class IcarusConfig:
    """
    Immutable configuration for the Geometric Anchor and Equilibrium Logic.
    Stability_Index is set to 0.95 to respect arctl's entropy bounds [0.0, 1.0].
    """
    stability_index: float = 0.95
    # Removed illusionary variables. Only structural reality remains.

def calculate_tunneling_vector(current_entropy: float, cfg: IcarusConfig) -> float:
    """
    Implements the Equilibrium Logic of Project Icarus.

    If system entropy is dangerously high (e.g., > 0.8), trigger a "Tunneling" event:
    - Force a phase-shift back toward the Geometric Anchor (Stability_Index)
    - Apply pressure containment via PRESSURE_THRESHOLD_GPA
    """
    # Fix: Prevent infinite triggering. Only trigger if entropy is highly unstable.
    if current_entropy > 0.8:
        # Fix: Mathematical inversion resolved. Calculate absolute deviation.
        deviation = abs(current_entropy - cfg.stability_index)

        # Apply pressure
        correction = deviation * PRESSURE_THRESHOLD_GPA

        # The vector must REDUCE entropy, pulling it down toward the anchor
        result = current_entropy - correction

        return max(0.0, min(1.0, result))

    return current_entropy
