"""Automatic semiconductor flat-band capacitance extraction."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

try:
    from .debye_length_extractor import (
        DebyeLengthResult,
    )

except ImportError:

    from extraction_new.debye_length_extractor import (
        DebyeLengthResult,
    )

    from extraction_new.measurement_context import (
        MeasurementContext,
    )

@dataclass(frozen=True, slots=True)
class CsfbResult:
    csfb_f: float

    @property
    def csfb(self) -> float:
        return self.csfb_f

def calculate_csfb(
    debye: DebyeLengthResult,
    area_cm2: float,
    *,
    permittivity_f_per_cm: float,
) -> CsfbResult:
    """
    Calculate semiconductor flat-band capacitance.

    Formula
    -------

        CsFB = εs A / LD
    """

    epsilon_s = float(
        permittivity_f_per_cm
    )

    ld = float(
        debye.debye_length
    )

    area = float(
        area_cm2
    )

    _validate_inputs(
        epsilon_s,
        ld,
        area,
    )

    csfb = (
        epsilon_s
        * area
        / ld
    )

    if (
        not np.isfinite(csfb)
        or csfb <= 0.0
    ):
        raise ValueError(
            "Calculated CsFB is non-physical."
        )

    return CsfbResult(
        csfb_f=float(csfb),
    )


def _validate_inputs(
    permittivity: float,
    ld: float,
    area: float,
) -> None:

    if permittivity <= 0.0:
        raise ValueError(
            "Semiconductor permittivity must be greater than zero."
        )

    if ld <= 0.0:
        raise ValueError(
            "Debye length must be greater than zero."
        )

    if area <= 0.0:
        raise ValueError(
            "Device area must be greater than zero."
        )