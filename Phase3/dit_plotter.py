"""
dit_plotter.py

Plotting utilities for Phase 3 Dit analysis.
"""

from __future__ import annotations

import matplotlib.pyplot as plt

try:
    from .phase3_models import Phase3Results
except ImportError:
    from phase3_models import Phase3Results

def plot_dit_vs_gate_voltage(
    results: Phase3Results,
):
    """
    Plot Dit versus Gate Voltage.

    Parameters
    ----------
    results : Phase3Results

    Returns
    -------
    matplotlib.figure.Figure
    """
    
    if len(results.dit_results) == 0:
        raise ValueError(
            "No Dit results available."
        )
    
    gate_voltage = [
        peak.gate_voltage
        for peak in results.peak_results
    ]

    dit = [
        result.dit
        for result in results.dit_results
    ]

    figure, axis = plt.subplots(
        figsize=(6.4, 4)
    )

    axis.plot(
        gate_voltage,
        dit,
        marker="o",
        markersize=6,
        linewidth=2,
    )

    axis.set_title(
        "Interface Trap Density vs Gate Voltage"
    )

    axis.set_xlabel(
        "Gate Voltage (V)"
    )

    axis.set_ylabel(
        "Dit (cm⁻² eV⁻¹)"
    )

    axis.grid(True)


    axis.ticklabel_format(
        axis="y",
        style="sci",
        scilimits=(0, 0),
    )

    figure.tight_layout()

    return figure

def plot_dit_vs_energy():
    """
    Placeholder.

    Will be implemented after the
    Energy Mapper is completed.
    """

    raise NotImplementedError(
        "Dit vs Energy plotting is not yet available."
    )

    