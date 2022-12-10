from randovania.layout.generator_parameters import GeneratorParameters
from randovania.layout.layout_description import LayoutDescription


class GenerationFailure(Exception):
    generator_params: GeneratorParameters
    source: Exception | None

    def __init__(self, reason: str, generator_params: GeneratorParameters, source: Exception | None):
        super().__init__(reason)
        self.generator_params = generator_params
        self.source = source

    def __reduce__(self):
        return GenerationFailure, (super().__str__(), self.generator_params, self.source)

    def __eq__(self, other):
        if not isinstance(other, GenerationFailure):
            return False

        if self.generator_params != other.generator_params:
            return False

        return super(Exception, other).__str__() == super().__str__()


class ImpossibleForSolver(GenerationFailure):
    def __init__(self, reason: str, generator_params: GeneratorParameters, layout: LayoutDescription):
        super().__init__(reason, generator_params, None)
        self.layout = layout

    def __reduce__(self):
        return ImpossibleForSolver, (super().__str__(), self.generator_params, self.layout)

    def __eq__(self, other):
        if not isinstance(other, ImpossibleForSolver):
            return False

        if self.layout != other.layout:
            return False

        return super().__eq__(other)
