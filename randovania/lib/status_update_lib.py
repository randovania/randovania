from typing import Callable, List

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
        self.status_update(
            message,
            min(self.call_count, self.max_calls) / self.max_calls
        )


class OffsetProgressUpdate:
    def __init__(self, status_update: ProgressUpdateCallable, offset: float, scale: float):
        self.status_update = status_update
        self.offset = offset
        self.scale = scale

    def __call__(self, message: str, percentage: float) -> None:
        new_value = percentage if percentage < 0 else self.offset + percentage * self.scale
        self.status_update(
            message,
            new_value
        )


def create_progress_update_from_successive_messages(
        status_update: ProgressUpdateCallable,
        max_calls: int) -> Callable[[str], None]:
    """
    Creates a callable that invokes the given ProgressUpdateCallable each it's called,
    with percentage based on call count.
    :param status_update:
    :param max_calls:
    :return:
    """
    return SuccessiveCallback(status_update, max_calls)


def split_progress_update(status_update: ProgressUpdateCallable, parts: int) -> List[ProgressUpdateCallable]:
    """
    Creates a list of ProgressUpdateCallable that when called progress successively,
    progresses a given ProgressUpdateCallable.
    :param status_update:
    :param parts:
    :return:
    """
    scale = 1.0 / parts
    return [
        OffsetProgressUpdate(status_update, scale * i, scale)
        for i in range(parts)
    ]
