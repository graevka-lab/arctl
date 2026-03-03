"""
Simulation experiment: with arctl vs without arctl on a synthetic high-repetition stream.

Produces a reproducible table and summary. No GPU or API required.
Run from project root: python experiments/simulation_experiment.py
"""

import os
import sys
from dataclasses import replace

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from arctl.core.kernel import ControllerConfig, SystemState, step
from arctl.core.states import OperationalMode, RawMetrics


def run_uncontrolled(metrics_stream, steps):
    """Simulate 'without arctl': just record repetition over steps (no controller)."""
    return [(i, m.repetition) for i, m in enumerate(metrics_stream[:steps])]


def run_with_arctl(metrics_stream, steps, cfg):
    """Run the same stream through arctl; record mode and energy each step."""
    state = SystemState.initial(0.0)
    now = 0.0
    history = []
    for i in range(steps):
        m = metrics_stream[min(i, len(metrics_stream) - 1)]
        now += 0.1
        state = step(m, state, now, cfg)
        history.append((i, state.mode, state.energy, state.s_repetition))
        if state.mode == OperationalMode.FALLBACK:
            break
    return history


def main():
    cfg = ControllerConfig(
        policy=replace(ControllerConfig().policy, smoothing_alpha=1.0)
    )
    steps = 80
    # Stream: 10 normal, then high repetition (simulating a stuck/degenerate loop)
    low = RawMetrics(entropy=0.5, divergence=0.0, repetition=0.2)
    high = RawMetrics(entropy=0.5, divergence=0.0, repetition=0.9)
    metrics_stream = [low] * 10 + [high] * (steps - 10)

    print("=" * 60)
    print("Experiment: High-repetition stream (with vs without arctl)")
    print("=" * 60)

    # Without arctl: repetition trajectory
    unctrl = run_uncontrolled(metrics_stream, steps)
    rep_after_10 = [r for i, r in unctrl if i >= 10]
    avg_high_rep = sum(rep_after_10) / len(rep_after_10) if rep_after_10 else 0

    print("\n1. WITHOUT arctl (uncontrolled)")
    print(f"   Repetition from step 10 onward: constant high (avg = {avg_high_rep:.3f})")
    print("   No mode transitions, no intervention.")

    # With arctl
    hist = run_with_arctl(metrics_stream, steps, cfg)
    fallback_at = next((i for i, mode, _, _ in hist if mode == OperationalMode.FALLBACK), None)
    emergencies = sum(1 for _, mode, _, _ in hist if mode == OperationalMode.EMERGENCY)
    cooldowns = sum(1 for _, mode, _, _ in hist if mode == OperationalMode.COOLDOWN)

    print("\n2. WITH arctl")
    print("   First EMERGENCY at step:", next((i for i, mode, _, _ in hist if mode == OperationalMode.EMERGENCY), "N/A"))
    print("   EMERGENCY count:", emergencies)
    print("   COOLDOWN count:", cooldowns)
    print("   FALLBACK at step:", fallback_at if fallback_at is not None else "N/A (did not reach)")
    if hist:
        print("   Final energy:", hist[-1][2])
        print("   Final mode:", hist[-1][1].value)

    # Small table: steps 8-25 (around transition)
    print("\n3. Sample trajectory (steps 8-25)")
    print("   Step | Uncontrolled(rep) | With arctl: mode    | energy")
    print("   " + "-" * 52)
    for i in range(8, min(26, len(hist))):
        _, mode, energy, srep = hist[i]
        m_rep = metrics_stream[i].repetition
        print(f"   {i:4} | {m_rep:17.3f} | {mode.value:12} | {energy:5}")

    print("\n" + "=" * 60)
    print("Summary: arctl forces EMERGENCY -> COOLDOWN -> STANDARD or FALLBACK;")
    print("         uncontrolled stream would keep repetition high with no intervention.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
