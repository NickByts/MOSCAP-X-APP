"""
sidebar.py

PySide6 replacement for the Streamlit sidebar in
_render_sidebar(): Material, Substrate Type, Temperature,
Device Area, Capacitance Unit, and the main dataset upload.

Only the widgets changed. The values this panel produces feed
into build_measurement_context(), exactly as before -- this
module does not call it itself, since MainWindow owns that
call (kept next to the rest of the pipeline orchestration).
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

try:
    from .data_loader import get_excel_sheet_names
    from .constants import SUPPORTED_EXCEL_EXTENSIONS
except ImportError:
    from data_loader import get_excel_sheet_names
    from constants import SUPPORTED_EXCEL_EXTENSIONS

class Sidebar(QWidget):
    """
    Measurement Settings + Device panel.

    settingsChanged
        Emitted whenever any measurement/device control
        changes. Carries no payload -- the owner reads current
        values via the getter methods below. This mirrors
        Streamlit re-running _render_sidebar() on every widget
        interaction.

    datasetUploaded
        Emitted with the chosen file path when the user picks
        a dataset file via "Upload Dataset...".
    """

    settingsChanged = Signal()

    datasetUploaded = Signal(str)

    datasetReady = Signal(str, str)

    def __init__(
        self,
        default_device_area_cm2: float,
        min_device_area_cm2: float,
        supported_upload_types: List[str],
        parent=None,
    ) -> None:
        super().__init__(parent)

        self._supported_upload_types = supported_upload_types
        self._uploaded_file_path: Optional[str] = None

        measurement_group = QGroupBox("Measurement Settings")
        measurement_layout = QFormLayout(measurement_group)

        self.material_combo = QComboBox()
        self.material_combo.addItems(["Silicon", "Germanium"])
        measurement_layout.addRow("Material", self.material_combo)

        self.substrate_combo = QComboBox()
        self.substrate_combo.addItems(["P-Type", "N-Type"])
        measurement_layout.addRow("Substrate Type", self.substrate_combo)

        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.0, 10000.0)
        self.temperature_spin.setDecimals(2)
        self.temperature_spin.setValue(300.0)
        measurement_layout.addRow("Temperature (K)", self.temperature_spin)

        device_group = QGroupBox("Device")
        device_layout = QFormLayout(device_group)

        self.device_area_spin = QDoubleSpinBox()
        self.device_area_spin.setDecimals(8)
        self.device_area_spin.setRange(min_device_area_cm2, 1.0e6)
        self.device_area_spin.setValue(default_device_area_cm2)
        device_layout.addRow("Device Area (cm\u00b2)", self.device_area_spin)


        self.upload_button = QPushButton("Upload Dataset...")
        self.upload_label = QLabel("No dataset loaded")
        self.sheet_label = QLabel("Dataset")
        self.sheet_combo = QComboBox()

        self.analyze_button = QPushButton(
            "Analyze Selected Sheet"
        )
        self.sheet_label.hide()
        self.sheet_combo.hide()
        self.analyze_button.hide()
        self.upload_label.setWordWrap(True)
        device_layout.addRow(self.upload_button)
        device_layout.addRow(self.upload_label)
        device_layout.addRow(self.sheet_label)
        device_layout.addRow(self.sheet_combo)
        device_layout.addRow(self.analyze_button)

        layout = QVBoxLayout(self)
        layout.addWidget(measurement_group)
        layout.addWidget(device_group)
        layout.addStretch(1)

        self.material_combo.currentIndexChanged.connect(
            lambda _index: self.settingsChanged.emit()
        )
        self.substrate_combo.currentIndexChanged.connect(
            lambda _index: self.settingsChanged.emit()
        )
        self.temperature_spin.valueChanged.connect(
            lambda _value: self.settingsChanged.emit()
        )
        self.device_area_spin.valueChanged.connect(
            lambda _value: self.settingsChanged.emit()
        )
        self.upload_button.clicked.connect(self._on_upload_clicked)

        self.analyze_button.clicked.connect(
            self._on_analyze_clicked
        )

    def _on_upload_clicked(self) -> None:
        extensions = " ".join(
            f"*.{ext}" for ext in self._supported_upload_types
        )

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Upload Dataset",
            "",
            f"Supported Files ({extensions})",
        )

        if not file_path:
            return

        self._uploaded_file_path = file_path
        self.upload_label.setText(
            f"Using: {Path(file_path).name}"
        )

        suffix = Path(file_path).suffix.lower()

        if suffix in SUPPORTED_EXCEL_EXTENSIONS:

            try:
                sheets = get_excel_sheet_names(file_path)
            except ValueError as exc:
                from PySide6.QtWidgets import QMessageBox

                QMessageBox.warning(
                    self,
                    "Workbook Error",
                    str(exc),
                )
                return

            self.sheet_combo.clear()
            self.sheet_combo.addItems(sheets)

            self.sheet_label.show()
            self.sheet_combo.show()
            self.analyze_button.show()

            return

        self.sheet_label.hide()
        self.sheet_combo.hide()
        self.analyze_button.hide()

        self.datasetUploaded.emit(file_path)

    def material(self) -> str:
        return self.material_combo.currentText()

    def substrate_type(self) -> str:
        return self.substrate_combo.currentText()

    def temperature_k(self) -> float:
        return float(self.temperature_spin.value())

    def device_area_cm2(self) -> float:
        return float(self.device_area_spin.value())

    def uploaded_file_path(self) -> Optional[str]:
        return self._uploaded_file_path

    def _on_analyze_clicked(self) -> None:

        if self._uploaded_file_path is None:
            return

        sheet = self.sheet_combo.currentText()

        if not sheet:
            return

        self.datasetReady.emit(
            self._uploaded_file_path,
            sheet,
        )