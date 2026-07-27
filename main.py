"""
main.py

Entry point for the MOSCAP-X desktop application.

Replaces:
    streamlit run app.py
with:
    python main.py
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from gui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("MOSCAP-X")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
