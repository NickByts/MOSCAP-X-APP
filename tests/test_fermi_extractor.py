"""Tests for Phase 2 Fermi-potential extraction."""

from __future__ import annotations

import unittest

import numpy as np

from extraction_new.fermi_extractor import calculate_fermi_potential
from extraction_new.phase2_validation import (
    BOLTZMANN_CONSTANT_J_PER_K,
    ELEMENTARY_CHARGE_C,
)


class FermiExtractorTestCase(unittest.TestCase):
    """Validate Fermi potential and logarithm safeguards."""

    def test_calculate_fermi_potential_at_room_temperature(self) -> None:
        expected = (
            BOLTZMANN_CONSTANT_J_PER_K
            * 300.0
            / ELEMENTARY_CHARGE_C
            * np.log(1.0e16 / 9.65e9)
        )

        result = calculate_fermi_potential(
            doping_cm3=1.0e16,
            intrinsic_concentration_cm3=9.65e9,
            temperature_k=300.0,
        )

        self.assertAlmostEqual(result, expected)

    def test_rejects_zero_intrinsic_concentration(self) -> None:
        with self.assertRaisesRegex(ValueError, "greater than zero"):
            calculate_fermi_potential(
                doping_cm3=1.0e16,
                intrinsic_concentration_cm3=0.0,
                temperature_k=300.0,
            )


if __name__ == "__main__":
    unittest.main()
