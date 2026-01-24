"""
Unit tests for ARCTL kernel and state machine.

Tests verify:
- State transitions between modes (STANDARD → EMERGENCY → COOLDOWN → STANDARD)
- FALLBACK terminal absorbing state property
- Energy management and restoration
- Time synchronization (Chronos)
- Metric smoothing
- Physics correctness
"""

import unittest
import time
from typing import Dict, List
from dataclasses import replace

from arctl.core.kernel import step, ControllerConfig, SystemState, TimeConfig, PolicyConfig
from arctl.core.states import RawMetrics, OperationalMode, TimeState
from arctl.verification.lexical import LexicalMetrics
from arctl.verification.metrics import ResonanceVerifier


class TestKernelBasics(unittest.TestCase):
    """Basic kernel functionality tests"""
    
    def setUp(self):
        """Initialize test fixtures"""
        self.cfg = ControllerConfig()
        self.state = SystemState.initial(0.0)
        self.now = 0.0
    
    def test_initial_state(self):
        """Verify initial state properties"""
        self.assertEqual(self.state.mode, OperationalMode.STANDARD)
        self.assertEqual(self.state.energy, 10)
        self.assertEqual(self.state.s_entropy, 0.5)
        self.assertEqual(self.state.logical_time, 0.0)
    
    def test_anti_stutter_mechanism(self):
        """Verify anti-stutter prevents rapid oscillation"""
        metrics = RawMetrics(entropy=0.5, divergence=0.0, repetition=0.5)
        
        # Call with tiny time delta (0.001s < min_step_interval)
        new_state = step(metrics, self.state, 0.001, self.cfg)
        
        # Should not execute - just buffer pending_dt
        self.assertEqual(new_state.step_performed, False)
        self.assertEqual(new_state.active_config, None)
        self.assertAlmostEqual(new_state.pending_dt, 0.001)


