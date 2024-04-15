from __future__ import annotations

from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.gui.preset_settings.starting_area_tab import PresetStartingArea


class PresetCSStartingArea(PresetStartingArea):
    def create_quick_fill_buttons(self):
        super().create_quick_fill_buttons()

        self.starting_area_quick_fill_classic = self._quick_fill_button(
            "Classic", self._starting_location_on_select_classic
        )
        self.starting_area_quick_fill_save_point = self._quick_fill_button(
            "Save Point", self._starting_location_on_select_save_point
        )

    @property
    def quick_fill_description(self) -> str:
        return "<br/>".join(
            [
                super().quick_fill_description,
                (
                    "Classic: Mimiga Village - Start Point, Mimiga Village - Arthur's House, and Labyrinth - Camp; "
                    "the three starting locations available in the classic randomizer."
                ),
                "Save Points: All rooms with a Save Point.",
            ]
        )

    def _starting_location_on_select_classic(self):
        classics = [
            NodeIdentifier.create("Mimiga Village", "Start Point", "Room Spawn"),
            NodeIdentifier.create("Mimiga Village", "Arthur's House", "Room Spawn"),
            NodeIdentifier.create("Labyrinth", "Camp", "Room Spawn"),
        ]

        with self._editor as editor:
            editor.set_configuration_field(
                "starting_location", editor.configuration.starting_location.with_elements(classics, self.game_enum)
            )

    def _starting_location_on_select_save_point(self):
        region_list = self.game_description.region_list
        save_points = [node.identifier for node in region_list.iterate_nodes() if "Save Point" in node.name]

        # remove because save point is locked behind a boss fight
        save_points = [i for i in save_points if i.area != "Egg Observation Room?"]

        with self._editor as editor:
            editor.set_configuration_field(
                "starting_location", editor.configuration.starting_location.with_elements(save_points, self.game_enum)
            )
