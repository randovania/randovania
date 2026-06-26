from __future__ import annotations

import logging
import platform
import sys
from abc import abstractmethod
from types import TracebackType

# Reference for this module:
# https://github.com/h3llrais3r/Deluge-PreventSuspendPlus/blob/master/preventsuspendplus/core.py
#
# Copyright (C) 2015 h3llrais3r <pooh_beer_1@hotmail.com>
# Copyright (C) 2009 Ian Martin <ianmartin@cantab.net>


class InhibitorSource:
    @abstractmethod
    def inhibit(self) -> None:
        """
        Inhibits sleep until `uninhibit` is called.
        """

    @abstractmethod
    def uninhibit(self) -> None:
        """
        Cancels a previous call to `inhibit`.
        """


class WindowsInhibitorSource(InhibitorSource):
    """https://msdn.microsoft.com/en-us/library/windows/desktop/aa373208(v=vs.85).aspx"""

    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001

    def __init__(self) -> None:
        import ctypes

        self.ctypes = ctypes

    def inhibit(self) -> None:
        if sys.platform == "win32":
            self.ctypes.windll.kernel32.SetThreadExecutionState(
                WindowsInhibitorSource.ES_CONTINUOUS | WindowsInhibitorSource.ES_SYSTEM_REQUIRED
            )

    def uninhibit(self) -> None:
        if sys.platform == "win32":
            self.ctypes.windll.kernel32.SetThreadExecutionState(WindowsInhibitorSource.ES_CONTINUOUS)


class DummyInhibitorSource(InhibitorSource):
    def inhibit(self) -> None:
        pass

    def uninhibit(self) -> None:
        pass


class Inhibitor:
    def __init__(self, source: InhibitorSource) -> None:
        self.source = source
        self.inhibited = False

    def inhibit(self) -> None:
        if not self.inhibited:
            self.source.inhibit()
            self.inhibited = True

    def uninhibit(self) -> None:
        if self.inhibited:
            self.source.uninhibit()
            self.inhibited = False

    def __enter__(self) -> None:
        self.inhibit()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.uninhibit()


def _get_inhibitor_source() -> InhibitorSource:
    if platform.system() == "Windows":
        try:
            return WindowsInhibitorSource()
        except Exception as e:
            logging.getLogger().warning(f"Unable to create WindowsInhibitor: {e}")

    return DummyInhibitorSource()


def get_inhibitor() -> Inhibitor:
    return Inhibitor(_get_inhibitor_source())
