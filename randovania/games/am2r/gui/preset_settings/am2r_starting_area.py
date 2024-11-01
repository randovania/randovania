from randovania.gui.preset_settings.starting_area_tab import PresetMetroidStartingArea


class PresetAM2RStartingArea(PresetMetroidStartingArea):
    @classmethod
    def header_name(cls) -> str | None:
        return cls.GAME_MODIFICATIONS_HEADER
