"""
Integration tests for ARCTL system.

Tests interaction between:
- Kernel state machine
- Lexical metrics
- Resonance verification
- Real-world scenarios
"""

import unittest
from dataclasses import replace

from arctl.core.kernel import ControllerConfig, SystemState, step
from arctl.core.states import OperationalMode, RawMetrics, TimeState
from arctl.verification.lexical import LexicalMetrics
from arctl.verification.metrics import ResonanceVerifier


class TestKernelWithLexicalMetrics(unittest.TestCase):
    """Integration test: kernel + lexical metrics"""

    def test_repetition_triggers_emergency(self):
        """High lexical repetition should trigger EMERGENCY mode"""
        cfg = ControllerConfig()
        state = SystemState.initial(0.0)

        # Highly repetitive token sequence
        repetitive_tokens = ["the", "the", "the", "the", "the"] * 10

        # Calculate metrics from tokens
        lex_metrics = LexicalMetrics.calculate(repetitive_tokens, window=50)

        # Should have high repetition
        self.assertGreater(lex_metrics.repetition, 0.5)

        # Convert to RawMetrics
        metrics = RawMetrics(
            entropy=lex_metrics.entropy,
            divergence=lex_metrics.divergence,
            repetition=lex_metrics.repetition
        )

        # Use fast config for instant updates
        cfg_fast = ControllerConfig(
            policy=replace(cfg.policy, smoothing_alpha=1.0)
        )

        # Step with high repetition
        new_state = step(metrics, state, 1.0, cfg_fast)

        # Should transition to EMERGENCY
        self.assertEqual(new_state.mode, OperationalMode.EMERGENCY)

    def test_diverse_tokens_stay_standard(self):
        """Diverse token sequence (low repetition) should keep system in STANDARD"""
        cfg = ControllerConfig(
            policy=replace(ControllerConfig().policy, smoothing_alpha=1.0)
        )
        state = SystemState.initial(0.0)

        # Many unique tokens → low n-gram repetition
        diverse_tokens = [f"w{i}" for i in range(80)]
        lex_metrics = LexicalMetrics.calculate(diverse_tokens, window=50)

        metrics = RawMetrics(
            entropy=lex_metrics.entropy,
            divergence=lex_metrics.divergence,
            repetition=lex_metrics.repetition
        )
        new_state = step(metrics, state, 1.0, cfg)

        self.assertLessEqual(new_state.s_repetition, cfg.policy.repetition_threshold,
                             "unique token sequence should have low repetition")
        self.assertEqual(new_state.mode, OperationalMode.STANDARD)


class TestFullWorkflow(unittest.TestCase):
    """Integration test: complete workflow"""

    def test_degradation_sequence(self):
        """
        Test realistic degradation sequence:
        STANDARD → repetition rises → EMERGENCY → timeout → COOLDOWN → STANDARD
        """
        cfg = ControllerConfig(
            policy=replace(ControllerConfig().policy, smoothing_alpha=1.0)
        )
        state = SystemState.initial(0.0)
        now = 0.0

        # Phase 1: Normal operation (low repetition)
        low_rep_metrics = RawMetrics(entropy=0.6, divergence=0.1, repetition=0.2)
        for i in range(5):
            state = step(low_rep_metrics, state, now + i * 0.5, cfg)

        self.assertEqual(state.mode, OperationalMode.STANDARD)
        now = 5 * 0.5

        # Phase 2: Repetition rises - trigger EMERGENCY
        # With alpha=1.0, instant update, so high rep on first step
        metrics_high = RawMetrics(entropy=0.5, divergence=0.0, repetition=0.8)
        state = step(metrics_high, state, now + 1.0, cfg)

        # Should have triggered EMERGENCY by now
        self.assertEqual(state.mode, OperationalMode.EMERGENCY)
        emergency_energy = state.energy
        now = now + 1.0

        # Phase 3: Wait for EMERGENCY timeout (need > 5.0 seconds in mode)
        # Use loop like test_core to accumulate logical time
        normal_metrics = RawMetrics(entropy=0.5, divergence=0.0, repetition=0.3)
        for i in range(55):  # 55 * 0.1 = 5.5 seconds
            state = step(normal_metrics, state, now + float(i) * 0.1, cfg)

        self.assertEqual(state.mode, OperationalMode.COOLDOWN)
        now_after_emergency = now + 5.5

        # Phase 4: Wait for COOLDOWN duration (need > 2.0 seconds in mode)
        for i in range(25):  # 25 * 0.1 = 2.5 seconds
            state = step(normal_metrics, state, now_after_emergency + float(i) * 0.1, cfg)

        self.assertEqual(state.mode, OperationalMode.STANDARD)
        self.assertEqual(state.energy, emergency_energy + 1)  # Recovered 1


