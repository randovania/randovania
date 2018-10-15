from randovania.resolver.layout_configuration import LayoutConfiguration


class GenerationFailure(Exception):
    def __init__(self, reason: str, configuration: LayoutConfiguration, seed_number: int):
        super().__init__(reason)
        self.configuration = configuration
        self.seed_number = seed_number

    def __str__(self) -> str:
        return "Generation Failure: {} received for {} with config {}".format(
            super().__str__(),
            self.seed_number,
            self.configuration.as_str
        )
