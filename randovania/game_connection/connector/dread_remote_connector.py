from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_connection.connector.mercury_remote_connector import MercuryConnector
from randovania.games.dread.exporter.patch_data_factory import get_resources_for_details
from randovania.games.game import RandovaniaGame

if TYPE_CHECKING:
    from randovania.game_connection.executor.dread_executor import DreadExecutor
    from randovania.game_description.pickup.pickup_entry import ConditionalResources, PickupEntry


class DreadRemoteConnector(MercuryConnector):
    _game_enum: RandovaniaGame = RandovaniaGame.METROID_DREAD

    def __init__(self, executor: DreadExecutor):
        super().__init__(executor, self._game_enum)

    def description(self) -> str:
        return f"{self.game_enum.long_name}: {self.executor.version}"

    def get_resources_for_details(
        self, pickup: PickupEntry, conditional_resources: list[ConditionalResources], other_player: bool
    ) -> list:
        return get_resources_for_details(pickup, conditional_resources, other_player)

    async def game_specific_execute(self, item_name: str, items_list: list, provider_name: str) -> None:
        remote_pickups = self.remote_pickups
        num_pickups = self.received_pickups

        from open_dread_rando.misc_patches.lua_util import lua_convert  # type: ignore

        progression_as_lua = lua_convert(items_list, True)
        message = self.format_received_item(item_name, provider_name)

        self.logger.info("%d permanent pickups, magic %d. Next pickup: %s", len(remote_pickups), num_pickups, message)

        main_item_id = items_list[0][0]["item_id"]
        from open_dread_rando.pickups.lua_editor import LuaEditor  # type: ignore

        parent = LuaEditor.get_parent_for(None, main_item_id)

        execute_string = (
            f"RL.ReceivePickup({repr(message)},{parent},{repr(progression_as_lua)},"
            f"{num_pickups},{self.inventory_index})"
        )

        await self.executor.run_lua_code(execute_string)

    async def display_arbitrary_message(self, message: str) -> None:
        escaped_message = message.replace("\\", "\\\\").replace("'", "\\'")
        execute_string = f"Game.AddSF(0, 'Scenario.QueueAsyncPopup', 'si', '{escaped_message}', 10.0)"
        await self.executor.run_lua_code(execute_string)
