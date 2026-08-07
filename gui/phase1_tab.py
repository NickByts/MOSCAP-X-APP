"""
phase1_tab.py

Phase 1 tab: parameter-extraction cards (previously
_render_phase_1b_cards) plus the automatic 1/C²-V region
detection plot (previously rendered via
plot_phase1_inverse_c2_regions in section 8 of app.py). No
calculation logic lives here -- this only displays a
Phase1PipelineResult that was already computed.
"""

from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from .format_utils import format_phase_1b_value
from .metric_card import MetricCard
from .plot_widget import PlotWidget


class Phase1Tab(QWidget):
    def __init__(self, figure_to_png_bytes: Callable, parent=None) -> None:
        super().__init__(parent)

        self._status_label = QLabel("")
        self._status_label.setWordWrap(True)

        self._cox_card = MetricCard("Cox")
        self._v0_card = MetricCard("V\u2080")
        self._r2_card = MetricCard("R\u00b2")
        self._doping_card = MetricCard("Doping")

        self._debye_card = MetricCard("Debye Length")
        self._csfb_card = MetricCard("CsFB")
        self._cfb_card = MetricCard("CFB")

        self._vfb_card = MetricCard("Flat-Band Voltage")

        row1 = QHBoxLayout()
        for card in (
            self._cox_card,
            self._v0_card,
            self._r2_card,
            self._doping_card,
        ):
            row1.addWidget(card)

        row2 = QHBoxLayout()
        for card in (self._debye_card, self._csfb_card, self._cfb_card):
            row2.addWidget(card)

        row3 = QHBoxLayout()
        row3.addWidget(self._vfb_card)

        self._region_plot_widget = PlotWidget(
            figure_to_png_bytes,
            default_file_name="phase1_inverse_c2_regions.png",
        )

        layout = QVBoxLayout(self)
        layout.addWidget(self._status_label)
        layout.addLayout(row1)
        layout.addLayout(row2)
        layout.addLayout(row3)
        layout.addWidget(QLabel("Automatic 1/C\u00b2-V Region Detection & Linear Regression"))
        layout.addWidget(self._region_plot_widget)

        self.set_summary(None, None)

    def set_summary(
        self,
        summary,
        error_message: Optional[str],
        region_figure=None,
    ) -> None:
        if summary is None:
            self._status_label.setText(
                error_message
                or "Phase 1B parameter extraction unavailable."
            )
            for card in (
                self._cox_card,
                self._v0_card,
                self._r2_card,
                self._doping_card,
                self._debye_card,
                self._csfb_card,
                self._cfb_card,
                self._vfb_card,
            ):
                card.set_value("--")
            self._region_plot_widget.set_figure(None)
            return

        self._status_label.setText("")

        self._cox_card.set_value(f"{format_phase_1b_value(summary.cox.cox)} F")
        self._v0_card.set_value(f"{summary.vintercept.vintercept:.4f} V")
        self._r2_card.set_value(f"{summary.fit.r2:.5f}")

        self._doping_card.set_label(summary.doping.substrate_type)
        self._doping_card.set_value(
            f"{format_phase_1b_value(summary.doping.doping_value)} cm⁻³"
        )

        self._debye_card.set_value(
            f"{format_phase_1b_value(summary.debye.debye_length)} cm"
        )
        self._csfb_card.set_value(
            f"{format_phase_1b_value(summary.csfb.csfb)} F"
        )
        self._cfb_card.set_value(
            f"{format_phase_1b_value(summary.cfb.cfb)} F"
        )

        self._vfb_card.set_value(f"{summary.vfb.vfb:.4f} V")

        self._region_plot_widget.set_figure(region_figure)
