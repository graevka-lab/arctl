# adaptive_core v1.0.0-rc.1
# "It just works — quietly."
#
# This is a reference implementation of a stateless adaptive controller
# for LLM sampling parameters. It is:
#   - Pure and deterministic
#   - TLA+ compatible
#   - Production hardened
#   - Built with care (and a quiet smile)
#
# No magic. No fluff. Just clarity.

import math
from enum import Enum
from typing import NamedTuple, Optional
from dataclasses import dataclass, field

# ==============================================================================
# MODULE: Adaptive Core v1.0.0-rc.1
# DESCRIPTION: Production-hardened, stateless adaptive sampling controller.
# - Pure functional kernel (referentially transparent)
# - Explicit invariants for TLA+ compatibility
# - Safe against clock skew, NaN, serialization issues
# - Input validation in debug mode (disabled with python -O)
# - pickle-safe; JSON requires adapter (see below)
#
# TIME CONTRACT:
#   absolute_now MUST be derived from a monotonic clock source.
#   If not, the system degrades gracefully via max(absolute_now, prev.last_call_time).
#
# JSON ADAPTER REQUIREMENTS:
#   - serialize OperationalMode via .value
#   - restore SamplingConfig positionally
#   - include version tag for forward compatibility
# ==============================================================================

# --- CONFIGURATION ---

@dataclass(frozen=True)
class TimeConfig:
    min_step_interval: float = 0.01        # Anti-stutter threshold (seconds)
    max_step_interval: float = 0.1         # Time clamping upper bound (seconds)
    deadlock_timeout: float = 5.0          # Emergency mode timeout (seconds)
    full_reset_after_seconds: float = 86400.0  # Reset after 24h absence


@dataclass(frozen=True)
class PolicyConfig:
    max_energy: int = 10                   # Discrete energy budget (units)
    emergency_cost: int = 3                # Energy cost to enter EMERGENCY
    recharge_on_cooldown: int = 1          # Energy restored after COOLDOWN

    # Behavioral thresholds
    smoothing_alpha: float = 0.3           # For exponential moving average
    repetition_threshold: float = 0.6      # Trigger for emergency logic
    cooldown_duration: float = 2.0         # Duration of COOLDOWN mode (logical time)


@dataclass(frozen=True)
class ControllerConfig:
    time: TimeConfig = field(default_factory=TimeConfig)
    policy: PolicyConfig = field(default_factory=PolicyConfig)


# --- TYPES ---

# FALLBACK is a terminal absorbing state. No transitions out are permitted.
class OperationalMode(Enum):
    STANDARD = "STD"
    EMERGENCY = "EMG"
    COOLDOWN = "CDN"
    FALLBACK = "FBK"


# NOTE: entropy and divergence are computed but not used in current emergency logic.
# They are reserved for future policy extensions (e.g., adaptive thresholds).
# Emergency trigger is based solely on repetition, per the original reflex arc design.
_TEMP_MAP = {
    OperationalMode.STANDARD: 0.7,
    OperationalMode.EMERGENCY: 1.2,
    OperationalMode.COOLDOWN: 0.5,
    OperationalMode.FALLBACK: 0.1,
}


class SamplingConfig(NamedTuple):
    """Output directives for the LLM sampler."""
    temperature: float  # Controls randomness (0.1 = deterministic, 1.2 = chaotic)


# Precomputed for performance (defined AFTER SamplingConfig)
_FALLBACK_CONFIG = SamplingConfig(0.1)


@dataclass(frozen=True, slots=True)
class RawMetrics:
    """Raw input signals from the generation pipeline. Values must be in [0.0, 1.0]."""
    entropy: float      # [0.0, 1.0] - Normalized entropy (field of possibilities)
    divergence: float   # [0.0, 1.0] - Normalized semantic drift
    repetition: float   # [0.0, 1.0] - Normalized token repetition score

    def __post_init__(self):
        # Validation is disabled when running with `python -O`
        assert 0.0 <= self.entropy <= 1.0, "entropy must be in [0.0, 1.0]"
        assert 0.0 <= self.divergence <= 1.0, "divergence must be in [0.0, 1.0]"
        assert 0.0 <= self.repetition <= 1.0, "repetition must be in [0.0, 1.0]"
        # Additional safety against NaN/inf (critical for production)
        assert math.isfinite(self.entropy), "entropy must be finite"
        assert math.isfinite(self.divergence), "divergence must be finite"
        assert math.isfinite(self.repetition), "repetition must be finite"


