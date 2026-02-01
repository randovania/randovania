from __future__ import annotations

import typing
from collections.abc import Hashable, Iterable

import typing_extensions

if typing.TYPE_CHECKING:
    from randovania.game_description.resources.resource_type import ResourceType


class ResourceInfo(Hashable, typing.Protocol):
    @property
    def resource_index(self) -> int: ...

    @property
    def long_name(self) -> str: ...

    @property
    def short_name(self) -> str: ...

    @property
    def resource_type(self) -> ResourceType: ...


ResourceInfoT = typing_extensions.TypeVar("ResourceInfoT", bound=ResourceInfo, default=ResourceInfo)


if typing.TYPE_CHECKING:
    ResourceQuantity: typing.TypeAlias = tuple[ResourceInfoT, int]
    ResourceGainTuple: typing.TypeAlias = tuple[ResourceQuantity[ResourceInfoT], ...]
    ResourceGain: typing.TypeAlias = Iterable[ResourceQuantity[ResourceInfoT]]
