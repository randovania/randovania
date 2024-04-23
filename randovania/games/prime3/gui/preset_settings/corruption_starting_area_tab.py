from __future__ import annotations

from randovania.gui.preset_settings.starting_area_tab import PresetMetroidStartingArea, PresetStartingArea


class PresetCorruptionStartingArea(PresetMetroidStartingArea):
    def create_quick_fill_buttons(self) -> None:
        super().create_quick_fill_buttons()

        self.starting_area_quick_fill_ships = self._quick_fill_button(
            "Landing Sites", self._starting_location_on_select_ships
        )

    @property
    def quick_fill_description(self) -> str:
        return "<br/>".join(
            [
                super().quick_fill_description,
                (
                    "Landing Sites: All areas with Ship Landing Sites, with the exception of G.F.S Olympus, "
                    "the Planets' Seeds and Phaaze."
                ),
            ]
        )

    def _starting_location_on_select_ships(self, area: PresetStartingArea) -> None:
        region_list = self.game_description.region_list
        ships = [node.identifier for node in region_list.iterate_nodes() if "Samus Ship" in node.name]

        # Remove seeds and phaaze
        ships = [i for i in ships if "- Seed" not in i.region and i.region != "Phaaze"]

        with self._editor as editor:
            editor.set_configuration_field(
                "starting_location", editor.configuration.starting_location.with_elements(ships, self.game_enum)
            )
