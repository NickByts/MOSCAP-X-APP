"""
sidebar.py

PySide6 replacement for the Streamlit sidebar.

Contains:
- Material
- Substrate Type
- Temperature
- Device Area
- Nc
- Nv
- Metal Work Function
- Dataset upload controls

The scientific calculations are not performed here.
This widget only collects user inputs and exposes them
through getter methods.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
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
    Measurement Settings + Device + Semiconductor Parameters panel.

    settingsChanged
        Emitted whenever a measurement/device/material control changes.

    datasetUploaded
        Emitted with the selected file path for CSV uploads.

    datasetReady
        Emitted with file path and sheet name for Excel uploads.
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

        # ---------------------------------------------------------
        # Measurement Settings
        # ---------------------------------------------------------

        measurement_group = QGroupBox(
            "Measurement Settings"
        )

        measurement_layout = QFormLayout(
            measurement_group
        )

        self.material_combo = QComboBox()

        self.material_combo.addItems(
            [
                "Silicon",
                "Germanium",
            ]
        )

        measurement_layout.addRow(
            "Material",
            self.material_combo,
        )

        self.substrate_combo = QComboBox()

        self.substrate_combo.addItems(
            [
                "P-Type",
                "N-Type",
            ]
        )

        measurement_layout.addRow(
            "Substrate Type",
            self.substrate_combo,
        )

        self.temperature_spin = QDoubleSpinBox()

        self.temperature_spin.setRange(
            1.0,
            10000.0,
        )

        self.temperature_spin.setDecimals(2)

        self.temperature_spin.setValue(
            300.0
        )

        measurement_layout.addRow(
            "Temperature (K)",
            self.temperature_spin,
        )

        # ---------------------------------------------------------
        # Device
        # ---------------------------------------------------------

        device_group = QGroupBox(
            "Device"
        )

        device_layout = QFormLayout(
            device_group
        )

        self.device_area_spin = QDoubleSpinBox()

        self.device_area_spin.setDecimals(
            8
        )

        self.device_area_spin.setRange(
            min_device_area_cm2,
            1.0e6,
        )

        self.device_area_spin.setValue(
            default_device_area_cm2
        )

        device_layout.addRow(
            "Device Area (cm²)",
            self.device_area_spin,
        )

        # ---------------------------------------------------------
        # Semiconductor / Work-Function Parameters
        # ---------------------------------------------------------

        semiconductor_group = QGroupBox(
            "Semiconductor Parameters"
        )

        semiconductor_layout = QFormLayout(
            semiconductor_group
        )

        # Effective density of states in conduction band.
        self.nc_spin = QDoubleSpinBox()

        self.nc_spin.setRange(
            1.0e10,
            1.0e23,
        )

        self.nc_spin.setDecimals(
            4
        )

        self.nc_spin.setValue(
            2.8e19
        )

        self.nc_spin.setToolTip(
            "Effective density of states in the "
            "conduction band, Nc (cm⁻³)."
        )

        semiconductor_layout.addRow(
            "Nc (cm⁻³)",
            self.nc_spin,
        )

        # Effective density of states in valence band.
        self.nv_spin = QDoubleSpinBox()

        self.nv_spin.setRange(
            1.0e10,
            1.0e23,
        )

        self.nv_spin.setDecimals(
            4
        )

        self.nv_spin.setValue(
            1.04e19
        )

        self.nv_spin.setToolTip(
            "Effective density of states in the "
            "valence band, Nv (cm⁻³)."
        )

        semiconductor_layout.addRow(
            "Nv (cm⁻³)",
            self.nv_spin,
        )

        # Metal work function.
        self.metal_work_function_spin = QDoubleSpinBox()

        self.metal_work_function_spin.setRange(
            0.0,
            20.0,
        )

        self.metal_work_function_spin.setDecimals(
            4
        )

        # Preserves the previous hard-coded value.
        self.metal_work_function_spin.setValue(
            4.16
        )

        self.metal_work_function_spin.setToolTip(
            "Metal work function, Phi_m (eV)."
        )

        semiconductor_layout.addRow(
            "Metal Work Function (eV)",
            self.metal_work_function_spin,
        )

        # ---------------------------------------------------------
        # Dataset Upload
        # ---------------------------------------------------------

        self.upload_button = QPushButton(
            "Upload Dataset..."
        )

        self.upload_label = QLabel(
            "No dataset loaded"
        )

        self.sheet_label = QLabel(
            "Dataset"
        )

        self.sheet_combo = QComboBox()

        self.analyze_button = QPushButton(
            "Analyze Selected Sheet"
        )

        self.sheet_label.hide()
        self.sheet_combo.hide()
        self.analyze_button.hide()

        self.upload_label.setWordWrap(
            True
        )

        device_layout.addRow(
            self.upload_button
        )

        device_layout.addRow(
            self.upload_label
        )

        device_layout.addRow(
            self.sheet_label
        )

        device_layout.addRow(
            self.sheet_combo
        )

        device_layout.addRow(
            self.analyze_button
        )

        # ---------------------------------------------------------
        # Main Sidebar Layout
        # ---------------------------------------------------------

        layout = QVBoxLayout(
            self
        )

        layout.addWidget(
            measurement_group
        )

        layout.addWidget(
            device_group
        )

        layout.addWidget(
            semiconductor_group
        )

        layout.addStretch(1)

        # ---------------------------------------------------------
        # Signals
        # ---------------------------------------------------------

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

        self.nc_spin.valueChanged.connect(
            lambda _value: self.settingsChanged.emit()
        )

        self.nv_spin.valueChanged.connect(
            lambda _value: self.settingsChanged.emit()
        )

        self.metal_work_function_spin.valueChanged.connect(
            lambda _value: self.settingsChanged.emit()
        )

        self.upload_button.clicked.connect(
            self._on_upload_clicked
        )

        self.analyze_button.clicked.connect(
            self._on_analyze_clicked
        )

    # -------------------------------------------------------------
    # Dataset handling
    # -------------------------------------------------------------

    def _on_upload_clicked(self) -> None:
        extensions = " ".join(
            f"*.{ext}"
            for ext in self._supported_upload_types
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

        suffix = Path(
            file_path
        ).suffix.lower()

        if suffix in SUPPORTED_EXCEL_EXTENSIONS:

            try:
                sheets = get_excel_sheet_names(
                    file_path
                )

            except ValueError as exc:
                from PySide6.QtWidgets import QMessageBox

                QMessageBox.warning(
                    self,
                    "Workbook Error",
                    str(exc),
                )

                return

            self.sheet_combo.clear()

            self.sheet_combo.addItems(
                sheets
            )

            self.sheet_label.show()
            self.sheet_combo.show()
            self.analyze_button.show()

            return

        self.sheet_label.hide()
        self.sheet_combo.hide()
        self.analyze_button.hide()

        self.datasetUploaded.emit(
            file_path
        )

    # -------------------------------------------------------------
    # Existing getters
    # -------------------------------------------------------------

    def material(self) -> str:
        return self.material_combo.currentText()

    def substrate_type(self) -> str:
        return self.substrate_combo.currentText()

    def temperature_k(self) -> float:
        return float(
            self.temperature_spin.value()
        )

    def device_area_cm2(self) -> float:
        return float(
            self.device_area_spin.value()
        )

    def uploaded_file_path(self) -> Optional[str]:
        return self._uploaded_file_path

    # -------------------------------------------------------------
    # New Phase 2 getters
    # -------------------------------------------------------------

    def nc_cm3(self) -> float:
        """Return user-provided Nc in cm^-3."""
        return float(
            self.nc_spin.value()
        )

    def nv_cm3(self) -> float:
        """Return user-provided Nv in cm^-3."""
        return float(
            self.nv_spin.value()
        )

    def metal_work_function_ev(self) -> float:
        """Return user-provided metal work function in eV."""
        return float(
            self.metal_work_function_spin.value()
        )

    # -------------------------------------------------------------
    # Excel sheet analysis
    # -------------------------------------------------------------

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