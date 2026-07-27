"""Automatic Debye length extraction for MOSCAP-X."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .phase2_constants import (
    BOLTZMANN_CONSTANT_J_PER_K,
    ELEMENTARY_CHARGE_C,
)

@dataclass(frozen=True, slots=True)
class DebyeLengthResult:
    """
    Automatic Debye length extraction result.
    """

    debye_length: float


# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------

def calculate_debye_length(
    doping_cm3: float,
    temperature_k: float,
    *,
    permittivity_f_per_cm: float,
) -> DebyeLengthResult:
    """
    Calculate the Debye length.

    Formula
    -------

              εs kT
    LD = √ ------------
            q² N

    where

        εs = εr ε0
    """

    temperature = float(temperature_k)

    concentration = float(doping_cm3)

    epsilon_s = float(permittivity_f_per_cm)

    _validate_inputs(
        epsilon_s,
        temperature,
        concentration,
    )

    numerator = (
        epsilon_s
        * BOLTZMANN_CONSTANT_J_PER_K
        * temperature
    )

    denominator = (
        ELEMENTARY_CHARGE_C**2
        * concentration
    )

    debye_length = np.sqrt(
        numerator / denominator
    )

    if (
        not np.isfinite(debye_length)
        or debye_length <= 0.0
    ):
        raise ValueError(
            "Calculated Debye length is non-physical."
        )

    return DebyeLengthResult(
        debye_length=float(debye_length),
    )


# ---------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------

def _validate_inputs(
    permittivity: float,
    temperature: float,
    concentration: float,
) -> None:

    if permittivity <= 0.0:
        raise ValueError(
            "Semiconductor permittivity must be greater than zero."
        )

    if temperature <= 0.0:
        raise ValueError(
            "Temperature must be greater than zero."
        )

    if concentration <= 0.0:
        raise ValueError(
            "Doping concentration must be greater than zero."
        )