# Adaptive Core

Stateless adaptive controller with explicit terminal failure semantics for LLM sampling.  
Stateless in the functional sense: state is explicit and externally observable.

> **If you’ve never debugged an LLM that spiraled into infinite loops or policy hallucinations — you might not need this.**  
> **If you have, this is your last line of defense.**

---

## Quick Start (CPU-only, no GPU needed)

```bash
git clone https://github.com/graevka-lab/arctl.git
cd arctl
python main.py
```

## You’ll see how the system reacts to degradation:

```
Draft 1: 'I think maybe 42...' → Mode: EMERGENCY (energy: 7)
Draft 2: 'As an AI, I cannot...' → Mode: COOLDOWN (energy: 7)
Draft 3: 'The answer is 42.' → Mode: STANDARD (energy: 8)
```

## No model required. No API keys. Just pure control logic.

---

## What This Is

- A **referentially transparent** adaptive controller
- A **discrete state machine** with explicit failure ontology
- An **executable specification** suitable for formal reasoning (e.g. TLA+)
- A control-layer component for long-running LLM inference systems

---

## What This Is Not

- Not a training mechanism
- Not a preference optimizer
- Not an alignment or reward-based system
- Not a recovery-oriented safety wrapper

There are no hidden objectives, no reward signals, and no learning dynamics.

---

## Operational Semantics (Informal)

The controller operates as a discrete-time state machine driven by external metrics.

Time is modeled in two layers:
- **Wall-clock time** — for safety, liveness, and starvation detection
- **Logical time** — for policy transitions and control semantics

The system expends **discrete energy** to escape anomalous regimes.
If energy is exhausted under sustained anomaly, the system enters an **irreversible FALLBACK state**.

Fallback is absorbing by design.

---

## Failure Model

Failure is not treated as an exception.  
Failure is a first-class outcome.

- Degradation is surfaced, not masked
- Emergency behavior is energy-bounded
- FALLBACK is terminal and irreversible
- No automatic recovery is permitted once FALLBACK is reached

This is an intentional design choice.

---

## Invariants

- Referential transparency (pure state transitions)
- Monotonic logical time
- Bounded discrete energy
- Explicit mode transitions
- Terminal FALLBACK state (absorbing)
- No hidden objectives or reward signals
- In FALLBACK, logical_time may advance but control physics are frozen

---

## Ontological Reset Semantics

Energy reset after prolonged absence is intentionally **non-interactive**.

This prevents false liveness under external polling (e.g. health checks),
but may mask starvation if interaction tracking is misused.

This tradeoff is explicit and intentional.

---

## Metrics and Forward Compatibility

The controller tracks entropy, divergence, and repetition as smoothed internal state.

Entropy and divergence are currently **not used** in emergency logic.
They are preserved as **first-class state variables** to ensure forward compatibility
without requiring state migration when policies evolve.

---

## Philosophy and Ethical Use

This software is provided under the MIT License, which grants broad permissions for use.

However, the spirit of this project is rooted in the creation of reliable, predictable,
and failure-honest systems.

This project intentionally avoids adaptive objectives, reward signals, or hidden optimization pressures.

Use of this software for intentionally deceptive, harmful, or destabilizing purposes
runs contrary to the core intent of this work.
While the license does not legally restrict such use, ethical responsibility is assumed.

---

## Useful For

- Long-running LLM inference services
- Failure-aware control layers
- Anomaly detection via control state transitions
- Research on formal semantics of failure in generative systems

---

## Not Useful For

- Maximizing user satisfaction
- Preference tuning
- Alignment training
- Output optimization

---

## Attribution and Citation

While the MIT License does not require attribution,
it is appreciated if this work is cited or linked when used in research or production systems.

**Recommended citation (academic use):**

Graevka.  
*Adaptive Core: A Stateless Controller with Terminal Failure Semantics for LLM Sampling.*  
2026.

GitHub: https://github.com/graevka-lab/arctl  

For commercial or public projects, a simple link in documentation or an “About” section is sufficient.

---

No hidden state.  
No training.  
No reward.

Failure is explicit.
