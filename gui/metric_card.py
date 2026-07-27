"""
metric_card.py

Reusable widget standing in for Streamlit's st.metric(). Pure
presentation -- takes an already-formatted label/value pair
and displays it.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class MetricCard(QFrame):
    """A labeled value card, e.g. MetricCard("Cox", "1.234E-12 F")."""

    def __init__(self, label: str, value: str = "--", parent=None) -> None:
        super().__init__(parent)

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setObjectName("MetricCard")

        self._label_widget = QLabel(label)
        self._label_widget.setObjectName("MetricLabel")
        self._label_widget.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self._value_widget = QLabel(value)
        self._value_widget.setObjectName("MetricValue")
        self._value_widget.setWordWrap(True)
        self._value_widget.setAlignment(Qt.AlignmentFlag.AlignLeft)

        font = self._value_widget.font()
        font.setPointSize(font.pointSize() + 3)
        font.setBold(True)
        self._value_widget.setFont(font)

        layout = QVBoxLayout(self)
        layout.addWidget(self._label_widget)
        layout.addWidget(self._value_widget)

    def set_label(self, label: str) -> None:
        self._label_widget.setText(label)

    def set_value(self, value: str) -> None:
        self._value_widget.setText(value)
