"""
Integration example: use arctl inside an inference loop.
Run from project root: python examples/arctl_in_inference_loop.py
"""

import os
import sys
from dataclasses import replace
from typing import Generator, Tuple, List, Optional
from arctl.core.kernel import ControllerConfig, SystemState, step
from arctl.verification.lexical import LexicalMetrics

# --- PATH HACK ---
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def arctl_loop(
    token_stream: List[str],
    cfg: Optional[ControllerConfig] = None,
    window: int = 50,
    time_step: float = 0.1,
) -> Generator[Tuple[SystemState, float], None, None]:
    cfg = cfg or ControllerConfig(policy=replace(ControllerConfig().policy, smoothing_alpha=1.0))
    state = SystemState.initial(0.0)
    now = 0.0
    buffer: List[str] = []

    for t in token_stream:
        buffer.append(t)
        if len(buffer) < window:
            continue
        recent = buffer[-window:]
        raw = LexicalMetrics.calculate(recent, window=window)
        now += time_step
        state = step(raw, state, now, cfg)
        temp = state.active_config.temperature if state.active_config else 0.7
        yield state, temp


def main() -> None:
    print("=" * 60)
    print("ARCTL in inference loop (synthetic token stream)")
    print("=" * 60)

    diverse = "the quick brown fox jumps over the lazy dog ".split()
    repetitive = ["token"] * 200
    stream = (diverse * 10) + repetitive

    print("\nStream: 90 diverse tokens + 200 repetitive. Window=50, step=0.1s")
    print("\nStep | Mode    | Energy | Temp  | s_repetition")
    print("-" * 55)

    step_count = 0
    for i, (state, temp) in enumerate(arctl_loop(stream, time_step=0.1)):
        step_count = i
        if i <= 15 or state.mode.value != "STD" or i % 20 == 0:
            print(
                f"  {i:4} | {state.mode.value:8} | {state.energy:6} | {temp:.3f} | {state.s_repetition:.3f}"
            )
        if state.mode.value == "FBK":
            print("  ... (FALLBACK reached)")
            break

    if step_count > 20 and state.mode.value != "FBK":
        print("  ...")
        print(
            f"  {step_count:4} | {state.mode.value:8} | {state.energy:6} | {temp:.3f} | {state.s_repetition:.3f}"
        )

    print("\nUse this pattern to plug arctl into your inference:")
    print("  for state, temperature in arctl_loop(my_token_iterator, cfg):")
    print("      next_token = model.generate(..., temperature=temperature)")
    print("=" * 60)


if __name__ == "__main__":
    main()
