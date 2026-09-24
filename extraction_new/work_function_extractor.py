"""Metal-semiconductor work-function difference extractor."""

from __future__ import annotations

from dataclasses import dataclass

from .phase2_validation import (
    validate_finite,
    validate_substrate_type,
)


@dataclass(frozen=True, slots=True)
class WorkFunctionResult:
    """Result of metal-semiconductor work-function calculation."""

    phi_ms: float


def calculate_work_function_difference(
    phi_m_ev: float,
    electron_affinity_ev: float,
    bandgap_ev: float,
    vp_v: float,
    substrate_type: str,
) -> WorkFunctionResult:
    """
    Calculate the metal-semiconductor work-function difference.

    Parameters
    ----------
    phi_m_ev
        Metal work function (eV).

    electron_affinity_ev
        Semiconductor electron affinity (eV).

    bandgap_ev
        Semiconductor bandgap (eV).

    vp_v
        Vp in volts.

        For P-Type:
            Vp = (kT/q) * ln(Nv / Na)

        For N-Type:
            Vp = (kT/q) * ln(Nc / Nd)

    substrate_type
        "P-Type" or "N-Type".

    Returns
    -------
    WorkFunctionResult
        Metal-semiconductor work-function difference.
    """

    validate_finite(
        phi_m_ev,
        "Metal work function",
    )

    validate_finite(
        electron_affinity_ev,
        "Electron affinity",
    )

    validate_finite(
        bandgap_ev,
        "Bandgap",
    )

    vp = validate_finite(
        vp_v,
        "Vp",
    )

    substrate_type = validate_substrate_type(
        substrate_type,
    )

    if substrate_type == "P-Type":

        # P-Type:
        #
        # Phi_ms = Phi_m - (X + Eg - Vp)

        semiconductor_work_function = (
            electron_affinity_ev
            + bandgap_ev
            - vp
        )

    else:

        # N-Type:
        #
        # Phi_ms = Phi_m - (X + Vp)

        semiconductor_work_function = (
            electron_affinity_ev
            + vp
        )

    phi_ms = (
        phi_m_ev
        - semiconductor_work_function
    )

    return WorkFunctionResult(
        phi_ms=float(phi_ms),
    )