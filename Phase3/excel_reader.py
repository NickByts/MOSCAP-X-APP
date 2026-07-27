"""
excel_reader.py

Reads Phase 3 conductance measurement workbooks.

Each worksheet represents one gate voltage.

Returns a list of VoltageSweep objects.
"""

from __future__ import annotations

import re

import pandas as pd

from .phase3_models import VoltageSweep


# ============================================================
# Sheet Name Parser
# ============================================================

def extract_voltage_from_sheet_name(sheet_name: str) -> float:
    """
    Extract numerical gate voltage from worksheet name.

    Examples
    --------
    "0.2V"
    "0.2 V"
    "Gate_0.2V"
    "Vg=0.2"
    "-1.5V"

    Returns
    -------
    float
    """

    match = re.search(r"[-+]?\d*\.?\d+", sheet_name)

    if match is None:
        raise ValueError(
            f"Cannot determine voltage from worksheet name: '{sheet_name}'"
        )

    return float(match.group())


# ============================================================
# Workbook Reader
# ============================================================

COLUMN_ALIASES = {
    "frequency": {
        "frequency",
        "freq",
        "f",
    },
    "conductance": {
        "conductance",
        "g",
    },
    "capacitance": {
        "capacitance",
        "cap",
        "c",
    },
}

def read_phase3_workbook(excel_file) -> list[VoltageSweep]:
    """
    Read complete Phase 3 workbook.

    Parameters
    ----------
    excel_file
        Uploaded Excel workbook.

    Returns
    -------
    list[VoltageSweep]
    """

    workbook = pd.ExcelFile(excel_file)

    voltage_sweeps = []

    for sheet_name in workbook.sheet_names:

        dataframe = pd.read_excel(
            workbook,
            sheet_name=sheet_name,
        )

        if dataframe.empty:
            raise ValueError(
                f"Worksheet '{sheet_name}' is empty."
            )
        
        voltage = extract_voltage_from_sheet_name(sheet_name)

        dataframe.columns = [
            str(column).strip().lower()
            for column in dataframe.columns
        ]

        column_mapping = {}

        for canonical_name, aliases in COLUMN_ALIASES.items():

            for alias in aliases:

                if alias in dataframe.columns:

                    column_mapping[alias] = canonical_name

                    break

        dataframe = dataframe.rename(
            columns=column_mapping,
        )

        required_columns = {
            "frequency",
            "conductance",
            "capacitance",
        }

        missing_columns = required_columns - set(dataframe.columns)

        if missing_columns:
            raise ValueError(
                f"Worksheet '{sheet_name}' is missing required columns: "
                f"{', '.join(sorted(missing_columns))}"
            )

        frequency = dataframe["frequency"].to_numpy(dtype=float)

        conductance = dataframe["conductance"].to_numpy(dtype=float)

        capacitance = dataframe["capacitance"].to_numpy(dtype=float)

        sweep = VoltageSweep(
            gate_voltage=voltage,
            frequency=frequency,
            conductance=conductance,
            capacitance=capacitance,
        )

        voltage_sweeps.append(sweep)

    return voltage_sweeps