"""
Performance benchmarks for ARCTL kernel.

Measures:
- Single step execution time
- Memory usage
- State machine throughput
- Metric calculation performance
"""

import time
import gc
import sys
from typing import Callable, List, Tuple
from dataclasses import dataclass

from arctl.core.kernel import step, ControllerConfig, SystemState
from arctl.core.states import RawMetrics, OperationalMode
from arctl.verification.lexical import LexicalMetrics
from arctl.verification.metrics import ResonanceVerifier


@dataclass
class BenchmarkResult:
    """Result of a benchmark run"""
    name: str
    iterations: int
    total_time_s: float
    ops_per_sec: float
    min_time_ns: float
    max_time_ns: float
    avg_time_ns: float
    
    def __str__(self) -> str:
        return (
            f"{self.name:50s} | "
            f"{self.ops_per_sec:>10.0f} ops/s | "
            f"{self.avg_time_ns:>8.0f} ns | "
            f"[{self.min_time_ns:.0f}-{self.max_time_ns:.0f}] ns"
        )


class Benchmarker:
    """Helper for running benchmarks"""
    
    @staticmethod
    def benchmark(
        name: str,
        func: Callable,
        iterations: int = 1000,
        warmup: bool = True
    ) -> BenchmarkResult:
        """
        Run a benchmark on a function.
        
        Args:
            name: Name for the benchmark
            func: Function to benchmark (should return nothing)
            iterations: Number of times to run
            warmup: Run 10 iterations first for JIT/caching
        
        Returns:
            BenchmarkResult with timing information
        """
        # Warmup
        if warmup:
            for _ in range(10):
                func()
        
        # Force garbage collection
        gc.collect()
        
        # Measure
        times = []
        start = time.perf_counter()
        
        for _ in range(iterations):
            t0 = time.perf_counter_ns()
            func()
            t1 = time.perf_counter_ns()
            times.append(t1 - t0)
        
        end = time.perf_counter()
        total_time = end - start
        
        # Statistics
        min_ns = min(times)
        max_ns = max(times)
        avg_ns = sum(times) / len(times)
        ops_per_sec = iterations / total_time
        
        return BenchmarkResult(
            name=name,
            iterations=iterations,
            total_time_s=total_time,
            ops_per_sec=ops_per_sec,
            min_time_ns=min_ns,
            max_time_ns=max_ns,
            avg_time_ns=avg_ns
        )


# ============================================================================
# BENCHMARKS
# ============================================================================

def benchmark_single_step():
    """Benchmark: Single step() execution"""
    cfg = ControllerConfig()
    state = SystemState.initial(0.0)
    metrics = RawMetrics(entropy=0.5, divergence=0.0, repetition=0.3)
    
    def func():
        step(metrics, state, 1.0, cfg)
    
    return Benchmarker.benchmark("Single step() execution", func, iterations=10000)


def benchmark_state_machine_cycle():
    """Benchmark: Full state machine cycle (STANDARD→EMERGENCY→COOLDOWN→STANDARD)"""
    cfg = ControllerConfig()
    state = SystemState.initial(0.0)
    metrics_high = RawMetrics(entropy=0.5, divergence=0.0, repetition=0.9)
    metrics_low = RawMetrics(entropy=0.5, divergence=0.0, repetition=0.2)
    
    def func():
        s = state
        # STANDARD → EMERGENCY
        s = step(metrics_high, s, 1.0, cfg)
        # EMERGENCY → COOLDOWN
        s = step(metrics_low, s, 7.0, cfg)
        # COOLDOWN → STANDARD
        s = step(metrics_low, s, 10.0, cfg)
    
    return Benchmarker.benchmark("Full state cycle (3 steps)", func, iterations=5000)


