"""Fermi-level extraction for MOSCAP-X Phase 2."""

from __future__ import annotations

import numpy as np
try:
    from .phase2_constants import (
        BOLTZMANN_CONSTANT_J_PER_K,
        ELEMENTARY_CHARGE_C,
    )
    from .phase2_validation import (
        validate_finite_positive,
        validate_unit,
        validate_substrate_type,
    )

except ImportError:
    from phase2_constants import (
        BOLTZMANN_CONSTANT_J_PER_K,
        ELEMENTARY_CHARGE_C,
    )
    from phase2_validation import (
        validate_finite_positive,
        validate_unit,
        validate_substrate_type,
    )

def calculate_fermi_level(
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
    EF = (kT/q) * ln(Nc / Nd)
    """

    validate_unit(doping_unit, "cm^-3", "Doping")
    validate_unit(temperature_unit, "K", "Temperature")
    validate_substrate_type(substrate_type)

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
        ef = thermal_voltage * np.log(
            nc / doping
        )

    elif substrate_type == "P-Type":
        ef = thermal_voltage * np.log(
            nv / doping
        )

    else:
        raise ValueError(
            "Unsupported substrate type."
        )

    if not np.isfinite(ef):
        raise ValueError(
            "Calculated Fermi level is non-finite."
        )

    return float(ef)