class TestResonanceIntegration(unittest.TestCase):
    """Integration test: kernel + resonance verification"""

    def test_stable_resonance_patterns(self):
        """Verify resonance detector can assess mode consistency"""
        verifier = ResonanceVerifier()

        # Responses that should be similar across modes
        consistent_responses = {
            "calm": "PWM is a technique that controls analog circuits using digital pulses.",
            "joy": "PWM is a fun technique that controls circuits with digital pulses!",
            "vigilance": "PWM controls circuits through digital pulses (ensure proper filtering).",
            "wonder": "PWM, a fascinating technique, controls circuits via digital pulses."
        }

        # Verify consistency
        result = verifier.verify(consistent_responses)

        # Should have reasonable stability (though exact threshold depends on model)
        self.assertIn("resonance_score", result)
        self.assertIn("is_stable", result)
        self.assertTrue(result["resonance_score"] >= 0.0)
        self.assertTrue(result["resonance_score"] <= 1.0)


class TestLongRunningBehavior(unittest.TestCase):
    """Integration test: system behavior over extended runs"""

    def test_100_step_stability(self):
        """Verify system remains stable over 100 steps"""
        cfg = ControllerConfig()
        state = SystemState.initial(0.0)

        metrics_cycling = [
            RawMetrics(entropy=0.5, divergence=0.0, repetition=0.2),  # normal
            RawMetrics(entropy=0.5, divergence=0.0, repetition=0.8),  # high rep
        ]

        for i in range(100):
            metrics = metrics_cycling[i % 2]
            state = step(metrics, state, float(i), cfg)

            # Invariants
            self.assertGreaterEqual(state.energy, 0)
            self.assertLessEqual(state.energy, cfg.policy.max_energy)
            self.assertTrue(isinstance(state.mode, OperationalMode))
            self.assertGreaterEqual(state.s_entropy, 0.0)
            self.assertLessEqual(state.s_entropy, 1.0)

    def test_energy_depletion_reaches_fallback(self):
        """Over many EMERGENCY transitions, energy depletes to FALLBACK"""
        cfg = ControllerConfig(
            policy=replace(ControllerConfig().policy, smoothing_alpha=1.0)
        )
        state = SystemState.initial(0.0)
        high_rep = RawMetrics(entropy=0.5, divergence=0.0, repetition=0.9)
        low_rep = RawMetrics(entropy=0.5, divergence=0.0, repetition=0.1)
        emergency_count = 0
        fallback_reached = False
        now = 0.0

        # Each EMERGENCY needs 55 steps (0.1s each) to timeout; COOLDOWN needs 25 steps
        for _ in range(20):  # 5+ full cycles to go 10→7→4→1→FALLBACK
            if state.mode == OperationalMode.FALLBACK:
                fallback_reached = True
                break
            if state.mode == OperationalMode.STANDARD:
                state = step(high_rep, state, now + 1.0, cfg)
                if state.mode == OperationalMode.EMERGENCY:
                    emergency_count += 1
                now += 1.0
            elif state.mode == OperationalMode.EMERGENCY:
                for i in range(55):
                    state = step(low_rep, state, now + i * 0.1, cfg)
                now += 5.5
            elif state.mode == OperationalMode.COOLDOWN:
                for i in range(25):
                    state = step(low_rep, state, now + i * 0.1, cfg)
                now += 2.5

        self.assertGreaterEqual(emergency_count, 3, "should trigger at least 3 emergencies")
        self.assertTrue(fallback_reached, "energy depletion must lead to FALLBACK")


class TestErrorRecovery(unittest.TestCase):
    """Integration test: system behavior with edge cases"""

    def test_rapid_fire_steps(self):
        """System handles rapid-fire step() calls (anti-stutter)"""
        cfg = ControllerConfig()
        state = SystemState.initial(0.0)
        metrics = RawMetrics(entropy=0.5, divergence=0.0, repetition=0.5)

        # Call step many times with tiny deltas
        for _ in range(1000):
            state = step(metrics, state, state.last_call_time + 0.0001, cfg)

        # System should handle this gracefully
        self.assertIsNotNone(state)
        self.assertEqual(state.mode, OperationalMode.STANDARD)

    def test_time_gap_handling(self):
        """System properly handles time gaps (24h+ inactivity) — conservative reset (+1 only)"""
        cfg = ControllerConfig()
        state = SystemState.initial(0.0)._replace(energy=0)
        metrics = RawMetrics(entropy=0.5, divergence=0.0, repetition=0.1)

        # Zero energy
        self.assertEqual(state.energy, 0)

        # Large time gap (24h+)
        new_state = step(metrics, state, 86400 + 1, cfg)

        # Conservative restoration: +1 only (Review 2.0), not full recharge
        self.assertEqual(new_state.energy, 1)
        self.assertTrue(new_state.reset_used)
        self.assertEqual(new_state.time_state, TimeState.GAP)


if __name__ == '__main__':
    unittest.main()
