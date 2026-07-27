"""
peak_detector.py

Peak detection for Gp/Omega curves.
"""

from __future__ import annotations

import numpy as np

from .phase3_models import PeakResult, VoltageSweep


def detect_peak(sweep: VoltageSweep) -> PeakResult:
    """
    Detect the maximum Gp/Omega value for one voltage sweep.

    Parameters
    ----------
    sweep : VoltageSweep

    Returns
    -------
    PeakResult
    """

    if sweep.gp_over_omega is None:
        raise ValueError(
            "Gp/Omega has not been calculated."
        )

    peak_index = int(np.argmax(sweep.gp_over_omega))

    return PeakResult(
        gate_voltage=sweep.gate_voltage,
        peak_index=peak_index,
        peak_frequency=float(sweep.frequency[peak_index]),
        peak_omega=float(sweep.omega[peak_index]),
        peak_value=float(sweep.gp_over_omega[peak_index]),
    )