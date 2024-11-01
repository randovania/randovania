from randovania.gui.preset_settings.starting_area_tab import PresetMetroidStartingArea


class PresetMSRStartingArea(PresetMetroidStartingArea):
    @classmethod
    def header_name(cls) -> str | None:
        return cls.GAME_MODIFICATIONS_HEADER
