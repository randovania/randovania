import pytest

from randovania.game.game_enum import RandovaniaGame
from randovania.game_description import default_database
from randovania.game_description.game_description import GameDescription
from randovania.games.prime_hunters.layout import HuntersConfiguration


@pytest.fixture
def prime_hunters_configuration(preset_manager) -> HuntersConfiguration:
    configuration = (
        preset_manager.default_preset_for_game(RandovaniaGame.METROID_PRIME_HUNTERS).get_preset().configuration
    )
    assert isinstance(configuration, HuntersConfiguration)
    return configuration


@pytest.fixture(scope="session")
def prime_hunters_game_description() -> GameDescription:
    return default_database.game_description_for(RandovaniaGame.METROID_PRIME_HUNTERS)
