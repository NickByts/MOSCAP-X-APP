"""
phase2_tab.py

Phase 2 tab: the 13-metric grid previously rendered by
_render_phase_2_metrics(). No calculation logic lives here --
this only displays a Phase2Summary that was already computed.
Row grouping (3, 4, 3, 4) mirrors the original
st.columns(3)/st.columns(4)/... layout.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from .format_utils import format_engineering
from .metric_card import MetricCard

_METRIC_SPECS = (
    ("Diffusion Potential", "vd_v", "V"),
    ("Debye Length", "ld_cm", "cm"),
    ("Electrostatic potentail (Vp)", "phi_f_v", "V"),
    ("Depletion Width", "wd_cm", "cm"),
    ("Junction Electric Field", "em_v_cm", "V/cm"),
    ("Image Force Barrier Lowering", "delta_phi_b_v", "eV"),
    ("Fermi Level", "ef_v", "eV"),
    ("Barrier Height", "phi_b_v", "eV"),
    ("Semiconductor Capacitance", "cs_f", "F"),
    ("Flat-Band Capacitance", "cfb_f", "F"),
    ("Metal-Semiconductor Work Function", "phi_ms_v", "eV"),
    ("Effective Oxide Charge", "qeff_c_cm2", "C/cm²"),
    ("Effective Charge Density", "neff_cm2", "cm⁻²"),
)

_ROW_SIZES = (3, 4, 3, 4)


class Phase2Tab(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._status_label = QLabel("")
        self._status_label.setWordWrap(True)

        self._cards = [MetricCard(label) for label, _, _ in _METRIC_SPECS]

        layout = QVBoxLayout(self)
        layout.addWidget(self._status_label)

        card_iter = iter(self._cards)
        for row_size in _ROW_SIZES:
            row = QHBoxLayout()
            for _ in range(row_size):
                try:
                    row.addWidget(next(card_iter))
                except StopIteration:
                    break
            layout.addLayout(row)

        layout.addStretch(1)

        self.set_summary(None, None)

    def set_summary(self, summary, error_message: Optional[str]) -> None:
        if summary is None:
            self._status_label.setText(
                error_message
                or "Phase 2 requires valid Phase 1B substrate and doping outputs."
            )
            for card in self._cards:
                card.set_value("--")
            return

        self._status_label.setText("")

        for card, (label, attribute, unit) in zip(self._cards, _METRIC_SPECS):
            value = getattr(summary, attribute)
            card.set_value(format_engineering(value, unit))
