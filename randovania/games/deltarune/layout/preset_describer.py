from randovania.games.deltarune.layout.deltarune_configuration import DeltaruneConfiguration
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.layout.base.major_items_configuration import MajorItemsConfiguration
from randovania.layout.preset_describer import format_params_base


def format_params(configuration: BaseConfiguration) -> dict[str, list[str]]:
    assert isinstance(configuration, DeltaruneConfiguration)
    template_strings = format_params_base(configuration)
    return template_strings


def unexpected_items(configuration: MajorItemsConfiguration) -> set[str]:
    return set()
