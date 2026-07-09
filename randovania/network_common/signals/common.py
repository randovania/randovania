from __future__ import annotations

import typing
from collections.abc import Callable

if typing.TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from typing import Annotated, Any

    from randovania.lib.json_lib import JsonObject_RO
    from randovania.lib.type_lib import AsyncCallable


type TypedBytes[T] = Annotated[bytes, T]

type TypedJsonObject[T] = Annotated[JsonObject_RO, T]

type SioDataType = str | bytes | Mapping[str, SioDataType] | Sequence[SioDataType]


class SignalBase[**P, RetT, CallbackT: AsyncCallable]:
    fn: CallbackT
    message: str
    handlers: set[CallbackT]

    all_signals: typing.ClassVar[tuple[SignalBase, ...]] = ()

    def __init__(self, fn: CallbackT, message: str) -> None:
        self.__class__.all_signals += (self,)

        self.fn = fn
        self.message = message
        self.handlers = set()

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> typing.Never:
        raise TypeError(
            f"Cannot call {self.__class__.__name__} {self.fn.__name__} directly. Did you "
            f"mean to call {self.fn.__name__}.{self._public_call_site.__name__}() instead?"
        )

    @property
    def _public_call_site(self) -> Callable:
        """
        The function users should call
        instead of calling the signal directly.
        """
        raise NotImplementedError

    def _add_handler(self, handler: CallbackT) -> None:
        """Adds the handler to the set of registered handlers."""
        self.handlers.add(handler)

    def _check_handlers(self) -> None:
        """
        Verifies whether this signal has any handlers registered.
        Used in tests to ensure all signals have at least one handler.
        """

        if not self.handlers:
            raise TypeError(f"{self.__class__.__name__} {self.fn.__name__} has no signal handlers registered.")


def args_to_sio_data(*args: Any) -> SioDataType | tuple[SioDataType, ...]:
    if len(args) == 1:
        return typing.cast("SioDataType", args[0])
    else:
        return typing.cast("tuple[SioDataType, ...]", args)
