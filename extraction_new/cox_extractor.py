"""Automatic oxide capacitance (Cox) extraction for MOSCAP-X Phase 2."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

try:
    from .plateau_detector import (
        DirectedPlateauResult,
        PlateauCandidate,
    )
except ImportError:
    from extraction_new.plateau_detector import (
        DirectedPlateauResult,
        PlateauCandidate,
    )


@dataclass(frozen=True, slots=True)
class CoxResult:
    """
    Automatic oxide capacitance extraction result.

    Attributes
    ----------
    cox : float
        Total oxide capacitance (F) extracted from the
        accumulation plateau. This is the measured device
        capacitance, not capacitance per unit area.
    """

    cox: float

    confidence: float

    plateau: PlateauCandidate


def calculate_cox(
    result: DirectedPlateauResult,
) -> CoxResult:
    """
    Extract oxide capacitance from the detected
    accumulation plateau.
    """

    plateau = result.accumulation_plateau

    cox = float(
        plateau.mean_capacitance
    )

    if not np.isfinite(cox):
        raise ValueError(
            "Extracted oxide capacitance is not finite."
        )

    if cox <= 0.0:
        raise ValueError(
            "Extracted oxide capacitance must be positive."
        )

    return CoxResult(
        cox=cox,
        confidence=result.confidence,
        plateau=plateau,
    )