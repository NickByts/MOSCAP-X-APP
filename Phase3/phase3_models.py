"""
phase3_models.py

Dataclasses used throughout Phase 3 (Conductance Method).

These classes store the data as it moves through the Phase 3
pipeline.

Pipeline:

Excel Reader
      ↓
Measurement Validation
      ↓
Omega Calculator
      ↓
Gp/Omega Extraction
      ↓
Peak Detection
      ↓
Dit Extraction
      ↓
Energy Mapping (Future)
"""

from dataclasses import dataclass, field
from typing import Optional, List

import numpy as np


# ============================================================
# Raw Measurement Data
# ============================================================

@dataclass
class VoltageSweep:
    """
    Represents one complete frequency sweep measured at
    one gate voltage.

    This object is created by excel_reader.py.
    """

    # ------------------------
    # Measurement Information
    # ------------------------

    gate_voltage: float

    frequency: np.ndarray

    conductance: np.ndarray

    capacitance: np.ndarray

    # ------------------------
    # Generated Later
    # ------------------------

    omega: Optional[np.ndarray] = None

    gp_over_omega: Optional[np.ndarray] = None


@dataclass
class PeakValidationResult:
    """
    Validation result for one Gp/Omega curve.
    """

    is_valid: bool

    message: str

    boundary_peak: bool

    candidate_count: int

    maximum_index: int


# ============================================================
# Peak Detection
# ============================================================

@dataclass
class PeakResult:
    """
    Stores the extracted physical peak.
    """

    gate_voltage: float

    peak_index: int

    peak_frequency: float

    peak_omega: float

    peak_value: float

    peak_prominence: float = 0.0

    peak_width: float = 0.0

    detection_method: str = "argmax"

# ============================================================
# Dit Result
# ============================================================

@dataclass
class DitResult:
    """
    Interface Trap Density extracted from one voltage sweep.
    """

    gate_voltage: float

    dit: float

    gp_over_omega_max: float

    peak_frequency: float

    peak_omega: float


# ============================================================
# Complete Phase 3 Result
# ============================================================

@dataclass
class Phase3Results:
    """
    Final result returned by the complete Phase 3 pipeline.
    """

    voltage_sweeps: List[VoltageSweep] = field(default_factory=list)

    peak_results: List[PeakResult] = field(default_factory=list)

    dit_results: List[DitResult] = field(default_factory=list)

@dataclass
class PeakCandidate:

    index: int

    frequency: float

    omega: float

    height: float

    prominence: float

    width: float

    accepted: bool = True

    rejection_reason: str = ""