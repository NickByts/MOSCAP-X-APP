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

MINIMUM_PLATEAU_POINTS = 5


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

        Reported as the MEDIAN plateau capacitance -- robust
        against transition leakage, measurement noise, and
        isolated outliers near the accumulation boundary.
        Always derived from the measured C-V plateau; never
        calculated from oxide thickness or a theoretical
        dielectric constant.

    confidence : float
        Confidence score of the underlying plateau detection
        (unchanged from DirectedPlateauResult.confidence).

    plateau : PlateauCandidate
        The full detected plateau, including its raw measured
        capacitance values.

    mean_capacitance : float
        Arithmetic mean of the plateau capacitance. Kept for
        diagnostics/comparison only -- no longer the reported
        Cox value.

    median_capacitance : float
        Same value as `cox`, exposed under an explicit name so
        callers don't have to know that `cox` is a median.

    standard_deviation : float
        Sample standard deviation (ddof=1) of the plateau
        capacitance.

    coefficient_of_variation : float
        |standard_deviation / mean_capacitance| for the plateau.

    plateau_point_count : int
        Number of measured points making up the plateau.
    """

    cox: float

    confidence: float

    plateau: PlateauCandidate

    mean_capacitance: float

    median_capacitance: float

    standard_deviation: float

    coefficient_of_variation: float

    plateau_point_count: int


def calculate_cox(
    result: DirectedPlateauResult,
) -> CoxResult:
    """
    Extract oxide capacitance from the detected
    accumulation plateau.

    Cox is reported as the median of the measured plateau
    capacitance values (robust against transition-boundary
    leakage, noise, and isolated outliers). The arithmetic mean,
    standard deviation, coefficient of variation, and point
    count are carried through as diagnostics -- the latter three
    are reused directly from the plateau detector rather than
    recomputed, since they were already calculated from the same
    measured points.

    Raises
    ------
    ValueError
        If the plateau has fewer than MINIMUM_PLATEAU_POINTS
        points, or if the resulting median capacitance is not
        finite or not positive.
    """

    plateau = result.accumulation_plateau

    if plateau.point_count < MINIMUM_PLATEAU_POINTS:
        raise ValueError(
            f"Accumulation plateau has only {plateau.point_count} "
            f"point(s); at least {MINIMUM_PLATEAU_POINTS} are "
            "required for a reliable Cox extraction."
        )

    median_capacitance = float(
        np.median(plateau.capacitance_values)
    )

    if not np.isfinite(median_capacitance):
        raise ValueError(
            "Extracted oxide capacitance (median) is not finite."
        )

    if median_capacitance <= 0.0:
        raise ValueError(
            "Extracted oxide capacitance (median) must be positive."
        )

    return CoxResult(
        cox=median_capacitance,
        confidence=result.confidence,
        plateau=plateau,
        mean_capacitance=plateau.mean_capacitance,
        median_capacitance=median_capacitance,
        standard_deviation=plateau.standard_deviation,
        coefficient_of_variation=plateau.coefficient_of_variation,
        plateau_point_count=plateau.point_count,
    )