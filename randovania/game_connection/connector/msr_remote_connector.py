from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_connection.connector.mercury_remote_connector import MercuryConnector
from randovania.games.game import RandovaniaGame
from randovania.games.samus_returns.exporter.patch_data_factory import get_resources_for_details

if TYPE_CHECKING:
    from randovania.game_connection.executor.msr_executor import MSRExecutor
    from randovania.game_description.pickup.pickup_entry import ConditionalResources, PickupEntry


class MSRRemoteConnector(MercuryConnector):
    _game_enum: RandovaniaGame = RandovaniaGame.METROID_SAMUS_RETURNS

    def __init__(self, executor: MSRExecutor):
        super().__init__(executor, self._game_enum)

    def description(self) -> str:
        return self.game_enum.long_name

    def get_resources_for_details(
        self, pickup: PickupEntry, conditional_resources: list[ConditionalResources], other_player: bool
    ) -> list:
        return get_resources_for_details(pickup, conditional_resources, other_player)

    async def game_specific_execute(self, item_name: str, items_list: list, provider_name: str) -> None:
        remote_pickups = self.remote_pickups
        num_pickups = self.received_pickups
        message = self.format_received_item(item_name, provider_name)

        self.logger.info("%d permanent pickups, magic %d. Next pickup: %s", len(remote_pickups), num_pickups, message)

        from open_samus_returns_rando.multiworld_integration import get_lua_for_item

        lua_code = get_lua_for_item(items_list)
        execute_string = f"RL.ReceivePickup({repr(message)},'{lua_code}'," f"{num_pickups},{self.inventory_index})"
        await self.executor.run_lua_code(execute_string)

    async def display_arbitrary_message(self, message: str) -> None:
        escaped_message = message.replace("\\", "\\\\").replace("'", "\\'")
        execute_string = f"Game.AddSF(0, 'Scenario.QueueAsyncPopup', 'si', '{escaped_message}', 10.0)"
        await self.executor.run_lua_code(execute_string)
