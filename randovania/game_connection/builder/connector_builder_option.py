import dataclasses

from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.game_connection.builder.connector_builder import ConnectorBuilder
from randovania.game_connection.builder.debug_connector_builder import DebugConnectorBuilder
from randovania.game_connection.builder.dolphin_connector_builder import DolphinConnectorBuilder
from randovania.game_connection.builder.nintendont_connector_builder import NintendontConnectorBuilder
from randovania.game_connection.builder.dread_connector_builder import DreadConnectorBuilder
from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice

_CHOICE_TO_BUILDER = {
    ConnectorBuilderChoice.DEBUG: DebugConnectorBuilder,
    ConnectorBuilderChoice.DOLPHIN: DolphinConnectorBuilder,
    ConnectorBuilderChoice.NINTENDONT: NintendontConnectorBuilder,
    ConnectorBuilderChoice.DREAD: DreadConnectorBuilder,
}


@dataclasses.dataclass(frozen=True)
class ConnectorBuilderOption(JsonDataclass):
    choice: ConnectorBuilderChoice
    params: dict

    def create_builder(self) -> ConnectorBuilder:
        return _CHOICE_TO_BUILDER[self.choice](**self.params)
