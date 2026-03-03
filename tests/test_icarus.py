# test_icarus.py
"""Unit tests for Project Icarus stability anchor (arctl.core.icarus)."""
import unittest

from arctl.core.icarus import IcarusConfig, calculate_tunneling_vector


class TestIcarusConfig(unittest.TestCase):
    """Tests for IcarusConfig defaults."""

    def test_stability_index_in_bounds(self):
        """Stability_Index is 0.95 for arctl entropy bounds [0.0, 1.0]."""
        cfg = IcarusConfig()
        self.assertEqual(cfg.stability_index, 0.95)

    def test_config_immutable(self):
        """IcarusConfig is frozen (immutable)."""
        cfg = IcarusConfig()
        with self.assertRaises(AttributeError):
           cfg.stability_index = 0.5


class TestTunnelingVector(unittest.TestCase):
    """Tests for calculate_tunneling_vector."""

    def setUp(self):
        self.cfg = IcarusConfig()

    def test_zero_entropy_unchanged(self):
        """Entropy 0.0 returns 0.0 (no correction)."""
        self.assertEqual(calculate_tunneling_vector(0.0, self.cfg), 0.0)

    def test_above_one_clamped(self):
        """Entropy > 1.0 is clamped to 1.0."""
        self.assertEqual(calculate_tunneling_vector(1.5, self.cfg), 1.0)

    def test_high_entropy_corrected(self):
        """Entropy > 0.8 triggers tunneling and is reduced."""
        cfg = IcarusConfig(stability_index=0.95)
        # current_entropy = 0.9. Deviation = abs(0.9 - 0.95) = 0.05.
        # Correction = 0.05 * 0.5 = 0.025. Result = 0.9 - 0.025 = 0.875
        result = calculate_tunneling_vector(0.9, cfg)
        self.assertAlmostEqual(result, 0.875, places=5)

    def test_low_entropy_corrected(self):
        """Entropy <= 0.8 does not trigger tunneling. Returns original value."""
        cfg = IcarusConfig(stability_index=0.95)
        # Since 0.5 is not > 0.8, no tunneling occurs. Should return 0.5.
        result = calculate_tunneling_vector(0.5, cfg)
        self.assertAlmostEqual(result, 0.5, places=5)

    def test_result_in_bounds(self):
        """All results are within [0.0, 1.0]."""
        for entropy in [0.0, 0.3, 0.5, 0.9, 0.95, 1.0, 1.5]:
            result = calculate_tunneling_vector(entropy, self.cfg)
            self.assertGreaterEqual(result, 0.0, f"entropy={entropy}")
            self.assertLessEqual(result, 1.0, f"entropy={entropy}")


if __name__ == "__main__":
    unittest.main()
