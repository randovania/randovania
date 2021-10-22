from randovania.games.game import GameData, GameGenerator, GameGui, GameLayout, GamePresetDescriber
from randovania.games.prime1.layout.prime_configuration import PrimeConfiguration
from randovania.games.prime1.layout.prime_cosmetic_patches import PrimeCosmeticPatches
from randovania.games.prime1.gui.preset_settings import prime1_preset_tabs, prime_expected_items, prime_unexpected_items, _prime_format_params
from randovania.games.prime1.gui.dialog.prime_cosmetic_patches_dialog import PrimeCosmeticPatchesDialog
from randovania.games.prime1.generator.item_pool.pool_creator import prime1_specific_pool

game_data: GameData = GameData(
    short_name = "Prime",
    long_name = "Metroid Prime",
    experimental = False,

    presets = [
        {
            "path": "starter_preset.rdvpreset"
        },
        {
            "path": "fewest_changes.rdvpreset"
        }
    ],

    layout = GameLayout(
        configuration = PrimeConfiguration,
        cosmetic_patches = PrimeCosmeticPatches
    ),

    gui = GameGui(
        tab_provider = prime1_preset_tabs,
        cosmetic_dialog = PrimeCosmeticPatchesDialog,
        preset_describer = GamePresetDescriber(
            expected_items = prime_expected_items,
            unexpected_items = prime_unexpected_items,
            format_params = _prime_format_params
        )
    ),

    generator = GameGenerator(
        item_pool_creator = prime1_specific_pool
    )
)
