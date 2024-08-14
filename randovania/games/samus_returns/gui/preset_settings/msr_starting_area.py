from randovania.gui.preset_settings.starting_area_tab import PresetMetroidStartingArea


class PresetMSRStartingArea(PresetMetroidStartingArea):
    @classmethod
    def starts_new_header(cls) -> bool:
        return True
