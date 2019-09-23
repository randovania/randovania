import logging
import platform
from abc import abstractmethod


# Reference for this module:
# https://github.com/h3llrais3r/Deluge-PreventSuspendPlus/blob/master/preventsuspendplus/core.py
#
# Copyright (C) 2015 h3llrais3r <pooh_beer_1@hotmail.com>
# Copyright (C) 2009 Ian Martin <ianmartin@cantab.net>


class InhibitorSource:
    @abstractmethod
    def inhibit(self):
        """
        Inhibits sleep until `uninhibit` is called.
        """

    @abstractmethod
    def uninhibit(self):
        """
        Cancels a previous call to `inhibit`.
        """
        pass


class WindowsInhibitorSource(InhibitorSource):
    """https://msdn.microsoft.com/en-us/library/windows/desktop/aa373208(v=vs.85).aspx"""
    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001

    def __init__(self):
        import ctypes
        self.ctypes = ctypes

    def inhibit(self):
        self.ctypes.windll.kernel32.SetThreadExecutionState(
            WindowsInhibitorSource.ES_CONTINUOUS | WindowsInhibitorSource.ES_SYSTEM_REQUIRED)

    def uninhibit(self):
        self.ctypes.windll.kernel32.SetThreadExecutionState(WindowsInhibitorSource.ES_CONTINUOUS)


class DummyInhibitorSource(InhibitorSource):
    def inhibit(self):
        pass

    def uninhibit(self):
        pass


class Inhibitor:
    def __init__(self, source: InhibitorSource):
        self.source = source
        self.inhibited = False

    def inhibit(self):
        if not self.inhibited:
            self.source.inhibit()
            self.inhibited = True

    def uninhibit(self):
        if self.inhibited:
            self.source.uninhibit()
            self.inhibited = False

    def __enter__(self):
        self.inhibit()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.uninhibit()


def _get_inhibitor_source() -> InhibitorSource:
    if platform.system() == "Windows":
        try:
            return WindowsInhibitorSource()
        except Exception as e:
            logging.getLogger().warning("Unable to create WindowsInhibitor: {}".format(e))

    return DummyInhibitorSource()


def get_inhibitor() -> Inhibitor:
    return Inhibitor(_get_inhibitor_source())
