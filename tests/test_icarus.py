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
        with self.assertRaises(Exception):
            cfg.stability_index = 0.5  # type: ignore


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
        """Entropy 0.9 is corrected toward stability_index."""
        result = calculate_tunneling_vector(0.9, self.cfg)
        # 0.9 - (0.9 - 0.95)*0.5 = 0.9 + 0.025 = 0.925
        self.assertAlmostEqual(result, 0.925, places=5)

    def test_low_entropy_corrected(self):
        """Entropy 0.5 is corrected toward stability_index."""
        result = calculate_tunneling_vector(0.5, self.cfg)
        # 0.5 - (0.5 - 0.95)*0.5 = 0.5 + 0.225 = 0.725
        self.assertAlmostEqual(result, 0.725, places=5)

    def test_result_in_bounds(self):
        """All results are within [0.0, 1.0]."""
        for entropy in [0.0, 0.3, 0.5, 0.9, 0.95, 1.0, 1.5]:
            result = calculate_tunneling_vector(entropy, self.cfg)
            self.assertGreaterEqual(result, 0.0, f"entropy={entropy}")
            self.assertLessEqual(result, 1.0, f"entropy={entropy}")


if __name__ == "__main__":
    unittest.main()
