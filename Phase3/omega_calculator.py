"""
omega_calculator.py

Angular frequency calculation for Phase 3.

ω = 2πf
"""

import numpy as np

from .phase3_models import VoltageSweep


def calculate_omega(sweep: VoltageSweep) -> VoltageSweep:
    """
    Calculate angular frequency for one voltage sweep.

    Parameters
    ----------
    sweep : VoltageSweep

    Returns
    -------
    VoltageSweep
        Same object with omega populated.
    """

    sweep.omega = 2.0 * np.pi * sweep.frequency

    return sweep