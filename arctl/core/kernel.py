# core v1.0 (Integrated with Chronos)
# "It just works — quietly."

from typing import NamedTuple, Optional
from dataclasses import dataclass, field

from .states import OperationalMode, TimeState, RawMetrics, SamplingConfig
from .chronos import Chronos

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
    smoothing_alpha: float = 0.3
    repetition_threshold: float = 0.6
    cooldown_duration: float = 2.0
    # Configurable Temperatures
    temp_standard: float = 0.7
    temp_emergency: float = 1.2
    temp_cooldown: float = 0.5
    temp_fallback: float = 0.1

@dataclass(frozen=True)
class ControllerConfig:
    time: TimeConfig = field(default_factory=TimeConfig)
    policy: PolicyConfig = field(default_factory=PolicyConfig)

# --- TYPES ---

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
            SamplingConfig(0.7), 
            True
        )

# --- KERNEL ---

def step(raw: RawMetrics, prev: SystemState, absolute_now: float, cfg: ControllerConfig) -> SystemState:
    absolute_now = max(absolute_now, prev.last_call_time)
    delta_real = absolute_now - prev.last_call_time
    new_pending = prev.pending_dt + delta_real

    # 1. Anti-Stutter (Physics)
    if new_pending < cfg.time.min_step_interval:
        return prev._replace(last_call_time=absolute_now, pending_dt=new_pending, step_performed=False, active_config=None)

    dt = min(new_pending, cfg.time.max_step_interval)
    remaining_dt = new_pending - dt
    effective_logical_now = prev.logical_time + dt

    # 2. CHRONOS INTEGRATION (Perception)
    time_state, context_note = Chronos.sync(prev.last_call_time, absolute_now)

    # 3. Energy Logic (Reset on GAP)
    next_energy = prev.energy
    if time_state == TimeState.GAP:
        # If gap > 24h, restore energy (user rested, context refreshed)
        next_energy = cfg.policy.max_energy

    # 4. Physics Update (applies to all modes)
    a = cfg.policy.smoothing_alpha
    s_ent = (1-a)*prev.s_entropy + a*raw.entropy
    s_div = (1-a)*prev.s_divergence + a*raw.divergence
    s_rep = (1-a)*prev.s_repetition + a*raw.repetition

    # 5. FALLBACK Terminal Check
    # FALLBACK is a Terminal Absorbing State - ontological failure.
    # No recovery, no transitions, no energy management.
    # System must remain here until hard reset (process restart).
    if prev.mode == OperationalMode.FALLBACK:
        return prev._replace(
            last_call_time=absolute_now,
            logical_time=effective_logical_now,
            s_entropy=s_ent,
            s_divergence=s_div,
            s_repetition=s_rep,
            pending_dt=remaining_dt,
            time_state=time_state,
            context_note=context_note,
            active_config=_FALLBACK_CONFIG,
            step_performed=True
        )

    # 6. Mode Transition Logic (for non-FALLBACK modes)
    next_mode = prev.mode
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
    else:  # STANDARD mode
        if s_rep > cfg.policy.repetition_threshold:
            if next_energy >= cfg.policy.emergency_cost: 
                next_mode = OperationalMode.EMERGENCY
                next_energy -= cfg.policy.emergency_cost
                next_mode_time = effective_logical_now
            else: 
                next_mode = OperationalMode.FALLBACK
                next_mode_time = effective_logical_now

    # 7. Config Selection
    if next_mode == OperationalMode.STANDARD:
        temp = cfg.policy.temp_standard
    elif next_mode == OperationalMode.EMERGENCY:
        temp = cfg.policy.temp_emergency
    elif next_mode == OperationalMode.COOLDOWN:
        temp = cfg.policy.temp_cooldown
    else:
        temp = cfg.policy.temp_fallback

    config = SamplingConfig(temp)
    next_energy = max(0, min(cfg.policy.max_energy, next_energy))

    return SystemState(
        s_ent, s_div, s_rep,
        next_mode, next_energy,
        absolute_now, effective_logical_now, next_mode_time, remaining_dt,
        time_state, context_note,
        config, True
    )

def get_diagnostics(state: SystemState, absolute_now: float) -> dict:
    """
    Pure diagnostic function for monitoring and telemetry.
    """
    days_since = (absolute_now - state.last_call_time) / 86400.0
    return {
        'days_since_last_interaction': round(days_since, 2),
        'energy_level': state.energy,
        'current_mode': state.mode.value,
        'time_state': state.time_state.value,
        'logical_time': state.logical_time,
        'context_note': state.context_note
    }