from randovania.games.game import GameData, GameGenerator, GameGui, GameLayout, GamePresetDescriber
from randovania.games.prime2.generator.base_patches_factory import EchoesBasePatchesFactory
from randovania.games.prime2.generator.bootstrap import EchoesBootstrap
from randovania.games.prime2.generator.item_pool.pool_creator import echoes_specific_pool
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
from randovania.games.prime2.layout.echoes_cosmetic_patches import EchoesCosmeticPatches
from randovania.games.prime2.layout.preset_describer import echoes_format_params, echoes_unexpected_items, \
    echoes_expected_items
from randovania.games.prime2.patcher.claris_patcher import ClarisPatcher


def _echoes_gui():
    from randovania.games.prime2.gui.preset_settings import prime2_preset_tabs
    from randovania.games.prime2.gui.dialog.echoes_cosmetic_patches_dialog import EchoesCosmeticPatchesDialog
    from randovania.gui.game_details.teleporter_details_tab import TeleporterDetailsTab
    from randovania.games.prime2.gui.translator_gate_details_tab import TranslatorGateDetailsTab
    from randovania.games.prime2.gui.hint_details_tab import HintDetailsTab
    from randovania.games.prime2.item_database import prime2_progressive_items

    return GameGui(
        tab_provider=prime2_preset_tabs,
        cosmetic_dialog=EchoesCosmeticPatchesDialog,
        input_file_text=("an ISO file", "the Nintendo Gamecube", "Gamecube ISO"),
        progressive_item_gui_tuples=prime2_progressive_items.gui_tuples(),
        spoiler_visualizer=(TeleporterDetailsTab, TranslatorGateDetailsTab, HintDetailsTab),
    )


game_data: GameData = GameData(
    short_name="Echoes",
    long_name="Metroid Prime 2: Echoes",
    experimental=False,

    presets=[
        {
            "path": "starter_preset.rdvpreset"
        },
        {
            "path": "darkszero_deluxe.rdvpreset"
        },
        {
            "path": "fewest_changes.rdvpreset"
        }
    ],

    faq={
    }.items(),

    layout=GameLayout(
        configuration=EchoesConfiguration,
        cosmetic_patches=EchoesCosmeticPatches,
        preset_describer=GamePresetDescriber(
            expected_items=echoes_expected_items,
            unexpected_items=echoes_unexpected_items,
            format_params=echoes_format_params
        )
    ),

    gui=_echoes_gui,

    generator=GameGenerator(
        item_pool_creator=echoes_specific_pool,
        bootstrap=EchoesBootstrap(),
        base_patches_factory=EchoesBasePatchesFactory()
    ),

    patcher=ClarisPatcher()
)
