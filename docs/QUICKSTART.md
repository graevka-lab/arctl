# Quick Start Guide

Welcome to **arctl** — Adaptive Resonance Control for LLMs!

This guide gets you from zero to running in 5 minutes.

---

## Prerequisites

Ensure you have:
- **Python 3.8+** ([Download](https://www.python.org/downloads/))
- **Git** ([Install](https://git-scm.com/))
- **pip** (comes with Python)

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/graevka-lab/arctl.git
cd arctl
```

### 2. Install in Development Mode

```bash
pip install -e .
```

This installs the core `arctl` package with minimal dependencies.

### 3. (Optional) Enable Resonance Verification

To use the Soft Core semantic verification:

```bash
pip install sentence-transformers
```

---

## First Steps

### Run the Tests

```bash
python run_tests.py --unit
```

### Run a Live Demo

```bash
# Kernel demo (fastest)
python examples/resonance_demo.py

# Real-time telemetry visualization
python examples/telemetry_simulation.py

# 3D phase space visualization
python examples/visualize_phase_space.py
```

---

## Using ARCTL in Your Code

### Basic Kernel Usage

```python
from arctl.core.kernel import step, SystemState, ControllerConfig
from arctl.core.states import RawMetrics

config = ControllerConfig()
state = SystemState.initial(0.0)

metrics = RawMetrics(entropy=0.5, divergence=0.0, repetition=0.3)
new_state = step(metrics, state, 1.0, config)

print(f"Mode: {new_state.mode}")
print(f"Energy: {new_state.energy}")
```

### Detecting Repetition Loops

```python
from arctl.verification.lexical import LexicalMetrics

tokens = ["the", "the", "the", "the", "the"]
metrics = LexicalMetrics.calculate(tokens, window=5)

print(f"Repetition Score: {metrics.repetition:.2f}")
```

### Semantic Verification

```python
from arctl.verification.metrics import ResonanceVerifier

verifier = ResonanceVerifier()

responses = {
    "calm": "PWM controls power via duty cycle.",
    "joy": "PWM is fun to control circuits!",
    "vigilance": "PWM requires EMI filtering."
}

result = verifier.verify(responses)
print(f"Resonance Score: {result['resonance_score']:.3f}")
```

---

## Configuration

```python
from arctl.core.kernel import ControllerConfig, PolicyConfig

config = ControllerConfig(
    policy=PolicyConfig(
        max_energy=15,
        emergency_cost=2,
        repetition_threshold=0.5,
        smoothing_alpha=0.5,
    )
)
```

---

## Architecture Overview

### Hard Core (Kernel)

4-state deterministic machine:
- **STANDARD** → Normal operation
- **EMERGENCY** → High repetition detected (costs 3 energy)
- **COOLDOWN** → Recovery phase (restores 1 energy)
- **FALLBACK** → Terminal failure state

### Soft Core (Resonance Engine)

Steers semantics via Cognitive Anchors in 4 modes:
- **Calm** — Technical precision
- **Joy** — Creative exploration
- **Vigilance** — Risk awareness
- **Wonder** — Philosophical depth

---

## Next Steps

1. [ARCHITECTURE.md](../docs/ARCHITECTURE.md) — Deep dive
2. [TESTING.md](../docs/TESTING.md) — Test suite guide
3. [GitHub Issues](https://github.com/graevka-lab/arctl) — Get help

---

Happy building! 🚀