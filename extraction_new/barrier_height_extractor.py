"""Barrier-height extraction for MOSCAP-X Phase 2."""

from __future__ import annotations

import numpy as np

try:
    from .phase2_validation import validate_finite
except ImportError:
    from phase2_validation import validate_finite


def calculate_barrier_height(
    vd_v: float,
    vp_v: float,
    delta_phi_b_v: float,
) -> float:
    """
    Calculate the barrier height.

    Formula
    -------
    phi_b = Vd + Vp - Delta_phi_b

    Parameters
    ----------
    vd_v
        Diffusion potential in volts.

    vp_v
        Vp in volts.

    delta_phi_b_v
        Image-force barrier lowering in volts/eV.

    Returns
    -------
    float
        Barrier height.
    """

    vd = validate_finite(
        vd_v,
        "Diffusion potential",
    )

    vp = validate_finite(
        vp_v,
        "Vp",
    )

    delta_phi_b = validate_finite(
        delta_phi_b_v,
        "Image-force barrier lowering",
    )

    barrier_height = (
        vd
        + vp
        - delta_phi_b
    )

    if not np.isfinite(barrier_height):
        raise ValueError(
            "Calculated barrier height is non-finite."
        )

    return float(barrier_height)