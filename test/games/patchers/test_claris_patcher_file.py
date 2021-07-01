from randovania.games.patchers import claris_patcher_file


def test_create_starting_popup_empty(default_echoes_preset, echoes_resource_database):
    starting_items = {}

    # Run
    result = claris_patcher_file._create_starting_popup(default_echoes_preset.configuration,
                                                        echoes_resource_database,
                                                        starting_items)

    # Assert
    assert result == []


def test_create_starting_popup_items(default_echoes_preset, echoes_resource_database):
    starting_items = {
        echoes_resource_database.get_item_by_name("Missile"): 15,
        echoes_resource_database.energy_tank: 3,
        echoes_resource_database.get_item_by_name("Dark Beam"): 1,
        echoes_resource_database.get_item_by_name("Screw Attack"): 1,
    }

    # Run
    result = claris_patcher_file._create_starting_popup(default_echoes_preset.configuration,
                                                        echoes_resource_database,
                                                        starting_items)

    # Assert
    assert result == [
        'Extra starting items:',
        'Dark Beam, 3 Energy Tank, 15 Missiles, Screw Attack'
    ]
