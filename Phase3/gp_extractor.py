"""
gp_extractor.py

Parallel conductance calculation.

Calculates Gp/Omega for one voltage sweep.
"""

from __future__ import annotations

import numpy as np

from .phase3_models import VoltageSweep


def calculate_gp_over_omega(
    sweep: VoltageSweep,
    cox: float,
) -> VoltageSweep:
    """
    Calculate parallel conductance divided by angular frequency.

    Parameters
    ----------
    sweep : VoltageSweep
        Voltage sweep containing measured conductance,
        capacitance and angular frequency.

    cox : float
        Total oxide capacitance (F), obtained from Phase 2.

    Returns
    -------
    VoltageSweep
        The same VoltageSweep object with gp_over_omega populated.
    """

    omega = sweep.omega

    if omega is None:
        raise ValueError(
            "Angular frequency has not been calculated. "
            "Run omega_calculator before gp_extractor."
        )

    gma = sweep.conductance

    cma = sweep.capacitance

    numerator = omega * gma * (cma ** 2)

    denominator = (
        (gma ** 2)
        + (omega ** 2) * ((cox - cma) ** 2)
    )

    sweep.gp_over_omega = numerator / denominator

    return sweep