class TestStateMachine(unittest.TestCase):
    """Tests for state machine transitions"""
    
    def setUp(self):
        """Initialize test fixtures"""
        # Use alpha=1.0 for instant metric updates (easier to test)
        self.cfg = ControllerConfig(
            policy=PolicyConfig(smoothing_alpha=1.0)
        )
        self.state = SystemState.initial(0.0)
    
    def test_standard_to_emergency_transition(self):
        """STANDARD → EMERGENCY when repetition > threshold"""
        # High repetition (0.9 > 0.6)
        metrics = RawMetrics(entropy=0.5, divergence=0.0, repetition=0.9)
        
        new_state = step(metrics, self.state, 1.0, self.cfg)
        
        # Should transition to EMERGENCY and cost energy
        self.assertEqual(new_state.mode, OperationalMode.EMERGENCY)
        self.assertEqual(new_state.energy, 7)  # 10 - 3
        self.assertEqual(new_state.s_repetition, 0.9)
    
    def test_emergency_to_cooldown_on_timeout(self):
        """EMERGENCY → COOLDOWN after deadlock_timeout"""
        # To properly test timeout, need enough time to accumulate in logical_time
        # dt = min(new_pending, max_step_interval) = min(delta_real, 0.1)
        # If we call with small deltas repeatedly, logical_time advances slowly
        
        cfg = ControllerConfig()
        
        # Start in EMERGENCY at logical_time=0, mode_entry_time=0
        emergency_state = self.state._replace(
            mode=OperationalMode.EMERGENCY,
            mode_entry_time=0.0,
            logical_time=0.0
        )
        
        metrics = RawMetrics(entropy=0.5, divergence=0.0, repetition=0.3)
        
        # Call step() multiple times with 0.1s each (max_step_interval)
        # This advances logical_time by 0.1 each time
        # Need 50+ calls to reach 5+ seconds (deadlock_timeout)
        state = emergency_state
        for i in range(55):  # 55 * 0.1 = 5.5 logical seconds
            state = step(metrics, state, float(i) * 0.1, cfg)
        
        # Should have transitioned to COOLDOWN
        self.assertEqual(state.mode, OperationalMode.COOLDOWN)
    
    def test_cooldown_duration_and_recovery(self):
        """COOLDOWN → STANDARD after duration + energy recovery"""
        # Create state in COOLDOWN with correct entry time
        cooldown_state = self.state._replace(
            mode=OperationalMode.COOLDOWN,
            energy=7,
            mode_entry_time=0.0,
            logical_time=0.0
        )
        
        metrics = RawMetrics(entropy=0.5, divergence=0.0, repetition=0.3)
        cfg = ControllerConfig()
        
        # Step multiple times to accumulate logical time
        # cooldown_duration = 2.0, max_step_interval = 0.1
        # Need 20+ calls to reach 2+ seconds
        state = cooldown_state
        for i in range(25):  # 25 * 0.1 = 2.5 logical seconds
            state = step(metrics, state, float(i) * 0.1, cfg)
        
        # Should transition to STANDARD and recover 1 energy
        self.assertEqual(state.mode, OperationalMode.STANDARD)
        self.assertEqual(state.energy, 8)  # 7 + 1
    
    def test_energy_depletion_leads_to_fallback(self):
        """When energy < emergency_cost, transition to FALLBACK"""
        # Deplete energy to near zero
        depleted_state = self.state._replace(
            mode=OperationalMode.STANDARD,
            energy=2  # < 3 (emergency_cost)
        )
        
        # High repetition triggers emergency attempt
        metrics = RawMetrics(entropy=0.5, divergence=0.0, repetition=0.9)
        
        new_state = step(metrics, depleted_state, 1.0, self.cfg)
        
        # Should transition to FALLBACK (cannot afford EMERGENCY)
        self.assertEqual(new_state.mode, OperationalMode.FALLBACK)
    
    def test_multiple_transitions_cycle(self):
        """Verify full cycle: STANDARD → EMERGENCY → COOLDOWN → STANDARD"""
        state = self.state
        metrics_high = RawMetrics(entropy=0.5, divergence=0.0, repetition=0.9)
        metrics_low = RawMetrics(entropy=0.5, divergence=0.0, repetition=0.2)
        
        # Use config with fast smoothing for this test
        cfg_fast = ControllerConfig(
            policy=replace(self.cfg.policy, smoothing_alpha=1.0)
        )
        
        # Step 1: Trigger EMERGENCY at time > initial (need to pass anti-stutter check)
        state = step(metrics_high, state, 0.02, cfg_fast)  # > min_step_interval (0.01)
        self.assertEqual(state.mode, OperationalMode.EMERGENCY)
        self.assertEqual(state.energy, 7)
        
        # Step 2: Wait for timeout (> 5.0 seconds in mode) → COOLDOWN
        # Need 55+ calls of 0.1s each = 5.5 seconds
        for i in range(1, 56):  # 1 to 55, giving times 0.12 to 5.52
            state = step(metrics_low, state, 0.02 + float(i) * 0.1, cfg_fast)
        self.assertEqual(state.mode, OperationalMode.COOLDOWN)
        
        # Step 3: Wait for cooldown duration (> 2.0 seconds) → STANDARD
        # Continue from 5.52 onwards
        for i in range(1, 26):  # 1 to 25, giving 25 steps of 0.1s = 2.5s
            state = step(metrics_low, state, 5.52 + float(i) * 0.1, cfg_fast)
        self.assertEqual(state.mode, OperationalMode.STANDARD)
        self.assertEqual(state.energy, 8)  # Recovered 1


class TestFallbackTerminal(unittest.TestCase):
    """Tests for FALLBACK terminal absorbing state property"""
    
    def setUp(self):
        """Initialize test fixtures"""
        self.cfg = ControllerConfig()
    
    def test_fallback_is_terminal(self):
        """FALLBACK never transitions out - terminal absorbing state"""
        # Create state in FALLBACK
        fallback_state = SystemState.initial(0.0)._replace(
            mode=OperationalMode.FALLBACK,
            energy=0
        )
        
        metrics_normal = RawMetrics(entropy=0.5, divergence=0.0, repetition=0.2)
        metrics_high = RawMetrics(entropy=0.5, divergence=0.0, repetition=0.9)
        
        # Try 100 steps with various metrics - mode should never change
        state = fallback_state
        for t in range(100):
            state = step(
                metrics_high if t % 2 else metrics_normal,
                state,
                float(t),
                self.cfg
            )
            
            self.assertEqual(
                state.mode,
                OperationalMode.FALLBACK,
                f"FALLBACK was exited at step {t}!"
            )
            self.assertEqual(
                state.energy,
                0,
                f"Energy was modified at step {t}!"
            )
    
    def test_fallback_physics_still_updates(self):
        """Even in FALLBACK, physics metrics are updated"""
        fallback_state = SystemState.initial(0.0)._replace(
            mode=OperationalMode.FALLBACK,
            s_entropy=0.5,
            s_repetition=0.0
        )
        
        # High repetition metric
        metrics = RawMetrics(entropy=0.9, divergence=0.0, repetition=0.8)
        
        new_state = step(metrics, fallback_state, 1.0, self.cfg)
        
        # Mode stays FALLBACK
        self.assertEqual(new_state.mode, OperationalMode.FALLBACK)
        
        # But metrics are updated (with alpha=0.3 default)
        alpha = self.cfg.policy.smoothing_alpha
        expected_entropy = (1 - alpha) * 0.5 + alpha * 0.9
        expected_repetition = (1 - alpha) * 0.0 + alpha * 0.8
        
        self.assertAlmostEqual(new_state.s_entropy, expected_entropy, places=5)
        self.assertAlmostEqual(new_state.s_repetition, expected_repetition, places=5)


