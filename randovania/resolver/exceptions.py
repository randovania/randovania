from randovania.layout.generator_parameters import GeneratorParameters


class GenerationFailure(Exception):
    generator_params: GeneratorParameters
    source: Exception

    def __init__(self, reason: str, generator_params: GeneratorParameters, source: Exception):
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


class ImpossibleForSolver(Exception):
    pass


class InvalidConfiguration(Exception):
    pass
