"""
analysis_window_plot.py

A dedicated, self-contained plot widget for the Phase 3 "Inspect
Individual Gate Voltage" chart, which needs live mouse interaction
(draggable analysis-window markers) on top of the Gp/omega curve.

This intentionally does NOT reuse PlotWidget / _PlotDisplay from
plot_widget.py. That widget deliberately renders a *static* QPixmap
rather than a live FigureCanvasQTAgg -- see its docstring -- to fix
a specific bug where matplotlib rewrites a live canvas's Figure size
on every Qt resize event, corrupting the Figure shared with the
Save-PNG export path. That fix, and every other plot in the app that
still relies on it (all-sweeps plot, Dit-vs-voltage plot, Phase 1/2
plots, C-V / 1/C^2 plots), is left completely untouched.

Only this one chart -- which now needs draggable markers and
therefore a live canvas -- gets its own small widget, isolated from
that shared code path.

Requires matplotlib's Qt-agnostic backend (matplotlib >= 3.5) with
PySide6 already imported/active as the Qt binding.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional, Sequence

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class AnalysisWindowPlotWidget(QWidget):
    """
    Displays the Gp/omega-vs-frequency Figure produced by
    gp_plotter.plot_gp_over_omega() (unchanged, reused as-is) inside
    a live matplotlib canvas, with two draggable vertical lines
    marking the current [minimum_frequency, maximum_frequency]
    analysis window on top of it.

    Signals
    -------
    analysisWindowDragged(float, float)
        Emitted with (minimum_frequency, maximum_frequency), already
        clamped to the measured range, ordered, and snapped to the
        nearest actual measured frequency, whenever the user drags
        either marker.
    """

    analysisWindowDragged = Signal(float, float)

    def __init__(
        self,
        figure_to_png_bytes: Callable[[Figure], bytes],
        default_file_name: str = "figure.png",
        parent=None,
    ) -> None:
        super().__init__(parent)

        self._figure_to_png_bytes = figure_to_png_bytes
        self._default_file_name = default_file_name

        self._figure: Optional[Figure] = None
        self._canvas: Optional[FigureCanvasQTAgg] = None
        self._axis = None

        self._measured_frequencies: np.ndarray = np.asarray([])
        self._minimum_frequency: float = 0.0
        self._maximum_frequency: float = 0.0

        self._min_line = None
        self._max_line = None
        self._dragging: Optional[str] = None  # "min" | "max" | None

        self._canvas_container = QVBoxLayout()

        self._save_button = QPushButton("Save PNG")
        self._save_button.clicked.connect(self._on_save_clicked)
        self._save_button.setEnabled(False)

        layout = QVBoxLayout(self)
        layout.addLayout(self._canvas_container)
        layout.addWidget(self._save_button)
        layout.addStretch(1)

    # ------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------

    def set_figure_and_window(
        self,
        figure: Optional[Figure],
        measured_frequencies: Sequence[float],
        minimum_frequency: float,
        maximum_frequency: float,
    ) -> None:
        """Swap in a newly-computed Figure and (re)draw the two markers."""

        self._teardown_canvas()

        self._figure = figure
        self._measured_frequencies = np.asarray(measured_frequencies, dtype=float)
        self._minimum_frequency = minimum_frequency
        self._maximum_frequency = maximum_frequency

        if figure is None:
            self._save_button.setEnabled(False)
            return

        self._axis = figure.axes[0] if figure.axes else figure.add_subplot(111)

        self._canvas = FigureCanvasQTAgg(figure)
        self._canvas.setMinimumHeight(420)
        self._canvas_container.addWidget(self._canvas)

        self._min_line = self._axis.axvline(
            minimum_frequency, color="0.35", linestyle="--", linewidth=1.5
        )
        self._max_line = self._axis.axvline(
            maximum_frequency, color="0.35", linestyle="--", linewidth=1.5
        )

        self._canvas.mpl_connect("button_press_event", self._on_mouse_press)
        self._canvas.mpl_connect("motion_notify_event", self._on_mouse_move)
        self._canvas.mpl_connect("button_release_event", self._on_mouse_release)

        self._canvas.draw_idle()
        self._save_button.setEnabled(True)

    # ------------------------------------------------------------
    # Dragging
    # ------------------------------------------------------------

    def _on_mouse_press(self, event) -> None:
        if event.inaxes != self._axis or event.xdata is None:
            return

        min_pixels = self._axis.transData.transform((self._minimum_frequency, 0))[0]
        max_pixels = self._axis.transData.transform((self._maximum_frequency, 0))[0]

        self._dragging = "min" if abs(event.x - min_pixels) <= abs(event.x - max_pixels) else "max"

    def _on_mouse_move(self, event) -> None:
        if self._dragging is None or event.inaxes != self._axis or event.xdata is None:
            return
        self._move_dragged_marker(event.xdata)

    def _on_mouse_release(self, event) -> None:
        if self._dragging is None:
            return
        if event.inaxes == self._axis and event.xdata is not None:
            self._move_dragged_marker(event.xdata)
        self._dragging = None

    def _move_dragged_marker(self, target_frequency: float) -> None:
        if self._measured_frequencies.size == 0:
            return

        snapped = self._nearest_measured_frequency(target_frequency)
        minimum_frequency, maximum_frequency = self._minimum_frequency, self._maximum_frequency

        if self._dragging == "min":
            minimum_frequency = min(snapped, self._previous_point(maximum_frequency))
        else:
            maximum_frequency = max(snapped, self._next_point(minimum_frequency))

        if (
            minimum_frequency == self._minimum_frequency
            and maximum_frequency == self._maximum_frequency
        ):
            return

        self._minimum_frequency = minimum_frequency
        self._maximum_frequency = maximum_frequency
        self._min_line.set_xdata([minimum_frequency, minimum_frequency])
        self._max_line.set_xdata([maximum_frequency, maximum_frequency])
        self._canvas.draw_idle()

        self.analysisWindowDragged.emit(minimum_frequency, maximum_frequency)

    def _nearest_measured_frequency(self, frequency: float) -> float:
        index = int(np.argmin(np.abs(self._measured_frequencies - frequency)))
        return float(self._measured_frequencies[index])

    def _previous_point(self, frequency: float) -> float:
        smaller = self._measured_frequencies[self._measured_frequencies < frequency]
        return float(smaller.max()) if smaller.size else float(self._measured_frequencies.min())

    def _next_point(self, frequency: float) -> float:
        larger = self._measured_frequencies[self._measured_frequencies > frequency]
        return float(larger.min()) if larger.size else float(self._measured_frequencies.max())

    # ------------------------------------------------------------
    # Teardown / export
    # ------------------------------------------------------------

    def _teardown_canvas(self) -> None:
        if self._canvas is not None:
            self._canvas.setParent(None)
            self._canvas.deleteLater()
            self._canvas = None
        self._min_line = None
        self._max_line = None
        self._dragging = None

    def _on_save_clicked(self) -> None:
        if self._figure is None:
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Plot", self._default_file_name, "PNG Image (*.png)"
        )
        if not file_path:
            return
        try:
            data = self._figure_to_png_bytes(self._figure)
            Path(file_path).write_bytes(data)
        except Exception as exc:
            QMessageBox.warning(self, "Save Failed", str(exc))