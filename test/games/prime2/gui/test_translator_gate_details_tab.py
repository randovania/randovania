from __future__ import annotations

from PySide6 import QtWidgets

from randovania.game.game_enum import RandovaniaGame
from randovania.games.prime2.gui import TranslatorGateDetailsTab
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.layout_description import LayoutDescription


def test_update_content(skip_qtbot, test_files_dir):
    # Setup
    parent = QtWidgets.QMainWindow()
    skip_qtbot.add_widget(parent)

    description = LayoutDescription.from_file(test_files_dir.joinpath("log_files", "seed_a.rdvgame"))
    tab = TranslatorGateDetailsTab(parent, RandovaniaGame.METROID_PRIME_ECHOES)

    # Run
    tab.update_content(
        description.get_preset(0).configuration,
        description.all_patches,
        PlayersConfiguration(0, {0: "You"}),
    )

    # Assert
    counts = {}
    for i in range(tab.tree_widget.topLevelItemCount()):
        item = tab.tree_widget.topLevelItem(i)
        assert item is not None
        counts[item.text(0)] = item.childCount()

    assert counts == {
        "Agon Wastes": 2,
        "Great Temple": 3,
        "Sanctuary Fortress": 2,
        "Temple Grounds": 7,
        "Torvus Bog": 3,
    }
