"""
phase3_tab.py

Phase 3 tab: conductance-workbook upload, log/linear frequency
toggle, the all-gate-voltages overlay plot, per-gate-voltage
inspection, extracted parameters, the Phase 3 summary cards,
the Dit results table, and the Dit-vs-gate-voltage plot.

This is a view component: it holds the current Phase3Results
and replots on x-scale / gate-voltage changes without asking
the caller to recompute anything. It never imports Phase3.*
itself -- every backend function it needs is injected in
__init__, so this file has no scientific logic and no
dependency on how Phase3 is packaged.

Peak/Dit lookup is done by gate_voltage, not by list position,
matching the earlier app.py fix: peak_results and dit_results
only contain sweeps that passed validation, so they can be
shorter than voltage_sweeps.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from .format_utils import format_phase_1b_value
from .metric_card import MetricCard
from .pandas_model import PandasModel
from .plot_widget import PlotWidget


class Phase3Tab(QWidget):
    """
    Signals
    -------
    workbookUploaded(str)
        Emitted with the chosen file path when the user picks
        a Phase 3 conductance workbook.
    """

    workbookUploaded = Signal(str)

    def __init__(
        self,
        plot_all_gp_over_omega: Callable,
        plot_gp_over_omega: Callable,
        calculate_phase3_summary: Callable,
        create_dit_table: Callable,
        plot_dit_vs_gate_voltage: Callable,
        figure_to_png_bytes: Callable,
        dataframe_to_csv_bytes: Callable,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self._plot_all_gp_over_omega = plot_all_gp_over_omega
        self._plot_gp_over_omega = plot_gp_over_omega
        self._calculate_phase3_summary = calculate_phase3_summary
        self._create_dit_table = create_dit_table
        self._plot_dit_vs_gate_voltage = plot_dit_vs_gate_voltage
        self._dataframe_to_csv_bytes = dataframe_to_csv_bytes

        self._phase3_results = None
        self._dit_table = None

        # -- Workbook upload --------------------------------

        self.upload_button = QPushButton("Upload Phase 3 Conductance Workbook...")
        self.upload_button.clicked.connect(self._on_upload_clicked)

        self._status_label = QLabel(
            "Upload a Phase 3 conductance workbook to begin interface "
            "trap analysis."
        )
        self._status_label.setWordWrap(True)

        # -- Frequency axis toggle ---------------------------

        axis_group_box = QGroupBox("Frequency Axis")
        axis_layout = QHBoxLayout(axis_group_box)

        self._log_radio = QRadioButton("log")
        self._linear_radio = QRadioButton("linear")
        self._log_radio.setChecked(True)

        self._axis_button_group = QButtonGroup(self)
        self._axis_button_group.addButton(self._log_radio)
        self._axis_button_group.addButton(self._linear_radio)

        axis_layout.addWidget(self._log_radio)
        axis_layout.addWidget(self._linear_radio)

        self._log_radio.toggled.connect(self._on_x_scale_changed)

        # -- All-sweeps plot ----------------------------------

        self._all_plot_widget = PlotWidget(
            figure_to_png_bytes,
            default_file_name="phase3_all_gate_voltages.png",
        )

        # -- Per-gate-voltage inspection -----------------------

        self.gate_voltage_combo = QComboBox()
        self.gate_voltage_combo.currentIndexChanged.connect(
            self._on_gate_voltage_changed
        )

        self._selected_plot_widget = PlotWidget(
            figure_to_png_bytes,
            default_file_name="phase3_selected_gate_voltage.png",
        )

        self._peak_status_label = QLabel("")
        self._peak_status_label.setWordWrap(True)

        self._gate_voltage_card = MetricCard("Gate Voltage")
        self._peak_frequency_card = MetricCard("Peak Frequency")
        self._peak_gp_over_omega_card = MetricCard("Peak Gp/\u03c9")
        self._dit_card = MetricCard("Dit")

        extracted_row = QHBoxLayout()
        for card in (
            self._gate_voltage_card,
            self._peak_frequency_card,
            self._peak_gp_over_omega_card,
            self._dit_card,
        ):
            extracted_row.addWidget(card)

        # -- Phase 3 summary -----------------------------------

        self._summary_status_label = QLabel("")
        self._summary_status_label.setWordWrap(True)

        self._gate_voltages_card = MetricCard("Gate Voltages")
        self._average_dit_card = MetricCard("Average Dit")
        self._minimum_dit_card = MetricCard("Minimum Dit")
        self._maximum_dit_card = MetricCard("Maximum Dit")
        self._peak_frequency_range_card = MetricCard("Peak Frequency Range")
        self._gp_over_omega_range_card = MetricCard("Gp/\u03c9 Range")

        summary_row1 = QHBoxLayout()
        for card in (
            self._gate_voltages_card,
            self._average_dit_card,
            self._minimum_dit_card,
            self._maximum_dit_card,
        ):
            summary_row1.addWidget(card)

        summary_row2 = QHBoxLayout()
        for card in (
            self._peak_frequency_range_card,
            self._gp_over_omega_range_card,
        ):
            summary_row2.addWidget(card)

        # -- Dit table ------------------------------------------

        self._dit_table_view = QTableView()
        self._dit_table_model = PandasModel(self._create_empty_dataframe())
        self._dit_table_view.setModel(self._dit_table_model)

        self._download_button = QPushButton("Download Dit Table (CSV)")
        self._download_button.clicked.connect(self._on_download_clicked)
        self._download_button.setEnabled(False)

        # -- Dit vs gate voltage plot -----------------------------

        self._dit_plot_widget = PlotWidget(
            figure_to_png_bytes,
            default_file_name="phase3_dit_vs_gate_voltage.png",
        )

        # -- Assemble --------------------------------------------

        layout = QVBoxLayout(self)
        layout.addWidget(self.upload_button)
        layout.addWidget(self._status_label)
        layout.addWidget(axis_group_box)
        layout.addWidget(QLabel("Gp/\u03c9 vs Frequency (All Gate Voltages)"))
        layout.addWidget(self._all_plot_widget)
        layout.addWidget(QLabel("Inspect Individual Gate Voltage"))
        layout.addWidget(self.gate_voltage_combo)
        layout.addWidget(self._selected_plot_widget)
        layout.addWidget(QLabel("Extracted Parameters"))
        layout.addWidget(self._peak_status_label)
        layout.addLayout(extracted_row)
        layout.addWidget(QLabel("Phase 3 Summary"))
        layout.addWidget(self._summary_status_label)
        layout.addLayout(summary_row1)
        layout.addLayout(summary_row2)
        layout.addWidget(QLabel("Dit Results"))
        layout.addWidget(self._dit_table_view)
        layout.addWidget(self._download_button)
        layout.addWidget(QLabel("Dit vs Gate Voltage"))
        layout.addWidget(self._dit_plot_widget)

        self._set_results_dependent_widgets_enabled(False)

    # ------------------------------------------------------------
    # Static helpers
    # ------------------------------------------------------------

    @staticmethod
    def _create_empty_dataframe():
        import pandas as pd

        return pd.DataFrame()

    def _set_results_dependent_widgets_enabled(self, enabled: bool) -> None:
        for widget in (
            self._log_radio,
            self._linear_radio,
            self.gate_voltage_combo,
        ):
            widget.setEnabled(enabled)

    # ------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------

    def _on_upload_clicked(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Upload Phase 3 Conductance Workbook",
            "",
            "Excel Files (*.xlsx *.xls)",
        )

        if not file_path:
            return

        self.workbookUploaded.emit(file_path)

    def show_error(self, message: str) -> None:
        self._status_label.setText(f"Phase 3 unavailable: {message}")
        self._phase3_results = None
        self._set_results_dependent_widgets_enabled(False)
        self._all_plot_widget.set_figure(None)
        self._selected_plot_widget.set_figure(None)
        self._dit_plot_widget.set_figure(None)

    def set_results(self, phase3_results) -> None:
        """Called once run_phase3() succeeds for a newly uploaded workbook."""

        self._phase3_results = phase3_results
        self._status_label.setText("")
        self._set_results_dependent_widgets_enabled(True)

        self.gate_voltage_combo.blockSignals(True)
        self.gate_voltage_combo.clear()
        for sweep in phase3_results.voltage_sweeps:
            self.gate_voltage_combo.addItem(
                f"{sweep.gate_voltage:.2f} V", sweep.gate_voltage
            )
        self.gate_voltage_combo.blockSignals(False)

        self._refresh_all_plot()
        self._refresh_selected()
        self._refresh_summary_and_table()

    # ------------------------------------------------------------
    # Internal: reactive updates
    # ------------------------------------------------------------

    def _current_x_scale(self) -> str:
        return "log" if self._log_radio.isChecked() else "linear"

    def _on_x_scale_changed(self) -> None:
        if self._phase3_results is None:
            return
        self._refresh_all_plot()
        self._refresh_selected()

    def _on_gate_voltage_changed(self) -> None:
        if self._phase3_results is None:
            return
        self._refresh_selected()

    def _refresh_all_plot(self) -> None:
        figure = self._plot_all_gp_over_omega(
            self._phase3_results.voltage_sweeps,
            self._phase3_results.peak_results,
            x_scale=self._current_x_scale(),
        )
        self._all_plot_widget.set_figure(figure)

    def _refresh_selected(self) -> None:
        if self.gate_voltage_combo.count() == 0:
            return

        selected_voltage = self.gate_voltage_combo.currentData()
        if selected_voltage is None:
            return

        sweep = next(
            s
            for s in self._phase3_results.voltage_sweeps
            if s.gate_voltage == selected_voltage
        )

        peaks_by_voltage = {
            peak.gate_voltage: peak
            for peak in self._phase3_results.peak_results
        }

        dits_by_voltage = {
            dit.gate_voltage: dit
            for dit in self._phase3_results.dit_results
        }

        peak = peaks_by_voltage.get(selected_voltage)
        dit = dits_by_voltage.get(selected_voltage)

        figure = self._plot_gp_over_omega(
            sweep,
            peak,
            x_scale=self._current_x_scale(),
        )
        self._selected_plot_widget.set_figure(figure)

        if peak is None:
            self._peak_status_label.setText(
                "No valid conductance peak was detected for this "
                "gate voltage."
            )
            for card in (
                self._gate_voltage_card,
                self._peak_frequency_card,
                self._peak_gp_over_omega_card,
                self._dit_card,
            ):
                card.set_value("--")
            return

        self._peak_status_label.setText("")
        self._gate_voltage_card.set_value(f"{peak.gate_voltage:.2f} V")
        self._peak_frequency_card.set_value(f"{peak.peak_frequency:.3E} Hz")
        self._peak_gp_over_omega_card.set_value(f"{peak.peak_value:.3E}")

        if dit is not None:
            self._dit_card.set_value(f"{dit.dit:.3E} cm\u207b\u00b2eV\u207b\u00b9")
        else:
            self._dit_card.set_value("--")

    def _refresh_summary_and_table(self) -> None:
        try:
            summary = self._calculate_phase3_summary(self._phase3_results)
            table = self._create_dit_table(self._phase3_results)
        except Exception as exc:
            self._summary_status_label.setText(f"Phase 3 summary unavailable: {exc}")
            self._download_button.setEnabled(False)
            self._dit_plot_widget.set_figure(None)
            return

        self._summary_status_label.setText("")

        self._gate_voltages_card.set_value(str(summary.total_gate_voltages))
        self._average_dit_card.set_value(f"{summary.average_dit:.3E}")
        self._minimum_dit_card.set_value(f"{summary.minimum_dit:.3E}")
        self._maximum_dit_card.set_value(f"{summary.maximum_dit:.3E}")

        self._peak_frequency_range_card.set_value(
            f"{summary.minimum_peak_frequency:.3E}"
            " \u2013 "
            f"{summary.maximum_peak_frequency:.3E} Hz"
        )
        self._gp_over_omega_range_card.set_value(
            f"{summary.minimum_gp_over_omega:.3E}"
            " \u2013 "
            f"{summary.maximum_gp_over_omega:.3E}"
        )

        self._dit_table = table
        self._dit_table_model.set_dataframe(table)
        self._download_button.setEnabled(True)

        dit_figure = self._plot_dit_vs_gate_voltage(self._phase3_results)
        self._dit_plot_widget.set_figure(dit_figure)

    def _on_download_clicked(self) -> None:
        if self._dit_table is None:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Download Dit Table",
            "phase3_dit_results.csv",
            "CSV Files (*.csv)",
        )

        if not file_path:
            return

        try:
            data = self._dataframe_to_csv_bytes(self._dit_table)
            Path(file_path).write_bytes(data)
        except Exception as exc:
            QMessageBox.warning(self, "Save Failed", str(exc))
