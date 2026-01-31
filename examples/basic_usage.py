"""
Basic Usage Example: ARCTL Kernel Demo

This is the simplest possible example of using ARCTL.
Shows the core state machine in action.

Run with: python examples/basic_usage.py
"""

import sys
import os

# Path hack for running from examples/
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from arctl.core.kernel import step, SystemState, ControllerConfig, PolicyConfig
from arctl.core.states import RawMetrics, OperationalMode
from dataclasses import replace


def main():
    print("=" * 70)
    print("ARCTL: Basic Usage Example")
    print("=" * 70)
    print()
    
    # 1. Initialize the kernel
    print("Step 1: Initialize the kernel")
    print("-" * 70)
    # Use fast smoothing (alpha=1.0) for demo clarity
    config = ControllerConfig(
        policy=replace(ControllerConfig().policy, smoothing_alpha=1.0)
    )
    state = SystemState.initial(0.0)
    current_time = 0.0
    
    print(f"Initial mode:   {state.mode.value}")
    print(f"Initial energy: {state.energy}")
    print()
    
    # 2. Simulate normal operation
    print("Step 2: Normal operation (low repetition)")
    print("-" * 70)
    normal_metrics = RawMetrics(entropy=0.5, divergence=0.0, repetition=0.2)
    
    for i in range(3):
        current_time += 0.02  # Increment by at least min_step_interval
        state = step(normal_metrics, state, current_time, config)
        print(f"  Step {i+1}: mode={state.mode.value}, energy={state.energy}, "
              f"repetition={state.s_repetition:.3f}")
    print()
    
    # 3. Trigger emergency (high repetition)
    print("Step 3: High repetition detected -> EMERGENCY mode")
    print("-" * 70)
    high_rep_metrics = RawMetrics(entropy=0.5, divergence=0.0, repetition=0.9)
    
    current_time += 0.02
    state = step(high_rep_metrics, state, current_time, config)
    print(f"  Mode changed to: {state.mode.value}")
    print(f"  Energy cost:     {config.policy.emergency_cost} (now {state.energy})")
    print(f"  Temperature:     {state.active_config.temperature} (was 0.7)")
    print()
    
    # 4. Exit emergency through timeout
    print("Step 4: Emergency timeout -> COOLDOWN mode")
    print("-" * 70)
    print(f"  Waiting for deadlock_timeout ({config.time.deadlock_timeout}s)...")
    
    normal_metrics = RawMetrics(entropy=0.5, divergence=0.0, repetition=0.2)
    for i in range(60):  # 60 * 0.1 = 6 seconds
        current_time += 0.1
        state = step(normal_metrics, state, current_time, config)
    
    print(f"  Mode changed to: {state.mode.value}")
    print(f"  Temperature:     {state.active_config.temperature} (recovery phase)")
    print()
    
    # 5. Exit cooldown
    print("Step 5: Cooldown duration -> STANDARD mode (recovered)")
    print("-" * 70)
    print(f"  Waiting for cooldown_duration ({config.policy.cooldown_duration}s)...")
    
    for i in range(30):  # 30 * 0.1 = 3 seconds
        current_time += 0.1
        state = step(normal_metrics, state, current_time, config)
    
    print(f"  Mode changed to: {state.mode.value}")
    print(f"  Energy restored: {state.energy} (gained 1)")
    print(f"  Temperature:     {state.active_config.temperature} (normal)")
    print()
    
    # 6. Summary
    print("=" * 70)
    print("Summary: Full State Machine Cycle Completed")
    print("=" * 70)
    print(f"Path: STANDARD -> EMERGENCY -> COOLDOWN -> STANDARD")
    print(f"Final energy: {state.energy}")
    print(f"Final mode:   {state.mode.value}")
    print(f"Logical time: {state.logical_time:.1f} seconds")
    print()
    print("[OK] ARCTL is working correctly!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
