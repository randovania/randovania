class Determiner:
    s: str
    supports_title: bool

    def __init__(self, s, supports_title: bool = True):
        self.s = s
        self.supports_title = supports_title

    def __format__(self, format_spec):
        return self.s.__format__(format_spec)

    @property
    def title(self):
        if self.supports_title:
            return self.s.title()
        else:
            return self.s

    @property
    def capitalize(self):
        return self.s.capitalize()

    @property
    def capitalize_title(self):
        return self.title.capitalize()

    @property
    def upper(self):
        return self.s.upper()

    @property
    def upper_title(self):
        return self.title.upper()
