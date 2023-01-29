from randovania.game_connection.connection_base import Inventory
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.world.world import World
from randovania.games.game import RandovaniaGame


class RemoteConnectorV2:
    @property
    def game_enum(self) -> RandovaniaGame:
        raise NotImplementedError()

    def description(self) -> str:
        raise NotImplementedError()

    async def current_game_status(self) -> World | None:
        """
        Fetches the world the player's currently at, or None if they're not in-game.
        """
        raise NotImplementedError()

    async def get_inventory(self) -> Inventory:
        """Fetches the inventory represented by the given game memory."""
        raise NotImplementedError()

    async def known_collected_locations(self) -> set[PickupIndex]:
        """Fetches pickup indices that have been collected.
        The list may return less than all collected locations, depending on implementation details.
        """
        raise NotImplementedError()

    async def receive_remote_pickups(self, remote_pickups: tuple[tuple[str, PickupEntry], ...]) -> None:
        """
        Determines if any of the remote_pickups needs to be written to executor.
        :param remote_pickups: Ordered list of pickups sent from other players, with the name of the player.
        """
        raise NotImplementedError()