def benchmark_fallback_stability():
    """Benchmark: Verify FALLBACK doesn't regress performance"""
    cfg = ControllerConfig()
    fallback_state = SystemState.initial(0.0)._replace(
        mode=OperationalMode.FALLBACK,
        energy=0
    )
    metrics = RawMetrics(entropy=0.5, divergence=0.0, repetition=0.5)
    
    def func():
        step(metrics, fallback_state, 1.0, cfg)
    
    return Benchmarker.benchmark("FALLBACK state (early return)", func, iterations=50000)


def benchmark_lexical_metrics():
    """Benchmark: Lexical metrics calculation"""
    tokens = ["the", "quick", "brown", "fox", "jumps"] * 10
    
    def func():
        LexicalMetrics.calculate(tokens, window=50)
    
    return Benchmarker.benchmark("Lexical metrics calculation", func, iterations=10000)


def benchmark_metric_smoothing():
    """Benchmark: Metric smoothing with various alpha values"""
    cfg = ControllerConfig()
    state = SystemState.initial(0.0)
    metrics = RawMetrics(entropy=0.9, divergence=0.8, repetition=0.7)
    
    def func():
        step(metrics, state, 1.0, cfg)
    
    return Benchmarker.benchmark("Metric smoothing (alpha=0.3)", func, iterations=50000)


def benchmark_resonance_verification():
    """Benchmark: Resonance verifier (expensive operation)"""
    verifier = ResonanceVerifier()
    
    responses = {
        "calm": "This is a calm response about the topic.",
        "joy": "This is a joyful response about the topic!",
        "vigilance": "This is a critical response about the topic.",
        "wonder": "This is a philosophical response about the topic?"
    }
    
    def func():
        verifier.verify(responses)
    
    return Benchmarker.benchmark("Resonance verification", func, iterations=100)


def benchmark_energy_restoration():
    """Benchmark: Energy restoration on time gaps"""
    cfg = ControllerConfig()
    depleted_state = SystemState.initial(0.0)._replace(energy=2)
    metrics = RawMetrics(entropy=0.5, divergence=0.0, repetition=0.1)
    
    def func():
        # 24+ hour gap triggers energy restoration
        step(metrics, depleted_state, 86400 + 1, cfg)
    
    return Benchmarker.benchmark("Energy restoration (24h+ gap)", func, iterations=10000)


def benchmark_many_fast_steps():
    """Benchmark: Many rapid steps (anti-stutter buffer accumulation)"""
    cfg = ControllerConfig()
    state = SystemState.initial(0.0)
    metrics = RawMetrics(entropy=0.5, divergence=0.0, repetition=0.1)
    
    step_count = [0]
    
    def func():
        nonlocal state
        # Rapid calls with tiny deltas (most will be buffered by anti-stutter)
        for i in range(100):
            state = step(metrics, state, state.last_call_time + 0.001, cfg)
    
    return Benchmarker.benchmark("100 rapid steps (anti-stutter)", func, iterations=100)


def benchmark_time_state_transitions():
    """Benchmark: Different time states (SYNC, LAG, GAP)"""
    cfg = ControllerConfig()
    state = SystemState.initial(0.0)
    metrics = RawMetrics(entropy=0.5, divergence=0.0, repetition=0.1)
    
    times = [30.0, 3600.0, 86400 + 1]  # SYNC, LAG, GAP
    
    def func():
        for t in times:
            step(metrics, state, t, cfg)
    
    return Benchmarker.benchmark("Time state transitions (SYNC/LAG/GAP)", func, iterations=5000)


def benchmark_config_construction():
    """Benchmark: Configuration object creation"""
    def func():
        ControllerConfig()
    
    return Benchmarker.benchmark("Config construction", func, iterations=100000)


def benchmark_state_copy_operations():
    """Benchmark: State._replace() operations (used in transitions)"""
    state = SystemState.initial(0.0)
    
    def func():
        new_state = state._replace(
            energy=7,
            mode=OperationalMode.EMERGENCY,
            active_config=state.active_config
        )
    
    return Benchmarker.benchmark("State._replace() (copy on write)", func, iterations=100000)


# ============================================================================
# MEMORY BENCHMARKS
# ============================================================================

