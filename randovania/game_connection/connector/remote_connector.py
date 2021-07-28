import dataclasses
from typing import List, Tuple, Set, Optional

from randovania.game_connection.connection_base import Inventory
from randovania.game_connection.executor.memory_operation import MemoryOperationExecutor, MemoryOperation
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.world.world import World
from randovania.games.game import RandovaniaGame


@dataclasses.dataclass(frozen=True)
class RemotePatch:
    """Format of the contents depends exclusively on each implementation."""
    memory_operations: List[MemoryOperation]


class RemoteConnector:
    @property
    def game_enum(self) -> RandovaniaGame:
        raise NotImplementedError()

    async def is_this_version(self, executor: MemoryOperationExecutor) -> bool:
        """Returns True if the accessible memory matches the version of this connector."""
        raise NotImplementedError()

    async def current_game_status(self, executor: MemoryOperationExecutor) -> Tuple[bool, Optional[World]]:
        """
        Fetches the world the player's currently at, or None if they're not in-game.
        :param executor:
        :return: bool indicating if there's a pending `execute_remote_patches` operation.
        """
        raise NotImplementedError()

    async def get_inventory(self, executor: MemoryOperationExecutor) -> Inventory:
        """Fetches the inventory represented by the given game memory."""
        raise NotImplementedError()

    async def known_collected_locations(self, executor: MemoryOperationExecutor,
                                        ) -> Tuple[Set[PickupIndex], List[RemotePatch]]:
        """Fetches pickup indices that have been collected.
        The list may return less than all collected locations, depending on implementation details.
        This function also returns a list of remote patches that must be performed via `execute_remote_patches`.
        """
        raise NotImplementedError()

    async def find_missing_remote_pickups(self, executor: MemoryOperationExecutor, inventory: Inventory,
                                          remote_pickups: Tuple[Tuple[str, PickupEntry], ...],
                                          in_cooldown: bool,
                                          ) -> Tuple[List[RemotePatch], bool]:
        """
        Determines if any of the remote_pickups needs to be written to executor.
        :param executor:
        :param inventory: The player's inventory, as given by `get_inventory`.
        :param remote_pickups: Ordered list of pickups sent from other players, with the name of the player.
        :param in_cooldown: If sending new pickups is on cooldown.
        :return: List of patches to give one missing pickup. A bool indicating that a message will be displayed.
        """
        raise NotImplementedError()

    async def execute_remote_patches(self, executor: MemoryOperationExecutor, patches: List[RemotePatch]) -> None:
        """
        Executes a given set of patches on the given memory operator. Should only be called if the bool returned by
        `current_game_status` is False, but validation of this fact is implementation-dependant.
        :param executor:
        :param patches: List of patches to execute
        :return:
        """
        raise NotImplementedError()
