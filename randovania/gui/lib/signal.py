import typing
from collections.abc import Callable
from typing import Generic, TypeVarTuple

FuncArgs = TypeVarTuple("FuncArgs")


class RdvSignal(Generic[*FuncArgs]):
    def __init__(self) -> None:
        self.subscribers: list = []

    def emit(self, *func_args: *FuncArgs) -> None:
        for x in self.subscribers:
            x(*func_args)

    def connect(self, func: Callable[[*FuncArgs], typing.Any]) -> None:
        self.subscribers.append(func)
