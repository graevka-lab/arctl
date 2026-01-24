# 🧪 Testing & Benchmarking Guide for ARCTL

## Quick Start

### Run All Tests
```bash
# Using unittest
python -m unittest discover tests

# Using run_tests.py script
python run_tests.py

# Using pytest (if installed)
pytest
```

### Run Specific Test Suites
```bash
# Unit tests only
python run_tests.py --unit

# Integration tests only
python run_tests.py --integration

# Benchmarks only
python run_tests.py --bench
```

### Run Benchmarks
```bash
# Full benchmark suite
python tests/benchmarks.py

# Or through test runner
python run_tests.py --bench
```

---

## Test Structure

### Unit Tests (`tests/test_core.py`)

Tests for individual components:

- **TestKernelBasics** — Basic kernel functionality
  - `test_initial_state` — Verify initial state properties
  - `test_anti_stutter_mechanism` — Verify rapid-call buffering

- **TestStateMachine** — State transitions
  - `test_standard_to_emergency_transition` — STANDARD → EMERGENCY
  - `test_emergency_to_cooldown_on_timeout` — EMERGENCY → COOLDOWN
  - `test_cooldown_duration_and_recovery` — COOLDOWN → STANDARD
  - `test_energy_depletion_leads_to_fallback` — Energy exhaustion
  - `test_multiple_transitions_cycle` — Full cycle test

- **TestFallbackTerminal** — FALLBACK invariant
  - `test_fallback_is_terminal` — Verify no transitions out
  - `test_fallback_physics_still_updates` — Physics updates continue

- **TestEnergyManagement** — Energy budget
  - `test_energy_restoration_on_24h_gap` — Long-delay recovery
  - `test_energy_clamped_to_bounds` — Boundary enforcement

- **TestMetricSmoothing** — EMA smoothing
  - `test_smoothing_alpha_zero` — No change when α=0
  - `test_smoothing_alpha_one` — Instant update when α=1

- **TestLexicalMetrics** — Token analysis
  - `test_repetition_detection` — Detect repeated tokens
  - `test_diversity_scoring` — Score vocabulary diversity

- **TestTimeManagement** — Chronos synchronization
  - `test_time_state_sync` — SYNC state (< 60s)
  - `test_time_state_lag` — LAG state (60s-24h)
  - `test_time_state_gap` — GAP state (> 24h)

- **TestEdgeCases** — Boundary conditions
  - `test_zero_energy_no_emergency` — Cannot afford EMERGENCY
  - `test_metric_boundaries` — Metrics stay in [0,1]
  - `test_max_energy_clamping` — Energy bounded

**Run:**
```bash
python -m unittest tests.test_core -v
```

---

### Integration Tests (`tests/test_integration.py`)

Tests for system interaction:

- **TestKernelWithLexicalMetrics** — Kernel + lexical analysis
  - `test_repetition_triggers_emergency` — High rep → EMERGENCY
  - `test_diverse_tokens_stay_standard` — Diverse → STANDARD

- **TestFullWorkflow** — Complete degradation sequence
  - `test_degradation_sequence` — STANDARD → EMG → CDN → STD

- **TestResonanceIntegration** — Resonance verification
  - `test_stable_resonance_patterns` — Mode consistency scoring

- **TestLongRunningBehavior** — Extended runs
  - `test_100_step_stability` — 100 steps without issues
  - `test_energy_depletion_reaches_fallback` — Exhaustion over time

- **TestErrorRecovery** — Edge cases
  - `test_rapid_fire_steps` — Anti-stutter under load
  - `test_time_gap_handling` — 24h+ inactivity recovery

**Run:**
```bash
python -m unittest tests.test_integration -v
```

---

## Benchmarks (`tests/benchmarks.py`)

Performance measurements:

### Throughput Benchmarks

| Benchmark | Purpose | Iterations |
|-----------|---------|-----------|
| Single step() | Baseline kernel performance | 10,000 |
| State cycle | 3-step STANDARD→EMG→CDN→STD | 5,000 |
| FALLBACK (early return) | Terminal state overhead | 50,000 |
| Lexical metrics | Token analysis cost | 10,000 |
| Metric smoothing | EMA with α=0.3 | 50,000 |
| Energy restoration | 24h+ gap handling | 10,000 |
| Rapid steps (100×) | Anti-stutter buffering | 100 iterations |
| Time state transitions | SYNC/LAG/GAP switching | 5,000 |
| Config construction | Dataclass creation | 100,000 |
| State copy (._replace) | NamedTuple copying | 100,000 |

### Scaling Tests

Tests how performance scales with step count:
- 10 steps
- 100 steps
- 1,000 steps
- 10,000 steps

### Memory Usage

Reports memory consumption:
- SystemState object
- ControllerConfig object
- RawMetrics object
- Array of 1,000 states

**Run:**
```bash
python tests/benchmarks.py
```

