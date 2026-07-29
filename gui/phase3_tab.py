"""
phase3_tab.py

Phase 3 tab: conductance-workbook upload, independent log/linear
toggles for the Frequency (X) axis and the Gp/omega (Y) axis, the
all-gate-voltages overlay plot, per-gate-voltage inspection
(including the Measurement Analysis Window), extracted parameters,
the Phase 3 summary cards, the Dit results table, and the Dit-vs-
gate-voltage plot.

This is a view component: it holds the current Phase3Results and
replots on x-scale / y-scale / gate-voltage / analysis-window
changes without asking the caller to recompute anything by hand --
every backend function it needs, including the analysis-window
pipeline, is injected in __init__, so this file has no scientific
logic and no dependency on how Phase3 is packaged.

Peak/Dit lookup is done by gate_voltage, not by list position,
matching the earlier app.py fix: peak_results and dit_results
only contain sweeps that passed validation (or have since had an
analysis window applied), so they can be shorter than
voltage_sweeps.

Analysis-window state (the per-gate-voltage [minimum_frequency,
maximum_frequency] range) and both axis-scale selections belong to
this tab, not to Phase3Results: they are session/workbook-scoped
only, reset every time set_results() is called for a newly-uploaded
workbook, and never persisted.
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
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from .analysis_window_plot import AnalysisWindowPlotWidget
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
        apply_analysis_window: Callable,
        full_range_window: Callable,
        snap_to_measured_frequency: Callable,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self._plot_all_gp_over_omega = plot_all_gp_over_omega
        self._plot_gp_over_omega = plot_gp_over_omega
        self._calculate_phase3_summary = calculate_phase3_summary
        self._create_dit_table = create_dit_table
        self._plot_dit_vs_gate_voltage = plot_dit_vs_gate_voltage
        self._dataframe_to_csv_bytes = dataframe_to_csv_bytes
        self._apply_analysis_window = apply_analysis_window
        self._full_range_window = full_range_window
        self._snap_to_measured_frequency = snap_to_measured_frequency

        self._phase3_results = None
        self._dit_table = None
        self._area_cm2: float = 0.0
        # gate_voltage -> (minimum_frequency, maximum_frequency), reset on every set_results()
        self._analysis_windows: dict[float, tuple[float, float]] = {}

        # -- Workbook upload --------------------------------

        self.upload_button = QPushButton("Upload Phase 3 Conductance Workbook...")
        self.upload_button.clicked.connect(self._on_upload_clicked)

        self._status_label = QLabel(
            "Upload a Phase 3 conductance workbook to begin interface "
            "trap analysis."
        )
        self._status_label.setWordWrap(True)

        # -- Frequency axis (X) toggle ---------------------------

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

        # -- Gp/omega axis (Y) toggle -----------------------------
        #
        # Deliberately the same QGroupBox + QButtonGroup pattern as
        # the Frequency Axis controls above, wired the same way (only
        # the "log" radio's toggled signal connected -- toggling it
        # off implies the "linear" radio toggled on, and vice versa,
        # via the exclusive QButtonGroup). This selector only ever
        # changes how the already-computed Gp/omega values are
        # displayed; it never touches VoltageSweep, filtered arrays,
        # peak detection, or Dit extraction.

        gp_axis_group_box = QGroupBox("Gp/\u03c9 Axis")
        gp_axis_layout = QHBoxLayout(gp_axis_group_box)

        self._gp_log_radio = QRadioButton("log")
        self._gp_linear_radio = QRadioButton("linear")
        self._gp_linear_radio.setChecked(True)

        self._gp_axis_button_group = QButtonGroup(self)
        self._gp_axis_button_group.addButton(self._gp_log_radio)
        self._gp_axis_button_group.addButton(self._gp_linear_radio)

        gp_axis_layout.addWidget(self._gp_log_radio)
        gp_axis_layout.addWidget(self._gp_linear_radio)

        self._gp_log_radio.toggled.connect(self._on_gp_y_scale_changed)

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

        # -- Measurement Analysis Window ------------------------

        analysis_window_group_box = QGroupBox("Measurement Analysis Window")
        analysis_window_layout = QHBoxLayout(analysis_window_group_box)

        analysis_window_layout.addWidget(QLabel("Minimum Frequency (Hz)"))
        self._min_freq_input = QLineEdit()
        analysis_window_layout.addWidget(self._min_freq_input)

        analysis_window_layout.addWidget(QLabel("Maximum Frequency (Hz)"))
        self._max_freq_input = QLineEdit()
        analysis_window_layout.addWidget(self._max_freq_input)

        self._apply_window_button = QPushButton("Apply")
        analysis_window_layout.addWidget(self._apply_window_button)

        self._reset_window_button = QPushButton("Reset")
        analysis_window_layout.addWidget(self._reset_window_button)

        self._apply_window_button.clicked.connect(self._on_apply_analysis_window_clicked)
        self._reset_window_button.clicked.connect(self._on_reset_analysis_window_clicked)
        self._min_freq_input.returnPressed.connect(self._on_apply_analysis_window_clicked)
        self._max_freq_input.returnPressed.connect(self._on_apply_analysis_window_clicked)

        self._selected_plot_widget = AnalysisWindowPlotWidget(
            figure_to_png_bytes,
            default_file_name="phase3_selected_gate_voltage.png",
        )
        self._selected_plot_widget.analysisWindowDragged.connect(
            self._on_analysis_window_dragged
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
        layout.addWidget(gp_axis_group_box)
        layout.addWidget(QLabel("Gp/\u03c9 vs Frequency (All Gate Voltages)"))
        layout.addWidget(self._all_plot_widget)
        layout.addWidget(QLabel("Inspect Individual Gate Voltage"))
        layout.addWidget(self.gate_voltage_combo)
        layout.addWidget(analysis_window_group_box)
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
            self._gp_log_radio,
            self._gp_linear_radio,
            self.gate_voltage_combo,
            self._min_freq_input,
            self._max_freq_input,
            self._apply_window_button,
            self._reset_window_button,
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
        self._analysis_windows = {}
        self._set_results_dependent_widgets_enabled(False)
        self._all_plot_widget.set_figure(None)
        self._selected_plot_widget.set_figure_and_window(None, [], 0.0, 0.0)
        self._dit_plot_widget.set_figure(None)

    def set_results(self, phase3_results, area_cm2: float) -> None:
        """Called once run_phase3() succeeds for a newly uploaded workbook."""

        self._phase3_results = phase3_results
        self._area_cm2 = area_cm2
        self._status_label.setText("")
        self._set_results_dependent_widgets_enabled(True)

        # A fresh workbook resets both axis-scale selections back to
        # their defaults (Frequency = log, Gp/omega = linear) -- axis
        # scale is session/workbook-scoped only, exactly like the
        # analysis windows below, and never carries over between
        # uploads.
        self._log_radio.blockSignals(True)
        self._linear_radio.blockSignals(True)
        self._log_radio.setChecked(True)
        self._log_radio.blockSignals(False)
        self._linear_radio.blockSignals(False)

        self._gp_log_radio.blockSignals(True)
        self._gp_linear_radio.blockSignals(True)
        self._gp_linear_radio.setChecked(True)
        self._gp_log_radio.blockSignals(False)
        self._gp_linear_radio.blockSignals(False)

        # A fresh workbook also resets every per-voltage analysis
        # window to that sweep's full measured frequency range --
        # windows never survive a new upload.
        self._analysis_windows = {
            sweep.gate_voltage: self._full_range_window(sweep)
            for sweep in phase3_results.voltage_sweeps
        }

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

    def _current_y_scale(self) -> str:
        return "log" if self._gp_log_radio.isChecked() else "linear"

    def _current_selected_sweep(self):
        if self._phase3_results is None:
            return None
        selected_voltage = self.gate_voltage_combo.currentData()
        if selected_voltage is None:
            return None
        return next(
            (
                s
                for s in self._phase3_results.voltage_sweeps
                if s.gate_voltage == selected_voltage
            ),
            None,
        )

    def _dataset_has_positive_gp_over_omega(self) -> bool:
        """
        True if at least one Gp/omega value in the whole loaded
        workbook is positive. Used only to decide whether a
        logarithmic Gp/omega axis is meaningful at all; it never
        affects the underlying data, peak detection, or Dit
        extraction.
        """
        if self._phase3_results is None:
            return False

        return any(
            value > 0
            for sweep in self._phase3_results.voltage_sweeps
            if sweep.gp_over_omega is not None
            for value in sweep.gp_over_omega
        )

    def _on_x_scale_changed(self) -> None:
        if self._phase3_results is None:
            return
        self._refresh_all_plot()
        self._refresh_selected()

    def _on_gp_y_scale_changed(self) -> None:
        if self._phase3_results is None:
            return

        if self._gp_log_radio.isChecked() and not self._dataset_has_positive_gp_over_omega():
            QMessageBox.warning(
                self,
                "Gp/\u03c9 Axis",
                "Every Gp/\u03c9 value in this workbook is zero or "
                "negative, so a logarithmic Gp/\u03c9 axis has no "
                "positive points to display. Staying on a linear "
                "Gp/\u03c9 axis.",
            )
            # Triggers this handler again via the exclusive button
            # group (log radio becomes unchecked), which then falls
            # through to the refresh below with y_scale="linear".
            self._gp_linear_radio.setChecked(True)
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
            y_scale=self._current_y_scale(),
        )
        self._all_plot_widget.set_figure(figure)

    def _refresh_selected(self) -> None:
        if self.gate_voltage_combo.count() == 0:
            return

        sweep = self._current_selected_sweep()
        if sweep is None:
            return

        selected_voltage = sweep.gate_voltage
        window = self._analysis_windows[selected_voltage]
        self._update_analysis_window_inputs(window)

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
            y_scale=self._current_y_scale(),
        )
        minimum_frequency, maximum_frequency = window
        self._selected_plot_widget.set_figure_and_window(
            figure,
            measured_frequencies=sweep.frequency,
            minimum_frequency=minimum_frequency,
            maximum_frequency=maximum_frequency,
        )

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

    # ------------------------------------------------------------
    # Measurement Analysis Window
    # ------------------------------------------------------------

    def _update_analysis_window_inputs(self, window: tuple[float, float]) -> None:
        minimum_frequency, maximum_frequency = window
        self._min_freq_input.blockSignals(True)
        self._max_freq_input.blockSignals(True)
        self._min_freq_input.setText(f"{minimum_frequency:.6g}")
        self._max_freq_input.setText(f"{maximum_frequency:.6g}")
        self._min_freq_input.blockSignals(False)
        self._max_freq_input.blockSignals(False)

    def _apply_window_for_selected_voltage(self, sweep, window: tuple[float, float]) -> None:
        minimum_frequency, maximum_frequency = window

        try:
            _filtered_sweep, peak, dit = self._apply_analysis_window(
                sweep, minimum_frequency, maximum_frequency, self._area_cm2
            )
        except Exception as exc:
            QMessageBox.warning(self, "Analysis Window", str(exc))
            self._update_analysis_window_inputs(self._analysis_windows[sweep.gate_voltage])
            return

        self._analysis_windows[sweep.gate_voltage] = window
        self._replace_peak_and_dit(sweep.gate_voltage, peak, dit)

        self._refresh_selected()
        self._refresh_summary_and_table()

    def _replace_peak_and_dit(self, gate_voltage: float, peak, dit) -> None:
        results = self._phase3_results

        peaks_by_voltage = {p.gate_voltage: p for p in results.peak_results}
        dits_by_voltage = {d.gate_voltage: d for d in results.dit_results}

        peaks_by_voltage[gate_voltage] = peak
        dits_by_voltage[gate_voltage] = dit

        results.peak_results = [
            peaks_by_voltage[s.gate_voltage]
            for s in results.voltage_sweeps
            if s.gate_voltage in peaks_by_voltage
        ]
        results.dit_results = [
            dits_by_voltage[s.gate_voltage]
            for s in results.voltage_sweeps
            if s.gate_voltage in dits_by_voltage
        ]

    def _on_apply_analysis_window_clicked(self) -> None:
        sweep = self._current_selected_sweep()
        if sweep is None:
            return

        current_window = self._analysis_windows[sweep.gate_voltage]

        try:
            minimum_frequency = float(self._min_freq_input.text())
            maximum_frequency = float(self._max_freq_input.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid Frequency", "Enter numeric frequency values.")
            self._update_analysis_window_inputs(current_window)
            return

        lowest = float(min(sweep.frequency))
        highest = float(max(sweep.frequency))

        if minimum_frequency < lowest or maximum_frequency > highest:
            QMessageBox.warning(
                self,
                "Invalid Range",
                "Minimum and maximum frequency must fall within the "
                f"measured range ({lowest:.3E} Hz \u2013 {highest:.3E} Hz).",
            )
            self._update_analysis_window_inputs(current_window)
            return

        if minimum_frequency >= maximum_frequency:
            QMessageBox.warning(
                self, "Invalid Range", "Minimum frequency must be less than maximum frequency."
            )
            self._update_analysis_window_inputs(current_window)
            return

        minimum_frequency = self._snap_to_measured_frequency(sweep, minimum_frequency)
        maximum_frequency = self._snap_to_measured_frequency(sweep, maximum_frequency)

        if minimum_frequency >= maximum_frequency:
            QMessageBox.warning(
                self,
                "Invalid Range",
                "Those values snap to the same measured frequency point. "
                "Choose values closer to two different measured points.",
            )
            self._update_analysis_window_inputs(current_window)
            return

        self._apply_window_for_selected_voltage(sweep, (minimum_frequency, maximum_frequency))

    def _on_reset_analysis_window_clicked(self) -> None:
        sweep = self._current_selected_sweep()
        if sweep is None:
            return
        self._apply_window_for_selected_voltage(sweep, self._full_range_window(sweep))

    def _on_analysis_window_dragged(self, minimum_frequency: float, maximum_frequency: float) -> None:
        sweep = self._current_selected_sweep()
        if sweep is None:
            return
        self._apply_window_for_selected_voltage(sweep, (minimum_frequency, maximum_frequency))