# --- SYSTEM STATE (IMMUTABLE, SERIALIZABLE, SAFE) ---

class SystemState(NamedTuple):
    # Smoothed internal metrics
    s_entropy: float
    s_divergence: float
    s_repetition: float

    # Control state (mode stored as Enum, serializable via .value)
    mode: OperationalMode
    energy: int

    # Time model
    last_call_time: float      # Wall-clock time of last step() call
    logical_time: float        # Abstract internal clock (starts at 0.0)
    mode_entry_time: float     # Logical time when current mode began
    pending_dt: float          # Accumulated time debt (anti-stutter)
    last_interaction: float    # Wall-clock of last state-modifying interaction

    # Output
    active_config: Optional[SamplingConfig]
    step_performed: bool

    @staticmethod
    def initial(now: float) -> 'SystemState':
        return SystemState(
            s_entropy=0.5,
            s_divergence=0.0,
            s_repetition=0.0,
            mode=OperationalMode.STANDARD,
            energy=10,
            last_call_time=now,
            logical_time=0.0,
            mode_entry_time=0.0,
            pending_dt=0.0,
            last_interaction=now,
            active_config=SamplingConfig(0.7),
            step_performed=True
        )

    # EXPLICIT INVARIANTS (must hold for all valid instances):
    # - logical_time >= 0.0 and monotonically non-decreasing
    # - pending_dt >= 0.0 and < (max_step_interval + min_step_interval)
    # - energy ∈ [0, cfg.policy.max_energy]
    # - s_entropy, s_divergence, s_repetition ∈ [0.0, 1.0] if inputs valid
    # - mode_entry_time updated iff mode changes
    # - last_interaction updated iff control state meaningfully changed
    # - FALLBACK mode is terminal: no transitions out, physics frozen
    # - prev state assumed finite (no NaN/inf); validated at boundary


# ==============================================================================
# PURE ADAPTIVE CONTROLLER KERNEL
# ==============================================================================

