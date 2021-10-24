from randovania.games.game import GameData, GameGenerator, GameGui, GameLayout, GamePresetDescriber

def _dread_gui():
    pass

game_data: GameData = GameData(
    short_name="Dread",
    long_name="Metroid Dread",
    experimental=True,

    presets=[
        {
            "path": "starter_preset.rdvpreset"
        }
    ],

    layout=GameLayout(
        # TODO
    ),

    gui=_dread_gui,

    generator=GameGenerator(
        # TODO
    )
)