def benchmark_memory_usage():
    """Benchmark: Memory usage of core objects"""
    print("\n" + "=" * 80)
    print("MEMORY USAGE")
    print("=" * 80)
    
    # Single state
    state = SystemState.initial(0.0)
    state_size = sys.getsizeof(state)
    print(f"SystemState size:        {state_size:>10} bytes")
    
    # Config
    cfg = ControllerConfig()
    cfg_size = sys.getsizeof(cfg)
    print(f"ControllerConfig size:   {cfg_size:>10} bytes")
    
    # Metrics
    metrics = RawMetrics(entropy=0.5, divergence=0.0, repetition=0.3)
    metrics_size = sys.getsizeof(metrics)
    print(f"RawMetrics size:         {metrics_size:>10} bytes")
    
    # Array of states (1000 steps)
    states = [state for _ in range(1000)]
    states_memory = sum(sys.getsizeof(s) for s in states)
    print(f"\n1000 states total:       {states_memory:>10} bytes ({states_memory/1024:.2f} KB)")


# ============================================================================
# SCALING TESTS
# ============================================================================

def benchmark_scaling():
    """Test how performance scales with number of steps"""
    print("\n" + "=" * 80)
    print("SCALING TEST: Performance vs Number of Steps")
    print("=" * 80)
    
    cfg = ControllerConfig()
    state = SystemState.initial(0.0)
    metrics = RawMetrics(entropy=0.5, divergence=0.0, repetition=0.3)
    
    step_counts = [10, 100, 1000, 10000]
    
    for num_steps in step_counts:
        def func():
            s = state
            for i in range(num_steps):
                s = step(metrics, s, float(i), cfg)
        
        result = Benchmarker.benchmark(
            f"Execute {num_steps} steps",
            func,
            iterations=max(1, 1000 // (num_steps // 10)),
            warmup=False
        )
        print(result)


# ============================================================================
# MAIN BENCHMARK SUITE
# ============================================================================

def run_all_benchmarks():
    """Run complete benchmark suite"""
    print("\n" + "=" * 80)
    print("ARCTL PERFORMANCE BENCHMARKS")
    print("=" * 80)
    print(f"{'Benchmark':<50} | {'Throughput':<12} | {'Time (ns)':<10} | {'Range':<20}")
    print("-" * 80)
    
    results: List[BenchmarkResult] = []
    
    # Core benchmarks
    results.append(benchmark_single_step())
    results.append(benchmark_state_machine_cycle())
    results.append(benchmark_fallback_stability())
    results.append(benchmark_lexical_metrics())
    results.append(benchmark_metric_smoothing())
    results.append(benchmark_energy_restoration())
    results.append(benchmark_many_fast_steps())
    results.append(benchmark_time_state_transitions())
    results.append(benchmark_config_construction())
    results.append(benchmark_state_copy_operations())
    
    # Try resonance (might fail if sentence_transformers not installed)
    try:
        results.append(benchmark_resonance_verification())
    except ImportError:
        print("⚠️  Skipping resonance benchmark (sentence_transformers not installed)")
    
    print()
    for result in results:
        print(result)
    
    # Memory benchmarks
    benchmark_memory_usage()
    
    # Scaling tests
    benchmark_scaling()
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total benchmarks run: {len(results)}")
    
    # Find best/worst
    if results:
        fastest = min(results, key=lambda r: r.avg_time_ns)
        slowest = max(results, key=lambda r: r.avg_time_ns)
        
        print(f"\nFastest:  {fastest.name:<40} {fastest.avg_time_ns:>8.0f} ns")
        print(f"Slowest:  {slowest.name:<40} {slowest.avg_time_ns:>8.0f} ns")
        
        # Throughput analysis
        best_throughput = max(results, key=lambda r: r.ops_per_sec)
        print(f"\nBest throughput: {best_throughput.name:<35} {best_throughput.ops_per_sec:>10.0f} ops/s")


if __name__ == '__main__':
    run_all_benchmarks()
