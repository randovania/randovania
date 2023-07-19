from PySide6 import QtWidgets

from randovania.gui.game_details.pickup_details_tab import PickupDetailsTab
from randovania.gui.lib import signal_handling
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.layout_description import LayoutDescription


def test_search_pickup(skip_qtbot, test_files_dir):
    layout = LayoutDescription.from_file(
        test_files_dir.joinpath("log_files", "dread", "dread_prime1_multiworld.rdvgame")
    )

    root = QtWidgets.QWidget()
    skip_qtbot.addWidget(root)

    players = PlayersConfiguration(
        0,
        {0: "You", 1: "They"}
    )

    tab = PickupDetailsTab(root, layout.all_patches[0].game.game)
    tab.update_content(layout.all_patches[0].configuration, layout.all_patches, players)

    def get_texts(model):
        return [
            [
                model.data(model.index(row, i))
                for i in range(4)
            ]
            for row in range(model.rowCount())
        ]

    assert tab.search_pickup_combo.currentIndex() == 0
    assert get_texts(tab.search_pickup_proxy) == []

    signal_handling.set_combo_with_value(tab.search_pickup_combo, "Progressive Beam")
    assert get_texts(tab.search_pickup_proxy) == [
        ['You', 'Artaria', 'Speed Hallway', 'Pickup (Energy Part)'],
        ['You', 'Cataris', 'Central Unit Access', 'Pickup (Morph Ball)'],
        ['They', 'Tallon Overworld', 'Frigate Crash Site', 'Pickup (Missile Expansion)']
    ]

    signal_handling.set_combo_with_value(tab.search_pickup_combo, "Screw Attack")
    assert get_texts(tab.search_pickup_proxy) == [
        ['They', 'Magmoor Caverns', 'Storage Cavern', 'Pickup (Missile)'],
    ]