class TestEnergyManagement(unittest.TestCase):
    """Tests for energy budget and management"""
    
    def setUp(self):
        """Initialize test fixtures"""
        self.cfg = ControllerConfig()
        self.state = SystemState.initial(0.0)
    
    def test_energy_restoration_on_24h_gap(self):
        """Energy fully restored after 24+ hour gap (TimeState.GAP)"""
        # Deplete energy
        depleted_state = self.state._replace(energy=2)
        
        metrics = RawMetrics(entropy=0.5, divergence=0.0, repetition=0.1)
        
        # Step with large time gap (86400+ seconds = 24+ hours)
        new_state = step(metrics, depleted_state, 86400 + 1, self.cfg)
        
        # Energy should be fully restored
        self.assertEqual(new_state.energy, 10)
        self.assertEqual(new_state.time_state, TimeState.GAP)
    
    def test_energy_clamped_to_bounds(self):
        """Energy is always clamped to [0, max_energy]"""
        # Create state with intentionally high energy (shouldn't happen, but defensive)
        over_state = self.state._replace(energy=15)
        
        metrics = RawMetrics(entropy=0.5, divergence=0.0, repetition=0.1)
        
        new_state = step(metrics, over_state, 1.0, self.cfg)
        
        # Should be clamped to max
        self.assertLessEqual(new_state.energy, self.cfg.policy.max_energy)
        self.assertGreaterEqual(new_state.energy, 0)


class TestMetricSmoothing(unittest.TestCase):
    """Tests for exponential moving average smoothing"""
    
    def test_smoothing_alpha_zero(self):
        """With alpha=0, metrics don't change"""
        cfg = ControllerConfig(
            policy=PolicyConfig(smoothing_alpha=0.0)
        )
        state = SystemState.initial(0.0)._replace(
            s_entropy=0.5,
            s_repetition=0.2
        )
        
        # Very different incoming metrics
        metrics = RawMetrics(entropy=0.95, divergence=0.9, repetition=0.95)
        
        new_state = step(metrics, state, 1.0, cfg)
        
        # With alpha=0, metrics unchanged
        self.assertAlmostEqual(new_state.s_entropy, 0.5)
        self.assertAlmostEqual(new_state.s_repetition, 0.2)
    
    def test_smoothing_alpha_one(self):
        """With alpha=1.0, metrics instantly update"""
        cfg = ControllerConfig(
            policy=PolicyConfig(smoothing_alpha=1.0)
        )
        state = SystemState.initial(0.0)
        
        metrics = RawMetrics(entropy=0.9, divergence=0.8, repetition=0.7)
        
        new_state = step(metrics, state, 1.0, cfg)
        
        # With alpha=1.0, metrics fully update
        self.assertAlmostEqual(new_state.s_entropy, 0.9)
        self.assertAlmostEqual(new_state.s_divergence, 0.8)
        self.assertAlmostEqual(new_state.s_repetition, 0.7)


