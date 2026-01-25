# Common Issues & Solutions

This guide addresses common runtime issues and configuration pitfalls when using `arctl`.

---

## ⚠️ Runtime Warnings

### 1. "sentence_transformers not installed"
**Symptom:**
You see a warning: `[WARNING] sentence_transformers not installed. Verification disabled.`
The `ResonanceVerifier` returns a score of `0.0`.

**Cause:**
The resonance verification module requires the `sentence-transformers` library to compute semantic embeddings. It is an optional dependency to keep the core lightweight.

**Solution:**
Install the full dependency set:
```bash
pip install sentence-transformers
```
### 2. "ModuleNotFoundError: No module named 'arctl'"

**Symptom:**
Running examples directly (e.g., `python examples/resonance_demo.py`) fails with an import error.

**Cause:**
Python cannot find the `arctl` package if it hasn't been installed in the current environment.

**Solution:**
Install the package in editable mode from the project root:

```bash
pip install -e .
```
Or ensure you are running scripts from the project root directory.

## 🐌 Performance
### 1. Slow Verification

**Symptom:**
`ResonanceVerifier.verify()` takes a long time to execute.

**Cause:**
The verification process has O(N²) complexity relative to the number of cognitive modes. With 4 default modes, it performs 6 pairwise comparisons. If you add more custom modes, the cost grows quadratically.

**Recommendation:**
Keep the number of active cognitive modes between 3 and 5 for optimal performance.

### 2. High Token Usage

**Symptom:**
The `ResonanceSynthesizer` consumes significantly more tokens than a standard prompt.

**Cause:**
The "Soft Core" injects semantic anchors (system prompts) into the context. This is by design.
Note: This module is intended for high-value inference where quality > cost. For high-throughput scenarios, rely on the "Hard Core" (Kernel) only.

## 🧪 Testing
### Tests failing with "AssertionError"

**Symptom:**
Integration tests fail after changing `ControllerConfig` defaults.

**Cause:**
Some tests rely on specific default values (e.g., `repetition_threshold=0.6`). If you modify `arctl/core/kernel.py` defaults, you must update the tests.

**Solution:**
Use a custom config object in your tests instead of relying on defaults.

## 🐛 Reporting Bugs

If you encounter an issue not listed here, please open an issue on GitHub with:

Your Python version.

The full traceback.

A minimal reproduction script.