from randovania.resolver.permalink import Permalink


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