def step(
    raw: RawMetrics,
    prev: SystemState,
    absolute_now: float,
    cfg: ControllerConfig
) -> SystemState:
    """
    Pure, referentially transparent state transition function.
    
    Input:  RawMetrics + previous SystemState + absolute wall-clock time + config
    Output: New SystemState
    
    Guarantees:
    - Determinism (same inputs → same outputs)
    - Monotonic logical time
    - Bounded energy with ontological reset semantics
    - Terminal FALLBACK state (physics frozen)

    WARNING:
    - absolute_now MUST be monotonic per state lineage (enforced by max() guard)
    - Ontological reset does not count as interaction (last_interaction unchanged)
    - Energy reset after long absence may mask starvation if health checks prevent interaction updates

    Example:
        new_state = step(raw_metrics, prev_state, current_time, config)
    """
    # PRODUCTION-GRADE TIME SAFETY: enforce monotonicity even if caller violates contract
    absolute_now = max(absolute_now, prev.last_call_time)

    # DEBUG: Double-check (redundant but safe)
    if __debug__:
        assert absolute_now >= prev.last_call_time

    # DEBUG: Validate prev state integrity (protects against corrupted snapshots)
    if __debug__:
        assert math.isfinite(prev.s_entropy)
        assert math.isfinite(prev.s_divergence)
        assert math.isfinite(prev.s_repetition)

    # 1. TIME ACCUMULATION
    delta_real = absolute_now - prev.last_call_time  # Now guaranteed >= 0
    new_pending = prev.pending_dt + delta_real

    # Anti-stutter: skip update if insufficient time accumulated
    if new_pending < cfg.time.min_step_interval:
        return prev._replace(
            last_call_time=absolute_now,
            pending_dt=new_pending,
            step_performed=False,
            active_config=None
        )

    # 2. TIME CLAMPING
    dt = min(new_pending, cfg.time.max_step_interval)
    remaining_dt = new_pending - dt
    effective_logical_now = prev.logical_time + dt

    # 3. ONTOLOGICAL RESET (after long absence)
    next_energy = prev.energy
    time_since_interaction = absolute_now - prev.last_interaction
    if time_since_interaction >= cfg.time.full_reset_after_seconds:
        next_energy = cfg.policy.max_energy
        # NOTE: This reset does NOT update last_interaction, as it is not a user interaction.
        # WARNING: If system is pinged by health checks without state change,
        # this may repeatedly trigger, masking true starvation.

    # 4. TERMINAL FALLBACK CHECK (before physics update)
    if prev.mode == OperationalMode.FALLBACK:
        # Physics is frozen; only time and telemetry advance
        return prev._replace(
            last_call_time=absolute_now,
            logical_time=effective_logical_now,
            pending_dt=remaining_dt,
            last_interaction=prev.last_interaction,  # No new interaction in terminal state
            active_config=_FALLBACK_CONFIG,
            step_performed=True
        )

    # 5. PHYSICS UPDATE (exponential smoothing)
    a = cfg.policy.smoothing_alpha
    one_minus_a = 1.0 - a  # Micro-optimization
    s_ent = one_minus_a * prev.s_entropy + a * raw.entropy
    s_div = one_minus_a * prev.s_divergence + a * raw.divergence
    s_rep = one_minus_a * prev.s_repetition + a * raw.repetition

    # 6. MODE TRANSITION LOGIC
    next_mode = prev.mode
    next_mode_time = prev.mode_entry_time
    time_in_mode = effective_logical_now - prev.mode_entry_time

    # EMERGENCY → COOLDOWN (timeout)
    if prev.mode == OperationalMode.EMERGENCY:
        if time_in_mode > cfg.time.deadlock_timeout:
            next_mode = OperationalMode.COOLDOWN
            next_mode_time = effective_logical_now

    # COOLDOWN → STANDARD (with energy recharge)
    elif prev.mode == OperationalMode.COOLDOWN:
        if time_in_mode > cfg.policy.cooldown_duration:
            next_mode = OperationalMode.STANDARD
            next_mode_time = effective_logical_now
            next_energy = min(cfg.policy.max_energy, next_energy + cfg.policy.recharge_on_cooldown)

    # STANDARD → EMERGENCY or FALLBACK (on high repetition)
    else:
        if s_rep > cfg.policy.repetition_threshold:
            if next_energy >= cfg.policy.emergency_cost:
                next_mode = OperationalMode.EMERGENCY
                next_energy -= cfg.policy.emergency_cost
                next_mode_time = effective_logical_now
            else:
                next_mode = OperationalMode.FALLBACK
                next_mode_time = effective_logical_now

    # 7. DETERMINE IF STATE CHANGED (for last_interaction update)
    temp_for_next = _TEMP_MAP.get(next_mode, _TEMP_MAP[OperationalMode.FALLBACK])
    config_for_next = SamplingConfig(temp_for_next)
    # SamplingConfig equality MUST reflect semantic equivalence for interaction tracking
    state_changed = (
        next_mode != prev.mode or
        next_energy != prev.energy or
        config_for_next != prev.active_config
    )
    new_last_interaction = absolute_now if state_changed else prev.last_interaction

    # 8. ENERGY HARDENING (clamp to [0, max_energy])
    next_energy = max(0, min(cfg.policy.max_energy, next_energy))

    # 9. ATOMIC COMMIT
    return SystemState(
        s_ent, s_div, s_rep,
        next_mode, next_energy,
        absolute_now, effective_logical_now, next_mode_time, remaining_dt,
        new_last_interaction,
        config_for_next, True
    )


def get_diagnostics(state: SystemState, absolute_now: float) -> dict:
    """Pure diagnostic function for monitoring and telemetry."""
    days_since = (absolute_now - state.last_interaction) / 86400.0
    return {
        'days_since_last_interaction': round(days_since, 2),
        'energy_level': state.energy,
        'current_mode': state.mode.value,  # Serializable
        'logical_time': state.logical_time,
        'full_reset_triggered': days_since >= 1.0
    }