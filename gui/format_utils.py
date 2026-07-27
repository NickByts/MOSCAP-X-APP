"""
format_utils.py

Pure numeric-formatting helpers, copied unchanged from the
Streamlit app.py (previously `_format_phase_1b_value` /
`_format_engineering`). No calculation logic lives here --
only string formatting of already-computed values.
"""

from __future__ import annotations

import numpy as np


def format_phase_1b_value(value: float) -> str:
    return f"{float(value):.3E}".replace("E+", "E")


def format_engineering(value: float, unit: str) -> str:
    numeric_value = float(value)
    if numeric_value == 0.0:
        return f"0 {unit}"

    magnitude = abs(numeric_value)
    if 0.1 <= magnitude < 1000.0:
        return f"{numeric_value:.4g} {unit}"

    exponent = int(np.floor(np.log10(magnitude) / 3.0) * 3)
    mantissa = numeric_value / (10.0**exponent)
    exponent_text = str(exponent) if exponent < 0 else f"+{exponent}"
    return f"{mantissa:.4g}E{exponent_text} {unit}"
