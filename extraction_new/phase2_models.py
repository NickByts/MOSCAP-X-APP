"""Typed inputs and material properties for MOSCAP-X Phase 2."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Phase2Inputs:
    """Device and measurement inputs required by Phase 2."""

    area_cm2: float

    temperature_k: float

    # Automatically supplied from Phase 1B:
    # P-Type -> Na
    # N-Type -> Nd
    doping_cm3: float

    substrate_type: str

    cox_f: float

    v0_v: float

    ld_cm: float

    cs_f: float

    cfb_f: float

    vfb_v: float

    # User-provided metal work function.
    phi_m_ev: float

    # User-provided effective density of states.
    nc_cm3: float

    nv_cm3: float


@dataclass(frozen=True, slots=True)
class Phase2MaterialProperties:
    """Semiconductor material properties used by Phase 2."""

    intrinsic_concentration_cm3: float

    bandgap_ev: float

    electron_affinity_ev: float

    relative_permittivity: float