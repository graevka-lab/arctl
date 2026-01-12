# Adaptive Core — Architecture

This document describes the conceptual and operational architecture of Adaptive Core.
It is not an implementation guide.
It is a semantic map of the system.

The code remains the primary specification.

---

## 1. Design Goal

Adaptive Core is designed to make **failure explicit, bounded, and irreversible**.

The system does not attempt to optimize outputs, recover indefinitely, or conceal degradation.
Instead, it enforces a controlled descent into a terminal state when anomalous conditions persist.

This is intentional.

---

## 2. System Model

Adaptive Core is a **pure state machine**.

At every step:

Input:
- RawMetrics (entropy, divergence, repetition)
- Previous immutable SystemState
- Absolute wall-clock time
- Static configuration

Output:
- New immutable SystemState

There are no side effects.
There is no hidden state.
There is no learning.

---

## 3. Time Model

Time is modeled on two independent axes:

### 3.1 Wall-Clock Time

- Represents external, real-world time
- Used for:
  - anti-stutter protection
  - starvation detection
  - ontological reset after prolonged absence

Wall-clock time is assumed monotonic.
Violations are guarded against defensively.

### 3.2 Logical Time

- Represents internal control evolution
- Advances only when a control step is performed
- Used for:
  - mode timeouts
  - cooldown duration
  - policy semantics

Logical time is monotonically non-decreasing.

In FALLBACK, logical time may advance, but control physics are frozen.

---

## 4. Modes (Control States)

The controller operates in exactly one of four modes:

### STANDARD (STD)

- Normal operation
- Energy may be spent to escape anomalies

### EMERGENCY (EMG)

- Entered when repetition exceeds threshold
- Consumes discrete energy on entry
- Intended as a short-lived escape regime

### COOLDOWN (CDN)

- Entered after EMERGENCY timeout
- Gradually restores energy
- Acts as a damping phase

### FALLBACK (FBK)

- Terminal, absorbing state
- No transitions out are permitted
- Control physics are frozen
- Sampling configuration is minimal and deterministic

FALLBACK represents ontological failure, not temporary safety mode.

---

## 5. Energy Model

Energy is:
- Discrete
- Bounded
- Spent only on EMERGENCY entry
- Partially restored during COOLDOWN
- Fully reset after prolonged absence (ontological reset)

Energy exhaustion under sustained anomaly leads to FALLBACK.

There is no energy regeneration loop that guarantees recovery.

---

## 6. Ontological Reset

After prolonged absence of interaction, energy may be reset to maximum.

This reset:
- Is non-interactive
- Does not update last_interaction
- Exists to prevent permanent starvation due to inactivity

This is a deliberate tradeoff and must not be treated as recovery.

---

## 7. Metrics and Smoothing

Raw metrics are externally provided and normalized.

Internal state tracks smoothed versions of:
- entropy
- divergence
- repetition

Currently:
- Only repetition participates in emergency logic
- Other metrics are preserved for forward compatibility

State evolution is deterministic given inputs.

---

## 8. Failure Philosophy

Failure is a valid and expected outcome.

The system:
- Surfaces degradation
- Bounds escape attempts
- Refuses infinite recovery loops

Once FALLBACK is reached, the system remains there.

This is not pessimism.
This is honesty.

---

## 9. Formal Properties (Informal)

The system satisfies:

- Referential transparency
- Deterministic transitions
- Bounded resources
- Explicit terminal state
- Suitability for formal specification (e.g. TLA+)

The implementation is an executable specification of these properties.

---

End of architecture.
