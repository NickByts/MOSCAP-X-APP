"""
worker.py

Generic background-worker plumbing so long-running backend
calls (Phase 1 / Phase 2 / Phase 3 pipelines) never block the
Qt event loop. This module contains no scientific logic -- it
only moves an existing callable onto a QThreadPool thread and
reports the outcome back via signals.
"""

from __future__ import annotations

import traceback
from typing import Any, Callable

from PySide6.QtCore import QObject, QRunnable, Signal, Slot


class WorkerSignals(QObject):
    """
    Signals emitted by a Worker.

    finished
        Emitted with the wrapped callable's return value on
        success.
    error
        Emitted with (exception, formatted_traceback) on
        failure. The GUI thread turns this into a status bar
        message / QMessageBox; it never re-raises here.
    """

    finished = Signal(object)
    error = Signal(object, str)


class Worker(QRunnable):
    """
    Runs `fn(*args, **kwargs)` on a QThreadPool thread.

    Usage
    -----
        worker = Worker(run_phase1_pipeline, voltage=..., capacitance=...)
        worker.signals.finished.connect(self._on_phase1_done)
        worker.signals.error.connect(self._on_phase1_failed)
        QThreadPool.globalInstance().start(worker)

    This changes nothing about what `fn` computes -- it only
    changes which thread it runs on.
    """

    def __init__(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs
        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            result = self._fn(*self._args, **self._kwargs)
        except Exception as exc:  # noqa: BLE001 - surfaced to the GUI thread
            self.signals.error.emit(exc, traceback.format_exc())
        else:
            self.signals.finished.emit(result)
