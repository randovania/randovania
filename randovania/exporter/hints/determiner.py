from __future__ import annotations


class Determiner:
    s: str
    supports_title: bool

    def __init__(self, s: str, supports_title: bool = True) -> None:
        self.s = s
        self.supports_title = supports_title

    def __format__(self, format_spec: str) -> str:
        return self.s.__format__(format_spec)

    @property
    def title(self) -> str:
        if self.supports_title:
            return self.s.title()
        else:
            return self.s

    @property
    def capitalize(self) -> str:
        return self.s.capitalize()

    @property
    def capitalize_title(self) -> str:
        return self.title.capitalize()

    @property
    def upper(self) -> str:
        return self.s.upper()

    @property
    def upper_title(self) -> str:
        return self.title.upper()
