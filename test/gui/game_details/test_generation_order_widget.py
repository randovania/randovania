from randovania.gui.game_details.generation_order_widget import GenerationOrderWidget
from randovania.gui.lib import model_lib
from randovania.layout.layout_description import LayoutDescription


def test_generation_order_widget(skip_qtbot, test_files_dir):
    layout = LayoutDescription.from_file(test_files_dir.joinpath("log_files", "prime2_seed_b.rdvgame"))

    widget = GenerationOrderWidget(None, layout, ["Me"])
    skip_qtbot.addWidget(widget)

    assert model_lib.get_texts(widget.proxy_model, max_rows=5) == [
        "Power Bomb at Temple Grounds/GFMC Compound/Pickup (Missile Launcher)",
        "Space Jump Boots at Temple Grounds/Hive Chamber B/Pickup (Missile)",
        "Violet Translator at Temple Grounds/Temple Assembly Site/Pickup (Missile)",
        "Amber Translator at Agon Wastes/Mining Station Access/Pickup (Energy Tank)",
        "Missile Launcher at Agon Wastes/Portal Access A/Pickup (Missile)",
    ]

    widget.filter_edit.setText("Space Jump")
    assert model_lib.get_texts(widget.proxy_model) == [
        "Space Jump Boots at Temple Grounds/Hive Chamber B/Pickup (Missile)",
        "Screw Attack at Dark Agon Wastes/Judgment Pit/Pickup (Space Jump Boots) with "
        "hint at Agon Wastes/Mining Plaza/Lore Scan",
    ]

    widget.filter_edit.setText("Something That Does Not Exist")
    assert model_lib.get_texts(widget.proxy_model) == []
