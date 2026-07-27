from __future__ import annotations

from dataclasses import dataclass

import numpy as np

try:
    from .phase3_models import Phase3Results
except ImportError:
    from phase3_models import Phase3Results


@dataclass(slots=True)
class Phase3Summary:

    total_gate_voltages: int

    average_dit: float

    minimum_dit: float

    maximum_dit: float

    minimum_peak_frequency: float

    maximum_peak_frequency: float

    minimum_gp_over_omega: float

    maximum_gp_over_omega: float


def calculate_phase3_summary(
    results: Phase3Results,
) -> Phase3Summary:
    """
    Calculate summary statistics for Phase 3 conductance analysis.

    Parameters
    ----------
    results : Phase3Results
        Output returned by the Phase 3 pipeline.

    Returns
    -------
    Phase3Summary
    """

    if len(results.dit_results) == 0:
        raise ValueError(
            "No Dit results available."
        )

    dit_values = np.asarray(
        [result.dit for result in results.dit_results],
        dtype=float,
    )

    peak_frequencies = np.asarray(
        [
            result.peak_frequency
            for result in results.peak_results
        ],
        dtype=float,
    )

    gp_over_omega_values = np.asarray(
        [
            peak.peak_value
            for peak in results.peak_results
        ],
        dtype=float,
    )

    return Phase3Summary(

        total_gate_voltages=len(results.dit_results),

        average_dit=float(np.mean(dit_values)),

        minimum_dit=float(np.min(dit_values)),

        maximum_dit=float(np.max(dit_values)),

        minimum_peak_frequency=float(
            np.min(peak_frequencies)
        ),

        maximum_peak_frequency=float(
            np.max(peak_frequencies)
        ),

        minimum_gp_over_omega=float(
            np.min(gp_over_omega_values)
        ),

        maximum_gp_over_omega=float(
            np.max(gp_over_omega_values)
        ),
    )