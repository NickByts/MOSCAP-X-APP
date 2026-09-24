"""Vp extraction for MOSCAP-X Phase 2.

Calculates Vp using the effective density of states and
the semiconductor doping concentration.

For P-Type:
    Vp = (kT/q) * ln(Nv / Na)

For N-Type:
    Vp = (kT/q) * ln(Nc / Nd)
"""

from __future__ import annotations

import numpy as np

try:
    from .phase2_constants import (
        BOLTZMANN_CONSTANT_J_PER_K,
        ELEMENTARY_CHARGE_C,
    )
    from .phase2_validation import (
        validate_finite_positive,
        validate_substrate_type,
        validate_unit,
    )
except ImportError:
    from phase2_constants import (
        BOLTZMANN_CONSTANT_J_PER_K,
        ELEMENTARY_CHARGE_C,
    )
    from phase2_validation import (
        validate_finite_positive,
        validate_substrate_type,
        validate_unit,
    )


def calculate_vp(
    doping_cm3: float,
    temperature_k: float,
    substrate_type: str,
    *,
    nc_cm3: float,
    nv_cm3: float,
    doping_unit: str = "cm^-3",
    temperature_unit: str = "K",
) -> float:
    """
    Calculate Vp for the semiconductor.

    P-Type:
        Vp = (kT/q) * ln(Nv / Na)

    N-Type:
        Vp = (kT/q) * ln(Nc / Nd)

    Parameters
    ----------
    doping_cm3
        Semiconductor doping concentration in cm^-3.

        P-Type:
            doping_cm3 = Na

        N-Type:
            doping_cm3 = Nd

    temperature_k
        Temperature in Kelvin.

    substrate_type
        "P-Type" or "N-Type".

    nc_cm3
        Effective density of states in the conduction band,
        in cm^-3.

    nv_cm3
        Effective density of states in the valence band,
        in cm^-3.

    Returns
    -------
    float
        Vp in volts.
    """

    validate_unit(
        doping_unit,
        "cm^-3",
        "Doping",
    )

    validate_unit(
        temperature_unit,
        "K",
        "Temperature",
    )

    substrate_type = validate_substrate_type(
        substrate_type,
    )

    doping = validate_finite_positive(
        doping_cm3,
        "Doping concentration",
    )

    temperature = validate_finite_positive(
        temperature_k,
        "Temperature",
    )

    nc = validate_finite_positive(
        nc_cm3,
        "Conduction-band effective density of states",
    )

    nv = validate_finite_positive(
        nv_cm3,
        "Valence-band effective density of states",
    )

    thermal_voltage = (
        BOLTZMANN_CONSTANT_J_PER_K
        * temperature
        / ELEMENTARY_CHARGE_C
    )

    if substrate_type == "N-Type":
        # N-Type:
        # Vp = (kT/q) * ln(Nc / Nd)
        logarithm_argument = nc / doping

    else:
        # P-Type:
        # Vp = (kT/q) * ln(Nv / Na)
        logarithm_argument = nv / doping

    if (
        logarithm_argument <= 0.0
        or not np.isfinite(logarithm_argument)
    ):
        raise ValueError(
            "Vp logarithm argument must be finite "
            "and greater than zero."
        )

    vp = thermal_voltage * np.log(
        logarithm_argument
    )

    if not np.isfinite(vp):
        raise ValueError(
            "Calculated Vp is non-finite."
        )

    return float(vp)