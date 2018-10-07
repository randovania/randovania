from randovania.resolver.layout_configuration import LayoutConfiguration


class GenerationFailure(Exception):
    def __init__(self, reason: str, configuration: LayoutConfiguration, seed_number: int):
        super().__init__(reason)
        self.configuration = configuration
        self.seed_number = seed_number
