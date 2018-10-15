from typing import Optional, TypeVar, List

from PyQt5.QtWidgets import QTabWidget

T = TypeVar("T")


class TabService:
    windows: List[T] = []

    @property
    def _tab_widget(self) -> QTabWidget:
        raise NotImplementedError()

    def get_tab(self, tab_class: T) -> Optional[T]:
        tab_class: type = tab_class
        for window in self.windows:
            if isinstance(window, tab_class):
                return window

    def focus_tab(self, tab: T):
        index = self.windows.index(tab)
        self._tab_widget.setCurrentIndex(index)
