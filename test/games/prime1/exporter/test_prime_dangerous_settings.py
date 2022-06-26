from randovania.layout.layout_description import LayoutDescription


def test_dangerous_settings(test_files_dir, rdvgame_filename="prime1_crazy_seed.rdvgame"):
    rdvgame = test_files_dir.joinpath("log_files", rdvgame_filename)
    layout_description = LayoutDescription.from_file(rdvgame)
    preset = layout_description.get_preset(0)

    assert preset.dangerous_settings() == [
        'One-way anywhere elevators',
        'Shuffled Item Position',
        'Room Randomizer',
        'Extra Superheated Rooms',
        'Submerged Rooms',
        'Dangerous Gravity Suit Logic',
    ]