**Example output:**
```
Single step() execution                      |   1000000 ops/s |      800 ns | [700-900] ns
Full state cycle (3 steps)                   |    500000 ops/s |     2000 ns | [1800-2500] ns
FALLBACK state (early return)                |   2000000 ops/s |      400 ns | [350-500] ns
Lexical metrics calculation                  |   100000 ops/s |    10000 ns | [9000-15000] ns
```

---

## Test Coverage

### What's Tested

✅ **State Machine Logic**
- All mode transitions (STANDARD ↔ EMERGENCY ↔ COOLDOWN)
- FALLBACK terminal property
- Energy management and restoration
- Mode entry/exit timing

✅ **Physics & Metrics**
- Exponential moving average smoothing (all α values)
- Metric boundary enforcement ([0,1])
- Lexical repetition detection
- Entropy diversity scoring

✅ **Time Management**
- Chronos time state classification (SYNC/LAG/GAP)
- Time gap handling (24h+ recovery)
- Anti-stutter buffering
- Logical time advancement

✅ **Edge Cases**
- Zero energy FALLBACK path
- Max energy clamping
- Rapid-fire step calls
- Large time deltas

✅ **Integration**
- Full degradation cycles
- Long-running stability (100+ steps)
- Cross-component interaction

### Coverage Gaps (Future)

❌ **Not yet tested:**
- Chronos context note generation
- Actual model.generate() calls
- ResonanceVerifier with real embeddings
- Formal specification proofs
- Failure scenario injection

---

## Best Practices

### Writing New Tests

1. **Use setUp() for fixtures**
   ```python
   def setUp(self):
       self.cfg = ControllerConfig()
       self.state = SystemState.initial(0.0)
   ```

2. **Use fast config (α=1.0) for metric tests**
   ```python
   cfg = ControllerConfig(policy=PolicyConfig(smoothing_alpha=1.0))
   ```

3. **Test state transitions explicitly**
   ```python
   self.assertEqual(new_state.mode, OperationalMode.EMERGENCY)
   self.assertEqual(new_state.energy, 7)
   ```

4. **Verify invariants in loops**
   ```python
   for i in range(100):
       state = step(metrics, state, float(i), cfg)
       self.assertGreaterEqual(state.energy, 0)
       self.assertLessEqual(state.energy, 10)
   ```

### Benchmarking

1. **Always use warmup=True**
   - Allows JIT compilation, caching
   - First 10 iterations are discarded

2. **Force garbage collection before timing**
   ```python
   gc.collect()
   # ... measure ...
   ```

3. **Measure nanoseconds for fine-grained performance**
   - Use `time.perf_counter_ns()` for precision
   - Report both min/max and average

4. **Run multiple iterations**
   - At least 1,000 for ~1ns operations
   - 100 for ~10μs operations
   - 10 for ~100μs operations

---

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.8', '3.9', '3.10', '3.11']
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install numpy sentence-transformers matplotlib
    
    - name: Run tests
      run: python run_tests.py
    
    - name: Run benchmarks
      run: python tests/benchmarks.py
```

### Local CI Check

```bash
#!/bin/bash
# check.sh - Run all checks before commit

echo "Running tests..."
python run_tests.py || exit 1

echo "Running benchmarks..."
python tests/benchmarks.py || exit 1

echo "✅ All checks passed"
```

---

## Troubleshooting

### Tests fail with "No module named 'arctl'"

**Solution:** Run from project root
```bash
cd arctl-project
python -m unittest discover tests
```

### Import errors in tests

**Solution:** Ensure `__init__.py` exists in all packages
```bash
touch tests/__init__.py
```

### Benchmarks show unrealistic times

**Solution:** 
- Disable background processes
- Run on idle system
- Use `time.perf_counter()` not `time.time()`
- Check that warmup is running

### sentence_transformers not installed

**Solution:** Benchmarks skip gracefully, but to enable:
```bash
pip install sentence-transformers
```

---

## Performance Goals

Based on benchmarks, acceptable ranges:

| Operation | Target | Acceptable Range |
|-----------|--------|-----------------|
| Single step() | < 1μs | 500-2000 ns |
| Full cycle (3 steps) | < 3μs | 1500-5000 ns |
| Lexical metrics | < 50μs | 10-100 μs |
| Resonance verify | < 100ms | 50-200ms |
| 1000 steps | < 1s | 0.5-2s |

---

## Reporting Issues

When reporting test failures:

1. **Include Python version**
   ```bash
   python --version
   ```

2. **Run with verbose output**
   ```bash
   python -m unittest tests.test_core -v
   ```

3. **Capture full traceback**
   ```bash
   python run_tests.py 2>&1 | tee test_output.log
   ```

4. **Document the failure**
   - Which test failed
   - Expected vs actual
   - Environment details
   - Reproducible steps

---

**Happy testing!** 🚀
