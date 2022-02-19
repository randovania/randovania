from typing import Optional, NamedTuple

from randovania.exporter.hints.determiner import Determiner
from randovania.exporter.hints.pickup_hint import PickupHint
from randovania.game_description.hint import Hint
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.game import RandovaniaGame


class PickupLocation(NamedTuple):
    game: RandovaniaGame
    location: PickupIndex


class HintNamer:
    def format_joke(self, joke: str, with_color: bool) -> str:
        raise NotImplementedError()

    def format_player(self, name: str, with_color: bool) -> str:
        raise NotImplementedError()

    def format_world(self, location: PickupLocation, with_color: bool) -> str:
        raise NotImplementedError()

    def format_area(self, location: PickupLocation, with_world: bool, with_color: bool) -> str:
        raise NotImplementedError()

    def format_location_hint(self, game: RandovaniaGame, pick_hint: PickupHint, hint: Hint, with_color: bool) -> str:
        raise NotImplementedError()

    def format_resource_is_starting(self, resource: ItemResourceInfo, with_color: bool) -> str:
        """Used when for when an item has a guaranteed hint, but is a starting item."""
        raise NotImplementedError()

    def format_guaranteed_resource(self, resource: ItemResourceInfo, player_name: Optional[str],
                                   location: PickupLocation, hide_area: bool, with_color: bool) -> str:
        """Used when for indicating where a given resource can be found."""
        raise NotImplementedError()

    # Echoes only
    def format_temple_name(self, temple_name: str, with_color: bool) -> str:
        raise NotImplementedError()

    # Helper
    def format_location(self, location: PickupLocation, with_world: bool, with_area: bool, with_color: bool) -> str:
        if with_area:
            return self.format_area(location, with_world=with_world, with_color=with_color)
        elif with_world:
            return self.format_world(location, with_color=with_color)
        else:
            raise ValueError("Both with_world and with_area not not set.")
