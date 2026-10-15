from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest

from randovania.exporter.patch_data_factory import PatchDataFactory
from randovania.interface_common.worlds_configuration import INVALID_UUID, WorldsConfiguration
from randovania.layout.layout_description import LayoutDescription

SEED_UUID = uuid.UUID("11111111-1111-8111-8111-111111111111")
SESSION_UUID = uuid.UUID("22222222-2222-4222-a222-222222222222")


def _world_uuid_for(worlds_config: WorldsConfiguration) -> uuid.UUID:
    factory = MagicMock(spec=PatchDataFactory)
    factory.worlds_config = worlds_config
    factory.description = MagicMock(spec=LayoutDescription)
    factory.description.seed_uuid = SEED_UUID

    return PatchDataFactory.world_uuid.fget(factory)


@pytest.mark.parametrize(
    ("worlds_config", "expected"),
    [
        (WorldsConfiguration(0, {0: "Solo"}), SEED_UUID),
        (WorldsConfiguration(0, {0: "Solo"}, {0: SESSION_UUID}), SESSION_UUID),
        (WorldsConfiguration(0, {0: "A", 1: "B"}), INVALID_UUID),
        (WorldsConfiguration(0, {0: "A", 1: "B"}, {0: SESSION_UUID, 1: INVALID_UUID}), SESSION_UUID),
        (WorldsConfiguration(0, {0: "Coop"}, {0: SESSION_UUID}, is_coop=True), SESSION_UUID),
    ],
)
def test_world_uuid(worlds_config: WorldsConfiguration, expected: uuid.UUID) -> None:
    assert _world_uuid_for(worlds_config) == expected
