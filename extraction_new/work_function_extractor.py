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
    phi_f_v: float,
    substrate_type: str,
) -> WorkFunctionResult:
    """
    Calculate the metal-semiconductor work-function difference.

    Parameters
    ----------
    phi_m_ev
        Metal work function (eV)

    electron_affinity_ev
        Semiconductor electron affinity (eV)

    bandgap_ev
        Semiconductor bandgap (eV)

    phi_f_v
        Fermi potential (V)

    substrate_type
        "P-Type" or "N-Type"

    Returns
    -------
    WorkFunctionResult
    """

    validate_finite(phi_m_ev, "Metal work function")
    validate_finite(
        electron_affinity_ev,
        "Electron affinity",
    )
    validate_finite(
        bandgap_ev,
        "Bandgap",
    )
    validate_finite(
        phi_f_v,
        "Fermi potential",
    )

    substrate_type = validate_substrate_type(
        substrate_type,
    )

    if substrate_type == "P-Type":

        phi_s = (
            electron_affinity_ev
            + bandgap_ev / 2.0
            + phi_f_v
        )

    else:

        phi_s = (
            electron_affinity_ev
            + bandgap_ev / 2.0
            - phi_f_v
        )

    phi_ms = phi_m_ev - phi_s

    return WorkFunctionResult(
        phi_ms=float(phi_ms),
    )