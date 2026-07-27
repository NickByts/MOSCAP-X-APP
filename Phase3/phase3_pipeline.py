"""
phase3_pipeline.py

Main execution pipeline for Phase 3.

This module coordinates all Phase 3 processing.
"""

import numpy as np

from .excel_reader import read_phase3_workbook
from .phase3_models import Phase3Results
from .measurement_validator import validate_voltage_sweep
from .omega_calculator import calculate_omega
from .gp_extractor import calculate_gp_over_omega
from .peak_detector import detect_peak

from extraction_new.phase2_results import Phase2Results
from extraction_new.phase2_models import Phase2Inputs
from .dit_extractor import calculate_dit
from constants import ELEMENTARY_CHARGE


def run_phase3(
    excel_file,
    phase2_results: Phase2Results,
    phase2_inputs: Phase2Inputs,
    debug: bool = False,
    debug_figures: list | None = None,
) -> Phase3Results:
    """
    Execute the complete Phase 3 pipeline.

    Parameters
    ----------
    excel_file
        Uploaded Excel workbook.

    phase2_results : Phase2Results
        Results from Phase 2 containing the extracted Cox.

    debug : bool, optional
        When True, prints a candidate-peak summary table and
        builds a validation plot for every accepted sweep.
        Has no effect on detection, filtering, or results
        when False (the default). Default False.

    debug_figures : list, optional
        If provided while debug=True, each sweep's validation
        Figure is appended to this list for the caller to
        display or save (e.g. via st.pyplot() in Streamlit).
        Ignored when debug=False.

    Returns
    -------
    Phase3Results
    """

    voltage_sweeps = read_phase3_workbook(excel_file)

    cox = phase2_results.cox

    peak_results = []
    dit_results = []

    for sweep in voltage_sweeps:

        validate_voltage_sweep(sweep)

        calculate_omega(sweep)

        calculate_gp_over_omega(
            sweep=sweep,
            cox=cox,
        )


        


        if debug:

            signal = np.asarray(
                sweep.gp_over_omega,
                dtype=float,
            )


        peak = detect_peak(sweep)

        peak_results.append(peak)

        if debug:

    


            if debug_figures is not None:
                debug_figures.append

        dit = calculate_dit(
            peak=peak,
            area_cm2=phase2_inputs.area_cm2,
            elementary_charge=ELEMENTARY_CHARGE,
        )

        dit_results.append(dit)

    results = Phase3Results(
        voltage_sweeps=voltage_sweeps,
        peak_results=peak_results,
        dit_results=dit_results,
    )
    return results