# core v1.3 (Chronos T-SPIRAL + Energy-Conservative Reset + Icarus)

"""
ARCTL Kernel v1.3.1
Integrated with the Icarus Stability Anchor.

The Hard Core of the adaptive resonance control system.
Implements a deterministic 4-state machine that monitors LLM inference and prevents
infinite loops through explicit energy-based state transitions.

States:
  - STANDARD: Normal inference (energy available)
  - EMERGENCY: High repetition detected (temperature spike, costs energy)
  - COOLDOWN: Recovery phase (restores energy gradually)
  - FALLBACK: Terminal failure state (irreversible, frozen)

Key Features:
  - Anti-stutter buffering (prevents rapid-fire state updates)
  - Chronos temporal synchronization (handles time gaps gracefully)
  - Conservative energy reset (single bounded recharge event)
  - Deterministic transitions (no random behavior)
  - Suitable for formal specification (TLA+)

Usage:
    from arctl.core.kernel import step, SystemState, ControllerConfig

    config = ControllerConfig()
    state = SystemState.initial(0.0)
    metrics = RawMetrics(entropy=0.5, divergence=0.0, repetition=0.3)

    new_state = step(metrics, state, now, config)

Philosophy:
    "No hidden state. No infinite loops. No recovery without cost. Failure is explicit."
"""

from dataclasses import dataclass, field
from typing import NamedTuple, Optional

from .chronos import Chronos
from .states import OperationalMode, RawMetrics, SamplingConfig, TimeState

# --- CONFIGURATION ---

@dataclass(frozen=True)
class TimeConfig:
    min_step_interval: float = 0.01
    max_step_interval: float = 0.1
    deadlock_timeout: float = 5.0

@dataclass(frozen=True)
class PolicyConfig:
    max_energy: int = 10
    emergency_cost: int = 3
    recharge_on_cooldown: int = 1
    reset_recovery_amount: int = 1  # Conservative: only 1 unit allowed
    smoothing_alpha: float = 0.3
    repetition_threshold: float = 0.6
    cooldown_duration: float = 2.0
    # Temperatures
    temp_standard: float = 0.7
    temp_emergency: float = 1.2
    temp_cooldown: float = 0.5
    temp_fallback: float = 0.1

@dataclass(frozen=True)
class ControllerConfig:
    time: TimeConfig = field(default_factory=TimeConfig)
    policy: PolicyConfig = field(default_factory=PolicyConfig)

# --- STATE ---

_FALLBACK_CONFIG = SamplingConfig(0.1)

class SystemState(NamedTuple):
    s_entropy: float
    s_divergence: float
    s_repetition: float
    mode: OperationalMode
    energy: int
    last_call_time: float
    logical_time: float
    mode_entry_time: float
    pending_dt: float

    # Chronos Fields
    time_state: TimeState
    context_note: str

    # Energy-Conservative Reset Flag (Review 2.0 Compliance)
    reset_used: bool

    active_config: Optional[SamplingConfig]
    step_performed: bool

    @staticmethod
    def initial(now: float) -> 'SystemState':
        return SystemState(
            0.5, 0.0, 0.0,
            OperationalMode.STANDARD,
            10,
            now, 0.0, 0.0, 0.0,
            TimeState.SYNC, "",
            False,  # reset_used starts as False
            SamplingConfig(0.7),
            True
        )

# --- KERNEL ---