class TestLexicalMetrics(unittest.TestCase):
    """Tests for lexical analysis (repetition, entropy)"""
    
    def test_repetition_detection(self):
        """High n-gram repetition detected correctly"""
        # Highly repetitive sequence: "A A A A A ..."
        tokens = ["the", "the", "the", "the", "the"]
        
        metrics = LexicalMetrics.calculate(tokens, window=5)
        
        # High repetition (same trigrams)
        self.assertGreater(metrics.repetition, 0.5)
    
    def test_diversity_scoring(self):
        """Vocabulary diversity scored correctly"""
        # Diverse sequence
        diverse = ["the", "quick", "brown", "fox", "jumps"]
        metrics_diverse = LexicalMetrics.calculate(diverse, window=5)
        
        # Repetitive sequence
        repetitive = ["the", "the", "the", "the", "the"]
        metrics_repetitive = LexicalMetrics.calculate(repetitive, window=5)
        
        # Diverse should have higher entropy than repetitive
        self.assertGreater(metrics_diverse.entropy, metrics_repetitive.entropy)


class TestTimeManagement(unittest.TestCase):
    """Tests for time handling and Chronos"""
    
    def setUp(self):
        """Initialize test fixtures"""
        self.cfg = ControllerConfig()
        self.state = SystemState.initial(0.0)
    
    def test_time_state_sync(self):
        """TimeState.SYNC for short gaps (< 60s)"""
        metrics = RawMetrics(entropy=0.5, divergence=0.0, repetition=0.1)
        
        # Small gap
        new_state = step(metrics, self.state, 30.0, self.cfg)
        
        self.assertEqual(new_state.time_state, TimeState.SYNC)
        self.assertEqual(new_state.context_note, "")
    
    def test_time_state_lag(self):
        """TimeState.LAG for medium gaps (60s-24h)"""
        metrics = RawMetrics(entropy=0.5, divergence=0.0, repetition=0.1)
        
        # Gap between 1 and 24 hours
        new_state = step(metrics, self.state, 3600.0, self.cfg)
        
        self.assertEqual(new_state.time_state, TimeState.LAG)
        self.assertIn("TEMPORAL SYNC", new_state.context_note)
    
    def test_time_state_gap(self):
        """TimeState.GAP for large gaps (> 24h)"""
        metrics = RawMetrics(entropy=0.5, divergence=0.0, repetition=0.1)
        
        # Gap > 24 hours
        new_state = step(metrics, self.state, 86400 + 1, self.cfg)
        
        self.assertEqual(new_state.time_state, TimeState.GAP)
        self.assertIn("TEMPORAL SYNC", new_state.context_note)


class TestEdgeCases(unittest.TestCase):
    """Tests for edge cases and boundary conditions"""
    
    def setUp(self):
        """Initialize test fixtures"""
        self.cfg = ControllerConfig()
        self.state = SystemState.initial(0.0)
    
    def test_zero_energy_no_emergency(self):
        """Cannot enter EMERGENCY with zero energy"""
        zero_energy_state = self.state._replace(energy=0)
        
        cfg_fast = ControllerConfig(
            policy=PolicyConfig(smoothing_alpha=1.0)
        )
        
        # High repetition
        metrics = RawMetrics(entropy=0.5, divergence=0.0, repetition=0.9)
        
        new_state = step(metrics, zero_energy_state, 1.0, cfg_fast)
        
        # Should go to FALLBACK, not EMERGENCY
        self.assertEqual(new_state.mode, OperationalMode.FALLBACK)
    
    def test_metric_boundaries(self):
        """Metrics stay in [0, 1] range"""
        # Inject boundary values
        state = self.state._replace(
            s_entropy=1.0,
            s_repetition=0.0
        )
        
        metrics = RawMetrics(entropy=1.0, divergence=0.0, repetition=0.0)
        
        new_state = step(metrics, state, 1.0, self.cfg)
        
        # All metrics should be in [0, 1]
        self.assertGreaterEqual(new_state.s_entropy, 0.0)
        self.assertLessEqual(new_state.s_entropy, 1.0)
        self.assertGreaterEqual(new_state.s_repetition, 0.0)
        self.assertLessEqual(new_state.s_repetition, 1.0)
    
    def test_max_energy_clamping(self):
        """Energy never exceeds max_energy"""
        metrics = RawMetrics(entropy=0.5, divergence=0.0, repetition=0.1)
        
        state = self.state
        for _ in range(100):
            state = step(metrics, state, float(state.logical_time) + 1.0, self.cfg)
            
            # Even with 24h gaps restoring energy, should never exceed max
            self.assertLessEqual(state.energy, self.cfg.policy.max_energy)


if __name__ == '__main__':
    unittest.main()