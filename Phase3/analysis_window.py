"""
analysis_window.py

Implements the "Measurement Analysis Window" feature: a per-gate-
voltage frequency sub-range used for peak detection and Dit
extraction, without ever modifying the raw VoltageSweep arrays
(frequency, conductance, capacitance, omega, gp_over_omega).

Pipeline, reused unchanged from phase3_pipeline.run_phase3():

    raw sweep --mask--> filtered sweep --detect_peak()--> PeakResult
                                        --calculate_dit()--> DitResult

Future preprocessing tools (negative-conductance removal,
Savitzky-Golay smoothing, median filtering, automatic low/high-
frequency rejection) should build their own boolean mask against
sweep.frequency and call apply_frequency_mask() /
recompute_peak_and_dit() below, instead of re-deriving filtered
arrays or re-implementing the peak/Dit step -- so there stays
exactly one "filtered sweep -> peak -> Dit" pipeline, run at
initial load (run_phase3) and again every time the analysis
window changes.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np

from .phase3_models import DitResult, PeakResult, VoltageSweep
from .peak_detector import detect_peak
from .dit_extractor import calculate_dit


def full_range_window(sweep: VoltageSweep) -> tuple[float, float]:
    """The default analysis window: `sweep`'s full measured frequency range."""
    raw_frequency = np.asarray(sweep.frequency, dtype=float)
    return float(np.min(raw_frequency)), float(np.max(raw_frequency))


def snap_to_measured_frequency(sweep: VoltageSweep, frequency: float) -> float:
    """The measured frequency in `sweep` nearest to `frequency`."""
    raw_frequency = np.asarray(sweep.frequency, dtype=float)
    index = int(np.argmin(np.abs(raw_frequency - frequency)))
    return float(raw_frequency[index])


def build_frequency_mask(
    sweep: VoltageSweep, minimum_frequency: float, maximum_frequency: float
) -> np.ndarray:
    """Boolean mask selecting sweep.frequency points inside [minimum_frequency, maximum_frequency]."""
    raw_frequency = np.asarray(sweep.frequency, dtype=float)
    return (raw_frequency >= minimum_frequency) & (raw_frequency <= maximum_frequency)


def apply_frequency_mask(sweep: VoltageSweep, mask: np.ndarray) -> VoltageSweep:
    """
    A NEW VoltageSweep holding only the masked subset of `sweep`'s
    arrays. `sweep` and its raw arrays are never modified.
    """
    return replace(
        sweep,
        frequency=np.asarray(sweep.frequency)[mask],
        conductance=np.asarray(sweep.conductance)[mask],
        capacitance=np.asarray(sweep.capacitance)[mask],
        omega=None if sweep.omega is None else np.asarray(sweep.omega)[mask],
        gp_over_omega=(
            None
            if sweep.gp_over_omega is None
            else np.asarray(sweep.gp_over_omega)[mask]
        ),
    )


def recompute_peak_and_dit(
    filtered_sweep: VoltageSweep,
    area_cm2: float,
    elementary_charge: float,
) -> tuple[PeakResult, DitResult]:
    """Re-run the existing peak_detector / dit_extractor pipeline on an already-filtered sweep."""
    peak = detect_peak(filtered_sweep)
    dit = calculate_dit(
        peak=peak,
        area_cm2=area_cm2,
        elementary_charge=elementary_charge,
    )
    return peak, dit


def apply_analysis_window(
    sweep: VoltageSweep,
    minimum_frequency: float,
    maximum_frequency: float,
    area_cm2: float,
    elementary_charge: float,
) -> tuple[VoltageSweep, PeakResult, DitResult]:
    """
    Full pipeline for one sweep: mask -> filtered sweep -> peak -> Dit.
    `sweep` itself is never mutated.
    """
    mask = build_frequency_mask(sweep, minimum_frequency, maximum_frequency)

    if mask.sum() < 2:
        raise ValueError(
            "The selected analysis window contains fewer than two "
            "measured frequency points."
        )

    filtered_sweep = apply_frequency_mask(sweep, mask)
    peak, dit = recompute_peak_and_dit(filtered_sweep, area_cm2, elementary_charge)
    return filtered_sweep, peak, dit