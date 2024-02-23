from __future__ import annotations

from randovania.games import game
from randovania.games.samus_returns import layout
from randovania.games.samus_returns.layout.preset_describer import MSRPresetDescriber
from randovania.games.samus_returns.pickup_database import progressive_items


def _options():
    from randovania.games.samus_returns.exporter.options import MSRPerGameOptions

    return MSRPerGameOptions


def _gui() -> game.GameGui:
    from randovania.games.samus_returns import gui

    return game.GameGui(
        game_tab=gui.MSRGameTabWidget,
        tab_provider=gui.msr_preset_tabs,
        cosmetic_dialog=gui.MSRCosmeticPatchesDialog,
        export_dialog=gui.MSRGameExportDialog,
        progressive_item_gui_tuples=progressive_items.tuples(),
        spoiler_visualizer=(gui.MSRHintDetailsTab,),
    )


def _patch_data_factory():
    from randovania.games.samus_returns.exporter.patch_data_factory import MSRPatchDataFactory

    return MSRPatchDataFactory


def _exporter():
    from randovania.games.samus_returns.exporter.game_exporter import MSRGameExporter

    return MSRGameExporter()


def _generator() -> game.GameGenerator:
    from randovania.games.samus_returns import generator
    from randovania.games.samus_returns.generator.bootstrap import MSRBootstrap
    from randovania.games.samus_returns.generator.hint_distributor import MSRHintDistributor

    return game.GameGenerator(
        pickup_pool_creator=generator.pool_creator,
        bootstrap=MSRBootstrap(),
        base_patches_factory=generator.MSRBasePatchesFactory(),
        hint_distributor=MSRHintDistributor(),
    )


game_data: game.GameData = game.GameData(
    short_name="MSR",
    long_name="Metroid: Samus Returns",
    development_state=game.DevelopmentState.EXPERIMENTAL,
    presets=[
        {"path": "starter_preset.rdvpreset"},
    ],
    faq=[
        (
            "What are the icons on the bottom of the HUD?",
            "These elements are present in the vanilla game, but they have been slightly revamped. "
            "From left to right, the HUD shows the amount of DNA you currently have, the amount of DNA "
            "collected per area out of how many in that area, "
            "and the amount of Metroids that are still alive. ",
        ),
        (
            "Do I still need to beat Metroids and collect DNA to progress areas?",
            "No you do not. All the hazardous liquid has already been drained. "
            "Metroids can now drop any item in the game as well as DNA.",
        ),
        (
            "Do I have to beat the Queen Metroid to beat the game?",
            "In order to beat the game, you must collect the required Metroid DNA, "
            "find the Baby, and defeat Proteus Ridley.",
        ),
        (
            "How much Metroid DNA is required to beat the game?",
            "The amount of required DNA is configurable from 0 to 39 DNA. "
            "The HUD shows how much DNA is located in each area, just like in the vanilla game.",
        ),
        (
            "How do I access Proteus Ridley?",
            "In the vanilla game, the Surface area where Proteus Ridley resides "
            "is a separate map from the starting Surface. These are normally not connected. "
            "This has been changed to warp the player to the other Surface map by passing the "
            "Baby blocks in the Landing Site. Once enough DNA is collected to access Ridley, "
            "you can no longer warp from Surface West to Surface East.",
        ),
        (
            "Are there any hints?",
            "All Chozo Seals have been repurposed to provide a hint to "
            "an item somewhere in the world. The region the item is located "
            "will be specified."
            "\n\n"
            "New seals have been added in all areas except Surface which hint at the location "
            "of DNA. See the `Hints` tab for more information.",
        ),
        (
            "Why is this pickup not animating?",
            "While progressive pickups update to have the correct model, "
            "due to limitations these models are not animated.",
        ),
        (
            "I collected Beam Burst, but I cannot use it.",
            "Beam Burst requires at least the Wave Beam to function.",
        ),
        (
            "What are Reserve Tanks?",
            "Reserve Tanks are items that restore a certain ammo type when depleted. "
            "In vanilla, these tanks can be unlocked by using certain amiibo, "
            "but in the randomizer, this has been changed to make them be actual pickups."
            "\n\n"
            "By default, the Energy Reserve Tank restores 299 Energy, the Aeion Reserve Tank "
            "restores 500 Aeion, and the Missile Reserve Tank restores 30 Missiles or "
            "10 Super Missiles. Note that when the Missile Reserve Tank is depeleted, "
            "it only restores whatever ammo was last used, and not both.",
        ),
        (
            "I collected the Missile Reserve Tank, but I cannot see nor use it.",
            "Due to limitations, the Missile Reserve Tank will remain deactivated "
            "until the Missile Launcher is in your inventory. This prevents a bug where "
            "the reserve will activate even if you have no usable Missiles.",
        ),
    ],
    layout=game.GameLayout(
        configuration=layout.MSRConfiguration,
        cosmetic_patches=layout.MSRCosmeticPatches,
        preset_describer=MSRPresetDescriber(),
    ),
    options=_options,
    gui=_gui,
    generator=_generator,
    patch_data_factory=_patch_data_factory,
    exporter=_exporter,
    multiple_start_nodes_per_area=True,
)
