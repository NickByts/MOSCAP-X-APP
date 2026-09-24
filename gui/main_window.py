"""
main_window.py

PySide6 replacement for app.py's main() / Streamlit rendering
functions. This module contains NO scientific logic: every
calculation is delegated to the exact same backend functions
app.py already called, in the exact same order. Only the
presentation layer (Streamlit -> PySide6) and the addition of
background threads for long-running steps are new.
"""

from __future__ import annotations

import importlib.util
import traceback
import functools
import importlib.util
import traceback
from pathlib import Path
from typing import Any, Optional
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import (
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStatusBar,
    QTableView,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .format_utils import format_engineering
from .pandas_model import PandasModel
from .phase1_tab import Phase1Tab
from .phase2_tab import Phase2Tab
from .phase3_tab import Phase3Tab
from .plot_widget import PlotWidget
from .sidebar import Sidebar
from .worker import Worker

# ----------------------------------------------------------------
# Backend imports -- unchanged from app.py, including the same
# relative/absolute import fallback used there. Nothing here was
# rewritten, simplified, or renamed.
# ----------------------------------------------------------------

try:
    from .constants import (
        APP_DESCRIPTION,
        APP_NAME,
        DEFAULT_DEVICE_AREA_CM2,
        ELEMENTARY_CHARGE,
        MIN_DEVICE_AREA_CM2,
        SAMPLE_DATA_RELATIVE_PATH,
        STANDARD_CAPACITANCE_COLUMN,
        STANDARD_VOLTAGE_COLUMN,
        SUPPORTED_UPLOAD_TYPES,
    )
    from .data_loader import load_csv, load_data
    from .extraction_new.phase2_summary import calculate_phase2_summary
    from .extraction_new.phase2_models import (
        Phase2Inputs,
        Phase2MaterialProperties,
    )
    from .plot_phase1_pipeline import (
        plot_phase1_cv_regions,
        plot_phase1_inverse_c2_regions,
    )
    from .plotting import plot_cv, plot_inverse_c2, plot_normalized_cv
    from .preprocessing import (
        clean_data,
        convert_capacitance_units,
        validate_data,
    )
    from .utils import (
        add_normalized_capacitance,
        dataframe_to_csv_bytes,
        figure_to_png_bytes,
        format_scientific,
    )
    from .extraction_new.measurement_context import build_measurement_context
    from .Phase3.dit_plotter import plot_dit_vs_gate_voltage
    from .Phase3.analysis_window import (
        apply_analysis_window,
        full_range_window,
        snap_to_measured_frequency,
    )

except ImportError:
    from constants import (
        APP_DESCRIPTION,
        APP_NAME,
        DEFAULT_DEVICE_AREA_CM2,
        ELEMENTARY_CHARGE,
        MIN_DEVICE_AREA_CM2,
        SAMPLE_DATA_RELATIVE_PATH,
        STANDARD_CAPACITANCE_COLUMN,
        STANDARD_VOLTAGE_COLUMN,
        SUPPORTED_UPLOAD_TYPES,
    )
    from data_loader import load_csv, load_data
    from extraction_new.phase2_summary import calculate_phase2_summary
    from extraction_new.phase2_models import (
        Phase2Inputs,
        Phase2MaterialProperties,
    )
    from plotting import plot_cv, plot_inverse_c2, plot_normalized_cv
    from preprocessing import (
        clean_data,
        convert_capacitance_units,
        validate_data,
    )
    from plot_phase1_pipeline import (
        plot_phase1_cv_regions,
        plot_phase1_inverse_c2_regions,
    )
    from utils import (
        add_normalized_capacitance,
        dataframe_to_csv_bytes,
        figure_to_png_bytes,
        format_scientific,
    )
    from extraction_new.measurement_context import build_measurement_context
    from Phase3.dit_plotter import plot_dit_vs_gate_voltage
    from Phase3.analysis_window import (
        apply_analysis_window,
        full_range_window,
        snap_to_measured_frequency,
    )


try:
    from measurement_statistics import calculate_statistics
except ImportError:
    from .measurement_statistics import calculate_statistics

try:
    from .extraction_new.phase1_pipeline import run_phase1_pipeline
except ImportError:
    from extraction_new.phase1_pipeline import run_phase1_pipeline

try:
    from .Phase3.phase3_pipeline import run_phase3
    from .Phase3.gp_plotter import plot_all_gp_over_omega, plot_gp_over_omega
    from .Phase3.phase3_summary import calculate_phase3_summary
    from .Phase3.dit_table import create_dit_table
    from .Phase3.dit_plotter import plot_dit_vs_gate_voltage
except ImportError:
    from Phase3.phase3_pipeline import run_phase3
    from Phase3.gp_plotter import plot_all_gp_over_omega, plot_gp_over_omega
    from Phase3.phase3_summary import calculate_phase3_summary
    from Phase3.dit_table import create_dit_table
    from Phase3.dit_plotter import plot_dit_vs_gate_voltage


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle(APP_NAME)
        self.resize(1400, 900)

        self._thread_pool = QThreadPool.globalInstance()

        # Cached pipeline state, mirroring the local variables that
        # used to live inside app.py's main().
        self._selected_sheet_name: str | None = None
        self._measurement_context = None
        self._device_area_cm2: float = DEFAULT_DEVICE_AREA_CM2
        self._cleaned_data: Optional[pd.DataFrame] = None
        self._phase1b_summary = None
        self._phase2_summary = None
        self._phase2_inputs = None

        self._build_ui()

        self.statusBar().showMessage("Ready")

    # ------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------

    def _build_ui(self) -> None:
        self.sidebar = Sidebar(
            default_device_area_cm2=DEFAULT_DEVICE_AREA_CM2,
            min_device_area_cm2=MIN_DEVICE_AREA_CM2,
            supported_upload_types=list(SUPPORTED_UPLOAD_TYPES),
        )
        self.sidebar.settingsChanged.connect(self._on_settings_changed)

        self.sidebar.datasetUploaded.connect(
            self._on_dataset_uploaded
        )

        self.sidebar.datasetReady.connect(
            self._on_dataset_ready
        )

        self.tabs = QTabWidget()

        self._raw_data_view = QTableView()
        self._raw_data_model = PandasModel(pd.DataFrame())
        self._raw_data_view.setModel(self._raw_data_model)
        self._source_label = QLabel("")
        raw_tab = self._wrap(self._source_label, self._raw_data_view)
        self.tabs.addTab(raw_tab, "Raw Data")

        self._validation_label = QLabel("")
        self._validation_label.setWordWrap(True)
        validation_tab = self._wrap(self._validation_label)
        self.tabs.addTab(validation_tab, "Validation")

        self._cleaned_data_view = QTableView()
        self._cleaned_data_model = PandasModel(pd.DataFrame())
        self._cleaned_data_view.setModel(self._cleaned_data_model)
        self._download_cleaned_button = QPushButton("Download Cleaned CSV")
        self._download_cleaned_button.clicked.connect(
            self._on_download_cleaned_clicked
        )
        self._download_cleaned_button.setEnabled(False)
        cleaned_tab = self._wrap(
            self._cleaned_data_view, self._download_cleaned_button
        )
        self.tabs.addTab(cleaned_tab, "Cleaned Data")

        from .metric_card import MetricCard

        self._statistics_labels = (
            "Total Points",
            "Voltage Min",
            "Voltage Max",
            "Capacitance Min",
            "Capacitance Max",
            "Capacitance Mean",
            "Capacitance Std",
        )
        self._statistics_cards = {
            label: MetricCard(label) for label in self._statistics_labels
        }
        self._statistics_status_label = QLabel("")
        self._statistics_status_label.setWordWrap(True)
        stats_tab = self._build_statistics_tab()
        self.tabs.addTab(stats_tab, "Statistics")

        self._cv_plot_widget = PlotWidget(
            figure_to_png_bytes, default_file_name="moscap_x_cv.png"
        )
        self._inverse_c2_plot_widget = PlotWidget(
            figure_to_png_bytes, default_file_name="moscap_x_inverse_c2.png"
        )
        plots_tab = self._wrap(
            QLabel("C-V Plot"),
            self._cv_plot_widget,
            QLabel("1/C\u00b2-V Plot"),
            self._inverse_c2_plot_widget,
        )
        self.tabs.addTab(self._make_scrollable(plots_tab), "Plots")

        self.phase1_tab = Phase1Tab(figure_to_png_bytes)
        self.tabs.addTab(self._make_scrollable(self.phase1_tab), "C–V Analysis")

        self.phase2_tab = Phase2Tab()
        self.tabs.addTab(self._make_scrollable(self.phase2_tab), "Parameter Extraction")

        self.phase3_tab = Phase3Tab(
            plot_all_gp_over_omega=plot_all_gp_over_omega,
            plot_gp_over_omega=plot_gp_over_omega,
            calculate_phase3_summary=calculate_phase3_summary,
            create_dit_table=create_dit_table,
            plot_dit_vs_gate_voltage=plot_dit_vs_gate_voltage,
            figure_to_png_bytes=figure_to_png_bytes,
            dataframe_to_csv_bytes=dataframe_to_csv_bytes,
            apply_analysis_window=functools.partial(
                apply_analysis_window, elementary_charge=ELEMENTARY_CHARGE
            ),
            full_range_window=full_range_window,
            snap_to_measured_frequency=snap_to_measured_frequency,
        )
        self.phase3_tab.workbookUploaded.connect(self._on_phase3_workbook_uploaded)
        self.tabs.addTab(self._make_scrollable(self.phase3_tab), "Interface Trap Analysis")

        splitter = QSplitter()
        splitter.addWidget(self.sidebar)
        splitter.addWidget(self.tabs)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([320, 1080])

        self.setCentralWidget(splitter)
        self.setStatusBar(QStatusBar())

    def _build_statistics_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(self._statistics_status_label)

        from PySide6.QtWidgets import QHBoxLayout

        row1 = QHBoxLayout()
        for label in self._statistics_labels[:4]:
            row1.addWidget(self._statistics_cards[label])
        row2 = QHBoxLayout()
        for label in self._statistics_labels[4:]:
            row2.addWidget(self._statistics_cards[label])

        layout.addLayout(row1)
        layout.addLayout(row2)
        layout.addStretch(1)
        return widget

    @staticmethod
    def _wrap(*widgets: QWidget) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        for widget in widgets:
            layout.addWidget(widget)
        return container

    @staticmethod
    def _make_scrollable(widget: QWidget) -> QScrollArea:
        """
        Wrap `widget` in a QScrollArea so tabs whose content (stacked
        plots, cards, tables) is taller than the visible tab area
        become vertically scrollable instead of being clipped.

        setWidgetResizable(True) lets the scroll area resize `widget`
        to match the viewport's width, while still respecting
        `widget`'s own minimum/preferred height -- so a vertical
        scrollbar appears exactly when the content doesn't fit,
        without altering anything about the widget's contents, order,
        or behaviour.
        """
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(widget)
        return scroll_area

    # ------------------------------------------------------------
    # Sidebar reactions
    # ------------------------------------------------------------

    def _on_settings_changed(self) -> None:
        uploaded_file = self.sidebar.uploaded_file_path()

        if uploaded_file is None:
            return

        self._run_main_pipeline(
            uploaded_file_path=uploaded_file,
            sheet_name=self._selected_sheet_name,
        )

    def _on_dataset_uploaded(
        self,
        file_path: str,
    ) -> None:
        """
        CSV upload path.

        CSV files start analysis immediately.
        """

        self._run_main_pipeline(
            uploaded_file_path=file_path,
        )

    def _on_dataset_ready(
        self,
        file_path: str,
        sheet_name: str,
    ) -> None:

        self._selected_sheet_name = sheet_name

        self._run_main_pipeline(
            uploaded_file_path=file_path,
            sheet_name=sheet_name,
        )

    # ------------------------------------------------------------
    # Main pipeline (sections 1-9 of the original app.py), run in
    # a background thread since it includes the Phase 1 regression
    # and Phase 2 calculation.
    # ------------------------------------------------------------

    def _run_main_pipeline(
        self,
        uploaded_file_path: Optional[str],
        sheet_name: str | None = None,
    ) -> None:
        self.statusBar().showMessage("Running analysis...")

        context = build_measurement_context(
            material=self.sidebar.material(),
            substrate_type=self.sidebar.substrate_type(),
            temperature_k=self.sidebar.temperature_k(),
        )
        device_area_cm2 = self.sidebar.device_area_cm2()
        nc_cm3 = self.sidebar.nc_cm3()
        nv_cm3 = self.sidebar.nv_cm3()
        metal_work_function_ev = (
            self.sidebar.metal_work_function_ev()
        )
        capacitance_unit = "F"

        worker = Worker(
            self._compute_main_pipeline,
            uploaded_file_path,
            sheet_name,
            context,
            device_area_cm2,
            nc_cm3,
            nv_cm3,
            metal_work_function_ev,
            capacitance_unit,
        )
        worker.signals.finished.connect(self._on_main_pipeline_finished)
        worker.signals.error.connect(self._on_main_pipeline_failed)
        self._thread_pool.start(worker)

    def _compute_main_pipeline(
        self,
        uploaded_file_path: Optional[str],
        sheet_name: str | None,
        measurement_context,
        device_area_cm2: float,
        nc_cm3: float,
        nv_cm3: float,
        metal_work_function_ev: float,
        capacitance_unit: str,
    ) -> dict:
        """
        Runs on a worker thread. Mirrors app.py's main() body for
        sections 1 through 9 exactly -- same functions, same
        order, same parameters.
        """

        if uploaded_file_path is None:
            raise ValueError("No dataset selected.")

        raw_data = load_data(
            uploaded_file_path,
            sheet_name=sheet_name,
        )
        if sheet_name:
            source_name = f"{Path(uploaded_file_path).name} — {sheet_name}"
        else:
            source_name = Path(uploaded_file_path).name

        validation_warnings = validate_data(raw_data)

        cleaned_data = clean_data(raw_data)
        cleaned_data = convert_capacitance_units(cleaned_data, capacitance_unit)
        analysis_data = add_normalized_capacitance(cleaned_data, device_area_cm2)

        statistics_error: Optional[str] = None
        statistics: Optional[dict] = None
        if not cleaned_data.empty:
            try:
                statistics = self._calculate_statistics(cleaned_data)
            except ValueError as exc:
                statistics_error = str(exc)

        cv_figure = None
        cv_error: Optional[str] = None
        try:
            cv_figure = plot_cv(cleaned_data)
        except ValueError as exc:
            cv_error = str(exc)

        phase1b_summary = None
        phase1b_error: Optional[str] = None
        try:
            voltage_array = pd.to_numeric(
                cleaned_data[STANDARD_VOLTAGE_COLUMN], errors="coerce"
            ).to_numpy(dtype=float)
            capacitance_array = pd.to_numeric(
                cleaned_data[STANDARD_CAPACITANCE_COLUMN], errors="coerce"
            ).to_numpy(dtype=float)
            phase1b_summary = run_phase1_pipeline(
                voltage=voltage_array,
                capacitance=capacitance_array,
                context=measurement_context,
                area_cm2=device_area_cm2,
            )
        except Exception as exc:
            phase1b_error = str(exc)

        inverse_c2_figure = None
        inverse_c2_error: Optional[str] = None
        try:
            inverse_c2_figure = plot_inverse_c2(cleaned_data)
        except ValueError as exc:
            inverse_c2_error = str(exc)

        region_figure = None
        if phase1b_summary is not None:
            try:
                region_figure = plot_phase1_inverse_c2_regions(
                    features=phase1b_summary.features,
                    linear_region=phase1b_summary.linear_region,
                    dataset=phase1b_summary.dataset,
                    fit=phase1b_summary.fit,
                )
            except Exception:
                region_figure = None

        phase2_summary = None
        phase2_inputs = None
        phase2_error: Optional[str] = None

        if phase1b_summary is not None:
            try:
                phase2_inputs = Phase2Inputs(
                    area_cm2=device_area_cm2,
                    temperature_k=phase1b_summary.context.temperature_k,
                    doping_cm3=phase1b_summary.doping.doping_value,
                    substrate_type=phase1b_summary.context.substrate_type,
                    cox_f=phase1b_summary.cox.cox,
                    v0_v=phase1b_summary.vintercept.vintercept,
                    ld_cm=phase1b_summary.debye.debye_length,
                    cs_f=phase1b_summary.csfb.csfb,
                    cfb_f=phase1b_summary.cfb.cfb,
                    vfb_v=phase1b_summary.vfb.vfb,
                    phi_m_ev=metal_work_function_ev,
                    nc_cm3=nc_cm3,
                    nv_cm3=nv_cm3,
                )

                phase2_materials = Phase2MaterialProperties(
                    intrinsic_concentration_cm3=(
                        phase1b_summary.context
                        .intrinsic_carrier_concentration_cm3
                    ),
                    bandgap_ev=(
                        phase1b_summary.context.bandgap_ev
                    ),
                    electron_affinity_ev=(
                        phase1b_summary.context
                        .electron_affinity_ev
                    ),
                    relative_permittivity=(
                        phase1b_summary.context
                        .relative_permittivity
                    ),
                )

                phase2_summary = calculate_phase2_summary(
                    phase2_inputs,
                    phase2_materials,
                )

            except (ArithmeticError, ValueError) as exc:
                phase2_error = str(exc)

        return {
            "raw_data": raw_data,
            "source_name": source_name,
            "validation_warnings": validation_warnings,
            "cleaned_data": cleaned_data,
            "analysis_data": analysis_data,
            "statistics": statistics,
            "statistics_error": statistics_error,
            "cv_figure": cv_figure,
            "cv_error": cv_error,
            "phase1b_summary": phase1b_summary,
            "phase1b_error": phase1b_error,
            "inverse_c2_figure": inverse_c2_figure,
            "inverse_c2_error": inverse_c2_error,
            "region_figure": region_figure,
            "phase2_summary": phase2_summary,
            "phase2_inputs": phase2_inputs,
            "phase2_error": phase2_error,
        }

    def _calculate_statistics(self, dataframe: pd.DataFrame) -> dict:
        return calculate_statistics(dataframe)

    

    def _on_main_pipeline_finished(self, result: dict) -> None:
        self.statusBar().showMessage("Ready", 3000)

        self._source_label.setText(f"Source: {result['source_name']}")
        self._raw_data_model.set_dataframe(result["raw_data"])

        warnings = result["validation_warnings"]
        if warnings:
            self._validation_label.setText("\n".join(warnings))
        else:
            self._validation_label.setText("Validation passed with no warnings.")

        cleaned_data = result["cleaned_data"]
        self._cleaned_data = cleaned_data
        self._cleaned_data_model.set_dataframe(result["analysis_data"])
        self._download_cleaned_button.setEnabled(not cleaned_data.empty)

        if cleaned_data.empty:
            QMessageBox.warning(
                self, "MOSCAP-X", "No valid rows remain after cleaning."
            )
            return

        if result["statistics"] is not None:
            self._statistics_status_label.setText("")
            for label, key in zip(
                self._statistics_labels,
                (
                    "total_points",
                    "voltage_min",
                    "voltage_max",
                    "capacitance_min",
                    "capacitance_max",
                    "capacitance_mean",
                    "capacitance_std",
                ),
            ):
                value = result["statistics"][key]
                if key == "total_points":
                    text = str(int(value))
                else:
                    text = format_scientific(value)
                self._statistics_cards[label].set_value(text)
        else:
            self._statistics_status_label.setText(
                f"Statistics unavailable: {result['statistics_error']}"
            )

        if result["cv_error"] is None:
            self._cv_plot_widget.set_figure(result["cv_figure"])
        else:
            self._cv_plot_widget.set_figure(None)

        if result["inverse_c2_error"] is None:
            self._inverse_c2_plot_widget.set_figure(result["inverse_c2_figure"])
        else:
            self._inverse_c2_plot_widget.set_figure(None)

        self._phase1b_summary = result["phase1b_summary"]
        self.phase1_tab.set_summary(
            result["phase1b_summary"],
            result["phase1b_error"],
            region_figure=result["region_figure"],
        )

        self._phase2_summary = result["phase2_summary"]
        self._phase2_inputs = result["phase2_inputs"]
        self.phase2_tab.set_summary(result["phase2_summary"], result["phase2_error"])

    def _on_main_pipeline_failed(self, exc: Exception, formatted_traceback: str) -> None:
        self.statusBar().showMessage("Error", 5000)
        QMessageBox.critical(self, "MOSCAP-X", str(exc))

    def _on_download_cleaned_clicked(self) -> None:
        if self._cleaned_data is None:
            return

        from PySide6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Download Cleaned CSV",
            "moscap_x_cleaned_data.csv",
            "CSV Files (*.csv)",
        )
        if not file_path:
            return

        try:
            data = dataframe_to_csv_bytes(self._cleaned_data)
            Path(file_path).write_bytes(data)
        except Exception as exc:
            QMessageBox.warning(self, "Save Failed", str(exc))

    # ------------------------------------------------------------
    # Phase 3 (separate workbook upload, separate worker)
    # ------------------------------------------------------------

    def _on_phase3_workbook_uploaded(self, file_path: str) -> None:
        if self._phase2_summary is None:
            self.phase3_tab.show_error("Phase 3 requires valid Phase 1B results.")
            return

        self.statusBar().showMessage("Running Phase 3 analysis...")

        worker = Worker(
            run_phase3,
            excel_file=file_path,
            phase2_results=self._phase2_summary,
            phase2_inputs=self._phase2_inputs,
        )
        worker.signals.finished.connect(self._on_phase3_finished)
        worker.signals.error.connect(self._on_phase3_failed)
        self._thread_pool.start(worker)

    def _on_phase3_finished(self, phase3_results: Any) -> None:
        self.statusBar().showMessage("Ready", 3000)
        self.phase3_tab.set_results(phase3_results, area_cm2=self._phase2_inputs.area_cm2)

    def _on_phase3_failed(self, exc: Exception, formatted_traceback: str) -> None:
        self.statusBar().showMessage("Error", 5000)
        self.phase3_tab.show_error(str(exc))