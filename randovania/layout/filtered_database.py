from randovania.game_description import derived_nodes, default_database
from randovania.game_description.game_description import GameDescription
from randovania.layout.base.base_configuration import BaseConfiguration


def game_description_for_layout(configuration: BaseConfiguration) -> GameDescription:
    game = derived_nodes.remove_inactive_layers(
        default_database.game_description_for(configuration.game),
        configuration.active_layers(),
    )

    return game
