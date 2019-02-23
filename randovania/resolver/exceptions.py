from randovania.layout.permalink import Permalink


class GenerationFailure(Exception):
    permalink: Permalink

    def __init__(self, reason: str, permalink: Permalink):
        super().__init__(reason)
        self.permalink = permalink

    def __str__(self) -> str:
        return "{} occurred for permalink {}".format(
            super().__str__(),
            self.permalink.as_str
        )

    def __reduce__(self):
        return GenerationFailure, (super().__str__(), self.permalink)

    def __eq__(self, other):
        if not isinstance(other, GenerationFailure):
            return False

        if self.permalink != other.permalink:
            return False

        return super(Exception, other).__str__() == super().__str__()


class InvalidConfiguration(Exception):
    pass
