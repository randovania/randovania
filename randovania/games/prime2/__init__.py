from randovania.games.game import GameData, GameGenerator, GameGui, GameLayout, GamePresetDescriber
from randovania.games.prime2.generator.item_pool.pool_creator import echoes_specific_pool
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
from randovania.games.prime2.layout.echoes_cosmetic_patches import EchoesCosmeticPatches
from randovania.games.prime2.gui.preset_settings import _echoes_format_params, echoes_unexpected_items, prime2_preset_tabs, echoes_expected_items
from randovania.games.prime2.gui.dialog import EchoesCosmeticPatchesDialog

game_data: GameData = GameData(
    short_name = "Echoes",
    long_name = "Metroid Prime 2: Echoes",
    experimental = False,

    presets = [
        {
            "path": "presets/starter_preset.rdvpreset"
        },
        {
            "path": "presets/darkszero_deluxe.rdvpreset"
        },
        {
            "path": "presets/fewest_changes.rdvpreset"
        }
    ],

    layout = GameLayout(
        configuration = EchoesConfiguration,
        cosmetic_patches = EchoesCosmeticPatches
    ),

    gui = GameGui(
        tab_provider = prime2_preset_tabs,
        cosmetic_dialog = EchoesCosmeticPatchesDialog,
        preset_describer = GamePresetDescriber(
            expected_items = echoes_expected_items,
            unexpected_items = echoes_unexpected_items,
            format_params = _echoes_format_params
        )
    ),

    generator = GameGenerator(
        item_pool_creator = echoes_specific_pool
    )
)
