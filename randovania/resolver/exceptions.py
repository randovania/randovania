from randovania.layout.permalink import Permalink


class GenerationFailure(Exception):
    permalink: Permalink
    source: Exception

    def __init__(self, reason: str, permalink: Permalink, source: Exception):
        super().__init__(reason)
        self.permalink = permalink
        self.source = source

    def __reduce__(self):
        return GenerationFailure, (super().__str__(), self.permalink, self.source)

    def __eq__(self, other):
        if not isinstance(other, GenerationFailure):
            return False

        if self.permalink != other.permalink:
            return False

        return super(Exception, other).__str__() == super().__str__()


class ImpossibleForSolver(Exception):
    pass


class InvalidConfiguration(Exception):
    pass
