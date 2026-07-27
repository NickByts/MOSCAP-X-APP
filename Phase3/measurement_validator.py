"""
measurement_validator.py

Validation routines for Phase 3 frequency sweep data.
"""

import numpy as np

from .phase3_models import VoltageSweep


MINIMUM_POINTS = 5


def validate_voltage_sweep(sweep: VoltageSweep) -> None:
    """
    Validate one VoltageSweep.

    Raises
    ------
    ValueError
        If the measurement is invalid.
    """

    # --------------------------------------------------
    # Empty dataset
    # --------------------------------------------------

    if len(sweep.frequency) == 0:
        raise ValueError(
            f"{sweep.gate_voltage} V : Empty dataset."
        )

    # --------------------------------------------------
    # Minimum points
    # --------------------------------------------------

    if len(sweep.frequency) < MINIMUM_POINTS:
        raise ValueError(
            f"{sweep.gate_voltage} V : "
            f"Need at least {MINIMUM_POINTS} points."
        )

    # --------------------------------------------------
    # Equal lengths
    # --------------------------------------------------

    if not (
        len(sweep.frequency)
        == len(sweep.conductance)
        == len(sweep.capacitance)
    ):
        raise ValueError(
            f"{sweep.gate_voltage} V : "
            "Frequency, Conductance and Capacitance "
            "must have equal length."
        )

    # --------------------------------------------------
    # NaN check
    # --------------------------------------------------

    if np.isnan(sweep.frequency).any():
        raise ValueError(
            f"{sweep.gate_voltage} V : "
            "Frequency contains NaN."
        )

    if np.isnan(sweep.conductance).any():
        raise ValueError(
            f"{sweep.gate_voltage} V : "
            "Conductance contains NaN."
        )

    if np.isnan(sweep.capacitance).any():
        raise ValueError(
            f"{sweep.gate_voltage} V : "
            "Capacitance contains NaN."
        )

    # --------------------------------------------------
    # Infinite values
    # --------------------------------------------------

    if not np.isfinite(sweep.frequency).all():
        raise ValueError(
            f"{sweep.gate_voltage} V : "
            "Frequency contains infinite values."
        )

    if not np.isfinite(sweep.conductance).all():
        raise ValueError(
            f"{sweep.gate_voltage} V : "
            "Conductance contains infinite values."
        )

    if not np.isfinite(sweep.capacitance).all():
        raise ValueError(
            f"{sweep.gate_voltage} V : "
            "Capacitance contains infinite values."
        )

    # --------------------------------------------------
    # Frequency
    # --------------------------------------------------

    if np.any(sweep.frequency <= 0):
        raise ValueError(
            f"{sweep.gate_voltage} V : "
            "Frequency must be greater than zero."
        )