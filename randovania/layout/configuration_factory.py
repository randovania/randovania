import json
from typing import Dict

from randovania import get_data_path
from randovania.game_description.resources.translator_gate import TranslatorGate
from randovania.games.game import RandovaniaGame
from randovania.games.prime2.layout.translator_configuration import LayoutTranslatorRequirement


def _raw_translator_configurations(data: dict) -> Dict[TranslatorGate, LayoutTranslatorRequirement]:
    return {
        TranslatorGate(int(key)): LayoutTranslatorRequirement(item)
        for key, item in data["translator_requirement"].items()
    }


def get_vanilla_actual_translator_configurations() -> Dict[TranslatorGate, LayoutTranslatorRequirement]:
    with RandovaniaGame.METROID_PRIME_ECHOES.data_path.joinpath("item_database", "default_state", 
                                                                "translator_vanilla_actual.json").open() as open_file:
        data = json.load(open_file)

    return _raw_translator_configurations(data)


def get_vanilla_colors_translator_configurations() -> Dict[TranslatorGate, LayoutTranslatorRequirement]:
    with RandovaniaGame.METROID_PRIME_ECHOES.data_path.joinpath("item_database", "default_state", 
                                                                "translator_vanilla_colors.json").open() as open_file:
        data = json.load(open_file)

    return _raw_translator_configurations(data)
