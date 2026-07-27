"""Typed inputs and material properties for MOSCAP-X Phase 2."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Phase2Inputs:

    area_cm2: float

    temperature_k: float

    doping_cm3: float

    substrate_type: str

    cox_f: float

    v0_v: float

    ld_cm: float

    cs_f: float

    cfb_f: float

    vfb_v: float

    phi_m_ev: float


@dataclass(frozen=True, slots=True)
class Phase2MaterialProperties:
    """Semiconductor properties kept separate from user/device inputs."""

    intrinsic_concentration_cm3: float
    bandgap_ev: float
    electron_affinity_ev: float
    relative_permittivity: float
    conduction_band_density_cm3: float
    valence_band_density_cm3: float