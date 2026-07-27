"""
gp_plotter.py

Plotting utilities for Phase 3.

Contains:
    • plot_gp_over_omega()
        -> Plot a single gate-voltage sweep.

    • plot_all_gp_over_omega()
        -> Plot all gate-voltage sweeps.
"""

from __future__ import annotations

import matplotlib.pyplot as plt

from .phase3_models import PeakResult, VoltageSweep


# ============================================================
# Single Voltage Sweep
# ============================================================

def plot_gp_over_omega(
    sweep: VoltageSweep,
    peak: PeakResult | None = None,
    x_scale: str = "log",
):
    """
    Plot Gp/ω versus Frequency for one gate voltage.

    If `peak` is None (no valid conductance peak was found
    for this sweep), only the raw Gp/ω curve is plotted; no
    peak marker is drawn and no exception is raised.
    """

    if sweep.gp_over_omega is None:
        raise ValueError(
            "Gp/ω has not been calculated."
        )

    figure, axis = plt.subplots(
        figsize=(6.5, 4)
    )

    axis.plot(
        sweep.frequency,
        sweep.gp_over_omega,
        linewidth=2,
        label=f"{sweep.gate_voltage:.2f} V",
    )

    if peak is not None:

        axis.scatter(
            peak.peak_frequency,
            peak.peak_value,
            color="red",
            s=60,
            zorder=5,
            label="Peak",
        )

    axis.set_title(
        f"Gp/ω vs Frequency\nGate Voltage = {sweep.gate_voltage:.2f} V"
    )

    axis.set_xlabel("Frequency (Hz)")

    axis.set_xscale(x_scale)

    axis.set_ylabel("Gp/ω")

    axis.grid(True)

    axis.legend()

    figure.tight_layout()

    return figure


# ============================================================
# All Voltage Sweeps
# ============================================================

def plot_all_gp_over_omega(
    sweeps: list[VoltageSweep],
    peaks: list[PeakResult],
    x_scale: str = "log",
):
    """
    Plot Gp/ω versus Frequency for every gate voltage.

    Iterates over `sweeps` directly rather than zipping
    against `peaks`, since sweeps that failed validation have
    no corresponding PeakResult and `peaks` can therefore be
    shorter than `sweeps`. Each sweep's peak (if any) is
    looked up by gate_voltage; sweeps with no match are
    plotted as a curve only, with no marker.
    """

    figure, axis = plt.subplots(
        figsize=(6.5, 4)
    )

    peaks_by_voltage = {
        peak.gate_voltage: peak
        for peak in peaks
    }

    for sweep in sweeps:

        if sweep.gp_over_omega is None:
            continue

        axis.plot(
            sweep.frequency,
            sweep.gp_over_omega,
            linewidth=1.8,
            label=f"{sweep.gate_voltage:.2f} V",
        )

        peak = peaks_by_voltage.get(sweep.gate_voltage)

        if peak is not None:

            axis.scatter(
                peak.peak_frequency,
                peak.peak_value,
                s=30,
                zorder=5,
            )

    axis.set_title(
        "Gp/ω vs Frequency (All Gate Voltages)"
    )

    axis.set_xlabel("Frequency (Hz)")

    axis.set_xscale(x_scale)

    axis.set_ylabel("Gp/ω")

    axis.grid(True)

    axis.legend(
        title="Gate Voltage",
        fontsize=8,
        loc="best",
        ncol=2,
    )

    figure.tight_layout()

    return figure