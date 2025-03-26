import pytest

from randovania.game.game_enum import RandovaniaGame
from randovania.games.prime_hunters.layout import HuntersConfiguration


@pytest.fixture
def prime_hunters_configuration(preset_manager) -> HuntersConfiguration:
    configuration = (
        preset_manager.default_preset_for_game(RandovaniaGame.METROID_PRIME_HUNTERS).get_preset().configuration
    )
    assert isinstance(configuration, HuntersConfiguration)
    return configuration
