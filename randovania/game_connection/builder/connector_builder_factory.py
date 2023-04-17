from __future__ import annotations

import dataclasses

from randovania.game_connection.builder.connector_builder import ConnectorBuilder
from randovania.game_connection.builder.dolphin_connector_builder import DolphinConnectorBuilder
from randovania.game_connection.builder.nintendont_connector_builder import NintendontConnectorBuilder
from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice

_CHOICE_TO_BUILDER = {
    ConnectorBuilderChoice.DOLPHIN: DolphinConnectorBuilder,
    ConnectorBuilderChoice.NINTENDONT: NintendontConnectorBuilder,
}


@dataclasses.dataclass(frozen=True)
class ConnectorBuilderOption:
    choice: ConnectorBuilderChoice
    params: dict

    @property
    def as_json(self):
        return {
            "choice": self.choice.value,
            "params": self.params,
        }

    @classmethod
    def from_json(cls, value: dict) -> ConnectorBuilderOption:
        return cls(
            ConnectorBuilderChoice(value["choice"]),
            value["params"],
        )

    def create_builder(self) -> ConnectorBuilder:
        return _CHOICE_TO_BUILDER[self.choice](**self.params)
