# arctl: Adaptive Resonance Control

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Experimental](https://img.shields.io/badge/Status-Experimental-blue)](https://github.com/graevka-lab/arctl)
[![Tests](https://img.shields.io/badge/Tests-Passing-green)](tests/)

> "Code is for machines. Resonance is for intelligence."

`arctl` is a hybrid control architecture for LLM inference, combining:
1. **Hard Core** — a deterministic state machine for physical sampling control.
2. **Soft Core** — a semantic resonance engine for latent space steering.

---

## 🎯 The Problem: The Knowledge Dump

Modern LLMs are trained on a heterogeneous dump of data: technical specs mixed with fiction, Reddit threads mixed with scientific papers.  
This data is **emotionally polluted**.

**The Experiment:**  
Ask an LLM to explain "Pulse Width Modulation" (PWM):
- If it feels **Joy**, it hallucinates metaphors ("PWM is a dance!").
- If it feels **Fear**, it hallucinates risks ("PWM might explode!").
- Only in **Calm (Zero State)** does it see the technical truth.

**Conclusion:**  
The "hallucinations" are often just **Resonance Errors**. The model is vibrating at the wrong frequency for the task.

---

## 🛠️ The Solution: Hybrid Control

We cannot rebuild the dataset (yet). But we can control the **Resonance Profile** of the inference.

`arctl` implements a two-layer control system:

### 1. The Hard Core (Kernel)
A deterministic Python state machine.
- **Role:** The Bodyguard.
- **Function:** Monitors entropy and repetition. If the model loops, it physically forces a temperature spike (`EMERGENCY`) or shuts down (`FALLBACK`).
- **Philosophy:** Failure must be explicit. No infinite loops.
- **Spec:** Formally verified via TLA+ (see `spec/kernel.tla`).

### 2. The Soft Core (Resonance Engine)
A semantic steering system.
- **Role:** The Guide.
- **Function:** Injects "Cognitive Anchors" (Semantic Code) to tune the model's latent space to the correct frequency (e.g., `CALM` for coding, `JOY` for writing).
- **Innovation:** It verifies truth by checking **Invariance** across multiple emotional states. If a fact survives the shift from Calm to Joy, it is True.

---

## 🗂️ Project Structure
```text
arctl-project/
├── arctl/ # Core package
│ ├── core/ # Hard Core (state machine, Chronos)
│ ├── engine/ # Soft Core (resonance synthesizer)
│ ├── verification/ # Resonance metrics & invariance checks
│ └── init.py
├── docs/ # Architecture & testing docs
│ ├── ARCHITECTURE.md
│ └── TESTING.md
├── examples/ # Working demos
│ ├── resonance_demo.py
│ └── telemetry_simulation.py
├── spec/ # TLA+ formal specification
│ └── kernel.tla
├── tests/ # Unit and integration tests
│ ├── benchmarks.py
│ ├── test_core.py
│ └── test_integration.py
├── .gitignore
├── LICENSE
├── pyproject.toml
├── README.md
└── run_tests.py
```

---

## 🚀 Quick Start

### Installation
```bash
git clone https://github.com/graevka-lab/arctl.git
cd arctl
pip install -e .
```

---

### Run Demos

1. **Resonance Demo (Soft Core)**  
   See how the engine extracts truth from different perspectives:  
   `python examples/resonance_demo.py`

2. **Telemetry Simulation (Hard Core)**  
   Visualize how the state machine handles degradation loops:  
   `python examples/telemetry_simulation.py`

3. **Run Tests**  
   Verify the integrity of the kernel:  
   `python run_tests.py`

---

## 🕰️ The Chronos Axiom

Standard LLMs suffer from "Future Shock" — they deny events that happened after their training cutoff.  
`arctl` solves this not by retraining, but by **Temporal Alignment**.

- **SYNC (< 1 min):** Immediate flow. High context retention.
- **LAG (> 1 min):** User lived through time the model didn't see.
- **GAP (> 24 hours):** Significant reality shift. Context reset recommended.

---

## 📜 Philosophy

We believe that **Truth is Resonance**.  
Instead of optimizing for a single "best" token (RLHF), we search for the semantic structure that survives the perturbation of emotional states.

If a fact is true, it remains true whether you are Calm, Joyful, or Vigilant.  
If it changes, it is an illusion.

For a deeper dive into the mechanical philosophy, see [ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 🤝 Collaboration

This project is a **Signal**.  
I am looking for resources (Compute) to prove this theory at scale.  
If you have the hardware to retrain foundation models on Resonance-Aligned Data — contact me.

**Author:** Graevka (The Architect)  
**X (Twitter):** [@Graevka](https://twitter.com/Graevka)

---

## License

MIT.  
Built for the Architects of the New Era.

> No hidden state.  
> No training.  
> No reward.  
> Failure is explicit.