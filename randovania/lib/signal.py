# Original file from https://github.com/dgovil/PySignal


# The MIT License (MIT)

# Copyright (c) 2016 Dhruv Govil

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


from __future__ import annotations

import inspect
import weakref
from collections.abc import Callable
from functools import partial
from typing import Any, Generic, Never, Self, overload

from typing_extensions import ParamSpec, TypeIs, TypeVar

P = ParamSpec("P", default=[])
T = TypeVar("T", default=None)

type Slot[**P, T] = Callable[P, T] | weakref.ref[Callable[P, T]] | weakref.WeakMethod[Callable[P, T]]
type SignalResults[**P, T] = weakref.WeakKeyDictionary[Callable[P, T], T]


class RdvSignalInstance(Generic[P, T]):
    """
    The RdvSignalInstance is the core object that handles connection and emission.
    """

    block: bool
    """Prevents emitting this signal when set."""

    def __init__(self) -> None:
        self.block = False
        self._slots: list[Slot[P, T]] = []

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> SignalResults[P, T]:
        return self.emit(*args, **kwargs)

    def emit(self, *args: P.args, **kwargs: P.kwargs) -> SignalResults[P, T]:
        """
        Calls all the connected slots with the provided args and kwargs unless block is activated
        """
        results: SignalResults[P, T] = weakref.WeakKeyDictionary()

        if self.block:
            return results

        def is_weak_ref(slot: Slot[P, T]) -> TypeIs[weakref.ref[Callable[P, T]]]:
            return isinstance(slot, weakref.ref)

        for slot in self._slots:
            if is_weak_ref(slot):
                # If it's a weakref, call the ref to get the instance and then call the func
                # Don't wrap in try/except so we don't risk masking exceptions from the actual func call
                tested_slot = slot()
                if tested_slot is not None:
                    results[tested_slot] = tested_slot(*args, **kwargs)
            else:
                # Else call it in a standard way. Should be just lambdas at this point
                results[slot] = slot(*args, **kwargs)

        return results

    def _get_slot(self, slot: Callable[P, T]) -> Slot:
        if not callable(slot):
            raise TypeError(f"{slot} is not callable")

        # If it's a partial, a Signal or a lambda
        if isinstance(slot, partial | RdvSignalInstance) or getattr(slot, "__name__", "") == "<lambda>":
            return slot

        # If it's an instance method
        if inspect.ismethod(slot):
            return weakref.WeakMethod[Callable[P, T]](slot)

        # If it's just a function
        return weakref.ref(slot)

    def connect(self, slot: Callable[P, T]) -> None:
        """
        Connects the signal to any callable object
        """
        slot_ref = self._get_slot(slot)
        if slot_ref not in self._slots:
            self._slots.append(slot_ref)

    def disconnect(self, slot: Callable[P, T]) -> None:
        """
        Disconnects the slot from the signal
        """
        slot_ref = self._get_slot(slot)
        self._slots.remove(slot_ref)

    def clear(self) -> None:
        """Clears the signal of all connected slots"""
        self._slots = []


class RdvSignal(Generic[P, T]):
    """
    The RdvSignal allows a signal to be set on a class rather than an instance.
    This emulates the behavior of a PyQt signal
    """

    _map: dict[Self, weakref.WeakKeyDictionary[Any, RdvSignalInstance]] = {}

    @overload
    def __get__(self, instance: None, owner: Any) -> Self: ...
    @overload
    def __get__(self, instance: Any, owner: Any) -> RdvSignalInstance[P, T]: ...

    def __get__(self, instance: Any, owner: Any) -> Self | RdvSignalInstance[P, T]:
        if instance is None:
            # When we access RdvSignal element on the class object without any instance,
            # we return the RdvSignal itself
            return self
        tmp = self._map.setdefault(self, weakref.WeakKeyDictionary())
        return tmp.setdefault(instance, RdvSignalInstance[P, T]())  # type: ignore[arg-type, return-value]

    def __set__(self, instance: Any, value: Any) -> Never:
        raise RuntimeError("Cannot reassign an RdvSignal")
