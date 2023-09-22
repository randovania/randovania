from __future__ import annotations

from collections.abc import Callable

ProgressUpdateCallable = Callable[[str, float], None]


class ConstantPercentageCallback:
    def __init__(self, status_update: ProgressUpdateCallable, percentage: float):
        self.status_update = status_update
        self.percentage = percentage

    def __call__(self, message: str) -> None:
        self.status_update(message, self.percentage)


class SuccessiveCallback:
    def __init__(self, status_update: ProgressUpdateCallable, max_calls: int):
        self.call_count = 0
        self.status_update = status_update
        self.max_calls = max_calls

    def __call__(self, message: str) -> None:
        self.call_count += 1
        self.status_update(message, min(self.call_count, self.max_calls) / self.max_calls)


class OffsetProgressUpdate:
    def __init__(self, status_update: ProgressUpdateCallable, offset: float, scale: float):
        self.status_update = status_update
        self.offset = offset
        self.scale = scale

    def __call__(self, message: str, percentage: float) -> None:
        percentage = min(percentage, 1.0)
        new_value = percentage if percentage < 0 else self.offset + percentage * self.scale
        self.status_update(message, new_value)


class DynamicSplitProgressUpdate:
    splits: dict[OffsetProgressUpdate, float]

    def __init__(self, status_update: ProgressUpdateCallable):
        self.status_update = status_update
        self.splits = {}

    def update_splits(self) -> None:
        total = sum(self.splits.values())
        scale = 1.0 / total

        offset = 0.0
        for split, weight in self.splits.items():
            this_scale = scale * weight
            split.offset = offset
            split.scale = this_scale
            offset += this_scale

    def create_split(self, weight: float = 1.0) -> ProgressUpdateCallable:
        new_split = OffsetProgressUpdate(self.status_update, 0, 1)
        self.splits[new_split] = weight
        self.update_splits()
        return new_split


def create_progress_update_from_successive_messages(
    status_update: ProgressUpdateCallable, max_calls: int
) -> Callable[[str], None]:
    """
    Creates a callable that invokes the given ProgressUpdateCallable each it's called,
    with percentage based on call count.
    :param status_update:
    :param max_calls:
    :return:
    """
    return SuccessiveCallback(status_update, max_calls)


def split_progress_update(status_update: ProgressUpdateCallable, parts: int) -> list[ProgressUpdateCallable]:
    """
    Creates a list of ProgressUpdateCallable that when called progress successively,
    progresses a given ProgressUpdateCallable.
    :param status_update:
    :param parts:
    :return:
    """
    split = DynamicSplitProgressUpdate(status_update)
    return [split.create_split() for _ in range(parts)]
