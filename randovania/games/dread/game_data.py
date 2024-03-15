from __future__ import annotations

from randovania.games import game
from randovania.games.dread.layout.dread_configuration import DreadConfiguration
from randovania.games.dread.layout.dread_cosmetic_patches import DreadCosmeticPatches
from randovania.games.dread.layout.preset_describer import DreadPresetDescriber


def _options():
    from randovania.games.dread.exporter.options import DreadPerGameOptions

    return DreadPerGameOptions


def _gui() -> game.GameGui:
    from randovania.games.dread import gui
    from randovania.games.dread.pickup_database import progressive_items

    return game.GameGui(
        tab_provider=gui.dread_preset_tabs,
        cosmetic_dialog=gui.DreadCosmeticPatchesDialog,
        export_dialog=gui.DreadGameExportDialog,
        progressive_item_gui_tuples=progressive_items.tuples(),
        spoiler_visualizer=(gui.DreadHintDetailsTab, gui.DreadTeleporterDetailsTab),
        game_tab=gui.DreadGameTabWidget,
    )


def _patch_data_factory():
    from randovania.games.dread.exporter.patch_data_factory import DreadPatchDataFactory

    return DreadPatchDataFactory


def _exporter():
    from randovania.games.dread.exporter.game_exporter import DreadGameExporter

    return DreadGameExporter()


def _generator() -> game.GameGenerator:
    from randovania.games.dread.generator.base_patches_factory import DreadBasePatchesFactory
    from randovania.games.dread.generator.bootstrap import DreadBootstrap
    from randovania.games.dread.generator.hint_distributor import DreadHintDistributor
    from randovania.games.dread.generator.pool_creator import pool_creator

    return game.GameGenerator(
        pickup_pool_creator=pool_creator,
        base_patches_factory=DreadBasePatchesFactory(),
        bootstrap=DreadBootstrap(),
        hint_distributor=DreadHintDistributor(),
    )


game_data: game.GameData = game.GameData(
    short_name="Dread",
    long_name="Metroid Dread",
    development_state=game.DevelopmentState.STABLE,
    presets=[
        {"path": "starter_preset.rdvpreset"},
        {"path": "april_fools_2023.rdvpreset"},
    ],
    faq=[
        (
            "Why does this missile door not open after I shoot a missile at it?",
            "Shoot another missile at the door. In the process of making certain missile doors possible to open from "
            "both sides, this issue shows up.",
        ),
        (
            "Using an Energy Recharge Station heals me to 299, but my energy maximum is 249. Which one is correct?",
            "The 299 is a display error. You can always see the correct value in the inventory screen.",
        ),
        (
            "Why is this pickup not animating, or displaying visual effects?",
            "While progressive pickups update to have the correct model, "
            "due to limitations these models are not animated or have any additional effects.",
        ),
        (
            "Can I play on Yuzu?",
            "Yuzu is not officially supported so you're on your own.\n\n"
            "It has been reported to work fine, but there are planned features that are known to be incompatible.",
        ),
        (
            "Can I use other mods?",
            "Depending on which files the other mods change, it can go from simple to impossible.\n\n"
            "* If a Lua file is modified, very likely it's not compatible.\n"
            "* If a PKG file is modified, it'll have to be combined with the one from Randovania.\n"
            "* Other mods likely work fine.\n\n"
            "When reporting issues, your first step is always to reproduce the issue without mods, "
            "**no matter how simple** the mod is.",
        ),
        (
            "I picked up the Speed Booster / Phantom Cloak / Storm Missile but can't use them!",
            "Press ZL + ZR + D-Pad Up to fix the issue."
            " Check the entry 'Crashing after suit upgrade' in 'Known Crashes' tab"
            " for important rules of when to use this button combination.\n\n"
            "You can also save and reload your game.",
        ),
        (
            "I entered the arena for Golzuna/Experiment Z-57 but it isn't there!",
            "Golzuna and Experiment Z-57 will not appear unless the X have been released from Elun.\n\n"
            "To activate the fight against Experiment Z-57, you must use the Morph Ball Launcher to enter the arena.",
        ),
        (
            "I opened the Wide Beam door in Dairon's Teleport to Cataris, but it won't let me through!",
            "Unlocking this door before turning on the power will render it unopenable.\n\n"
            "To fix this, simply save and reload the game.",
        ),
        (
            "I received a Beam/Missile upgrade from an E.M.M.I., and now my arm cannon doesn't work!",
            "Reload from checkpoint immediately to fix the issue. "
            "Your checkpoint was saved after killing the E.M.M.I., so you will not lose progress.",
        ),
        (
            "Why are items, hints, and the seed hash not displaying properly in my game?",
            "Currently, English is the only officially supported language.\n\n"
            "You must set your language to English to see all the text the randomizer changes.",
        ),
    ],
    web_info=game.GameWebInfo(
        what_can_randomize=[
            "All items",
            "Elevator and shuttle destinations",
            "Starting locations",
            "Door locks",
            "A new goal has been added (DNA Hunt)",
        ],
        need_to_play=[
            "A modded Switch with Atmosphere and SimpleModManager; or Ryujinx",
            "A dumped RomFS of your original game. Either version 1.0.0 or 2.1.0",
        ],
    ),
    layout=game.GameLayout(
        configuration=DreadConfiguration, cosmetic_patches=DreadCosmeticPatches, preset_describer=DreadPresetDescriber()
    ),
    options=_options,
    gui=_gui,
    generator=_generator,
    patch_data_factory=_patch_data_factory,
    exporter=_exporter,
    multiple_start_nodes_per_area=True,
    defaults_available_in_game_sessions=True,
)
