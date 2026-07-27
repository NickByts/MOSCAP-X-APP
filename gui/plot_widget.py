"""
plot_widget.py

Displays an existing matplotlib Figure -- unchanged, still produced by
the same plotting.py / gp_plotter.py / dit_plotter.py /
plot_phase1_pipeline.py functions -- inside a Qt widget, with a
"Save PNG" button standing in for Streamlit's st.download_button().
No plotting logic lives here.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from matplotlib.figure import Figure
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

# Shared, responsive display envelope used by every plot in the app
# (Plots / Phase 1 / Phase 2 / Phase 3 tabs alike), independent of any
# individual Figure's own figsize/dpi. Qt is free to size the plot
# anywhere in [MIN, MAX], preferring PREFERRED when there's room.
_CANVAS_MIN_HEIGHT_PX = 420
_CANVAS_PREFERRED_HEIGHT_PX = 500
_CANVAS_MAX_HEIGHT_PX = 600


class _PlotDisplay(QLabel):
    """
    Renders a fixed QPixmap of a matplotlib Figure, rescaled
    (preserving aspect ratio) to whatever size the layout gives this
    label, clamped to the shared min/preferred/max height envelope.

    This intentionally does NOT embed a live FigureCanvasQTAgg.
    matplotlib's Qt canvas classes call `Figure.set_size_inches()` on
    every resizeEvent to match the widget's current pixel size -- that
    is upstream matplotlib behaviour, not something specific to this
    app. Since the canvas's Figure and the Figure handed to
    `figure_to_png_bytes()` for the Save PNG button were the same
    object, ordinary window/splitter/tab resizing was silently
    rewriting the real Figure's size and aspect ratio -- which is what
    produced the "different visual scale in every tab" symptom, and
    made "exported PNG identical to before" unreliable.

    Rendering the Figure to bytes exactly once (via the same
    `figure_to_png_bytes` used for export) and displaying that as a
    QPixmap means on-screen resizing is a pure Qt pixmap-scaling
    operation. It can never reach back and alter the Figure, so every
    plot behaves identically regardless of which tab or layout it's
    in, and the Figure passed to Save PNG is always the pristine,
    never-mutated object exactly as the plotting functions produced it.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._source_pixmap: Optional[QPixmap] = None

        self.setAlignment(Qt.AlignCenter)
        # Expand to fill available width; height is allowed to flex
        # between the min/max bounds below, around the preferred value
        # reported by sizeHint().
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setMinimumHeight(_CANVAS_MIN_HEIGHT_PX)
        self.setMaximumHeight(_CANVAS_MAX_HEIGHT_PX)

    def sizeHint(self) -> QSize:
        # Deliberately constant and independent of the current pixmap.
        # If this instead reflected the loaded image's native size (the
        # default QLabel behaviour), every plot would ask its parent
        # layout for a different amount of space based on its own
        # figure's original figsize/dpi -- reintroducing the exact
        # per-tab inconsistency this widget exists to eliminate.
        return QSize(self.width() or 800, _CANVAS_PREFERRED_HEIGHT_PX)

    def set_pixmap_source(self, pixmap: Optional[QPixmap]) -> None:
        self._source_pixmap = pixmap
        self._refresh()

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt override
        super().resizeEvent(event)
        self._refresh()

    def _refresh(self) -> None:
        if self._source_pixmap is None or self._source_pixmap.isNull():
            self.clear()
            return

        # Scale for the label's device pixel ratio too, so the plot
        # stays crisp on HiDPI displays instead of being upscaled from
        # a lower-resolution pixmap.
        dpr = self.devicePixelRatioF()
        target_size = self.size() * dpr
        scaled = self._source_pixmap.scaled(
            target_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        scaled.setDevicePixelRatio(dpr)
        self.setPixmap(scaled)


class PlotWidget(QWidget):
    """
    Displays a matplotlib Figure and offers a save-to-PNG button via an
    injected `figure_to_png_bytes` function (the same one already in
    utils.py -- passed in rather than imported here, so this module
    stays backend-agnostic).
    """

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

        self._plot_display = _PlotDisplay()

        self._save_button = QPushButton("Save PNG")
        self._save_button.clicked.connect(self._on_save_clicked)
        self._save_button.setEnabled(False)

        layout = QVBoxLayout(self)
        layout.addWidget(self._plot_display)
        layout.addWidget(self._save_button)
        # Keep the button snug directly under the plot even if this
        # widget is given extra vertical space by a parent layout
        # (e.g. the enclosing QScrollArea's content widget).
        layout.addStretch(1)

    def set_figure(self, figure: Optional[Figure]) -> None:
        """Swap in a newly-computed Figure, or clear the plot with None."""

        self._figure = figure

        if figure is None:
            self._plot_display.set_pixmap_source(None)
            self._save_button.setEnabled(False)
            return

        # Render once, through the exact same function used for the
        # Save PNG button, so the on-screen plot and the exported file
        # are always pixel-identical in content. The Figure object
        # itself is never modified by this call.
        try:
            png_bytes = self._figure_to_png_bytes(figure)
            pixmap = QPixmap()
            if not pixmap.loadFromData(png_bytes, "PNG"):
                pixmap = None
        except Exception:
            pixmap = None

        self._plot_display.set_pixmap_source(pixmap)
        self._save_button.setEnabled(pixmap is not None)

    def _on_save_clicked(self) -> None:
        if self._figure is None:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Plot",
            self._default_file_name,
            "PNG Image (*.png)",
        )

        if not file_path:
            return

        try:
            data = self._figure_to_png_bytes(self._figure)
            Path(file_path).write_bytes(data)
        except Exception as exc:
            QMessageBox.warning(self, "Save Failed", str(exc))