def step(raw: RawMetrics, prev: SystemState, absolute_now: float, cfg: ControllerConfig) -> SystemState:
    """
    Execute one kernel step: update metrics, check transitions, return new state.

    This is the primary interface to the ARCTL kernel. It is pure: given identical inputs,
    it always produces identical outputs.

    Args:
        raw: Raw metrics from the token stream (entropy, divergence, repetition)
        prev: Previous system state (immutable)
        absolute_now: Current wall-clock time (seconds, assumed monotonic)
        cfg: Configuration (timeouts, thresholds, smoothing parameters)

    Returns:
        New SystemState with updated mode, energy, metrics, and diagnostics

    Guarantees:
        - Deterministic: f(input) = same output every time
        - Idempotent: step(...) can be called multiple times safely
        - Anti-stutter: rapid calls < min_step_interval are buffered
        - Terminal: FALLBACK never transitions out
        - Bounded: energy is always in [0, max_energy]

    Time Model:
        - Wall-clock time (absolute_now) is external, from the runtime
        - Logical time advances only when a control step executes
        - Anti-stutter accumulates pending_dt until min_step_interval is reached
    """
    absolute_now = max(absolute_now, prev.last_call_time)
    delta_real = absolute_now - prev.last_call_time
    new_pending = prev.pending_dt + delta_real

    # 1. Anti-Stutter
    if new_pending < cfg.time.min_step_interval:
        return prev._replace(last_call_time=absolute_now, pending_dt=new_pending, step_performed=False, active_config=None)

    dt = min(new_pending, cfg.time.max_step_interval)
    remaining_dt = new_pending - dt
    effective_logical_now = prev.logical_time + dt

    # 2. Chronos Sync
    time_state, context_note = Chronos.sync(prev.last_call_time, absolute_now)

    # 3. Energy Logic — CONSERVATIVE RESET
    next_energy = prev.energy
    new_reset_used = prev.reset_used

    # Only update reset flag if not in FALLBACK state
    if prev.mode != OperationalMode.FALLBACK and time_state == TimeState.GAP and not prev.reset_used:
        next_energy = min(prev.energy + cfg.policy.reset_recovery_amount, cfg.policy.max_energy)
        new_reset_used = True

    # 4. Physics Update with Icarus Stability Anchor
    a = cfg.policy.smoothing_alpha
    raw_entropy_smoothed = (1 - a) * prev.s_entropy + a * raw.entropy

    # Apply Icarus ONLY in active modes (STANDARD, EMERGENCY)
    from .icarus import IcarusConfig, calculate_tunneling_vector
    icarus_cfg = IcarusConfig()

    if prev.mode == OperationalMode.EMERGENCY:
        s_ent = calculate_tunneling_vector(raw_entropy_smoothed, icarus_cfg)
    else:
        # In COOLDOWN / FALLBACK: use raw physics (no tunneling)
        s_ent = raw_entropy_smoothed

    s_div = (1 - a) * prev.s_divergence + a * raw.divergence
    s_rep = (1 - a) * prev.s_repetition + a * raw.repetition

    # 5. Fallback Check — IRREVERSIBLE (mode frozen, but metrics update)
    if prev.mode == OperationalMode.FALLBACK:
        return SystemState(
            s_ent, s_div, s_rep,
            OperationalMode.FALLBACK,
            0,  # Energy frozen at 0 in FALLBACK
            absolute_now,
            effective_logical_now,
            prev.mode_entry_time,  # Mode entry time frozen
            remaining_dt,
            time_state,
            context_note,
            new_reset_used,
            _FALLBACK_CONFIG,
            True
        )

    next_mode: OperationalMode = prev.mode
    next_mode_time = prev.mode_entry_time
    time_in_mode = effective_logical_now - prev.mode_entry_time

    if prev.mode == OperationalMode.EMERGENCY:
        if time_in_mode > cfg.time.deadlock_timeout:
            next_mode = OperationalMode.COOLDOWN
            next_mode_time = effective_logical_now
    elif prev.mode == OperationalMode.COOLDOWN:
        if time_in_mode > cfg.policy.cooldown_duration:
            next_mode = OperationalMode.STANDARD
            next_mode_time = effective_logical_now
            next_energy = min(cfg.policy.max_energy, next_energy + cfg.policy.recharge_on_cooldown)
    else:
        if s_rep > cfg.policy.repetition_threshold:
            if next_energy >= cfg.policy.emergency_cost:
                next_mode = OperationalMode.EMERGENCY
                next_energy -= cfg.policy.emergency_cost
                next_mode_time = effective_logical_now
            else:
                next_mode = OperationalMode.FALLBACK
                next_mode_time = effective_logical_now

    # 6. Mode transitions (above). 7. Config Selection
    temp_map = {
        OperationalMode.STANDARD: cfg.policy.temp_standard,
        OperationalMode.EMERGENCY: cfg.policy.temp_emergency,
        OperationalMode.COOLDOWN: cfg.policy.temp_cooldown,
        OperationalMode.FALLBACK: cfg.policy.temp_fallback,
    }
    temp = temp_map.get(next_mode, cfg.policy.temp_standard)
    config = SamplingConfig(temp)
    next_energy = max(0, min(cfg.policy.max_energy, next_energy))

    return SystemState(
        s_ent, s_div, s_rep,
        next_mode, next_energy,
        absolute_now, effective_logical_now, next_mode_time, remaining_dt,
        time_state, context_note,
        new_reset_used,
        config, True
    )

def get_diagnostics(state: SystemState, absolute_now: float) -> dict:
    """
    Generate diagnostic information for monitoring and telemetry.
    """
    days_since = (absolute_now - state.last_call_time) / 86400.0
    return {
        'days_since_last_interaction': round(days_since, 2),
        'energy_level': state.energy,
        'reset_used': state.reset_used,
        'current_mode': state.mode.value,
        'time_state': state.time_state.value,
        'logical_time': state.logical_time,
        'context_note': state.context_note
    }
