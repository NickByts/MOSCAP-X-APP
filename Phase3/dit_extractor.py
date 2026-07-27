"""
dit_extractor.py

Interface Trap Density (Dit) extraction using the conductance method.
"""

from __future__ import annotations

from .phase3_models import DitResult, PeakResult


def calculate_dit(
    peak: PeakResult,
    area_cm2: float,
    elementary_charge: float,
) -> DitResult:
    """
    Calculate interface trap density (Dit).

    Parameters
    ----------
    peak : PeakResult
        Peak detected from the Gp/Omega curve.

    area_cm2 : float
        MOS capacitor area in cm².

    elementary_charge : float
        Elementary charge (C).

    Returns
    -------
    DitResult
    """

    if area_cm2 <= 0.0:
        raise ValueError(
            "Device area must be positive."
        )

    if elementary_charge <= 0.0:
        raise ValueError(
            "Elementary charge must be positive."
        )

    dit = (
        peak.peak_value
        /
        (0.403 * elementary_charge * area_cm2)
    )

    return DitResult(
        gate_voltage=peak.gate_voltage,
        dit=dit,
        gp_over_omega_max=peak.peak_value,
        peak_frequency=peak.peak_frequency,
        peak_omega=peak.peak_omega,
    )