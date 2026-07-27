"""
dit_table.py

Utilities for converting Phase 3 results into
tabular form.
"""

from __future__ import annotations

import pandas as pd

try:
    from .phase3_models import Phase3Results
except ImportError:
    from phase3_models import Phase3Results


def create_dit_table(
    results: Phase3Results,
) -> pd.DataFrame:
    """
    Create a table containing the extracted
    interface trap parameters.

    Parameters
    ----------
    results : Phase3Results

    Returns
    -------
    pandas.DataFrame
    """
    if len(results.dit_results) == 0:
        raise ValueError(
            "No Dit results available."
        )
    rows = []

    for peak, dit in zip(
        results.peak_results,
        results.dit_results,
    ):

        rows.append(
            {
                "Gate Voltage (V)": peak.gate_voltage,
                "Peak Frequency (Hz)": peak.peak_frequency,
                "Peak ω (rad/s)": peak.peak_omega,
                "Peak Gp/ω": peak.peak_value,
                "Dit (cm⁻² eV⁻¹)": dit.dit,
            }
        )

    return pd.DataFrame(rows)