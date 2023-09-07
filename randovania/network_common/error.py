from __future__ import annotations

from typing import Self


class BaseNetworkError(Exception):
    @classmethod
    def human_readable_name(cls) -> str:
        return cls.__name__

    @classmethod
    def code(cls):
        return NotImplementedError()

    @property
    def detail(self):
        return None

    @property
    def as_json(self) -> dict:
        return {
            "error": {
                "code": self.code(),
                "detail": self.detail,
            }
        }

    @classmethod
    def from_detail(cls, detail) -> Self:
        return cls()

    @classmethod
    def from_json(cls, data: dict) -> Self | None:
        if "error" not in data:
            return None

        code = data["error"]["code"]
        detail = data["error"]["detail"]

        for ret_cls in BaseNetworkError.__subclasses__():
            if code == ret_cls.code():
                return ret_cls.from_detail(detail)

        raise RuntimeError("Unknown error")

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.detail == other.detail

    def __str__(self):
        return self.human_readable_name()


class NotLoggedInError(BaseNetworkError):
    @classmethod
    def code(cls):
        return 1


class WrongPasswordError(BaseNetworkError):
    @classmethod
    def code(cls):
        return 2


class NotAuthorizedForActionError(BaseNetworkError):
    @classmethod
    def code(cls):
        return 3


class InvalidActionError(BaseNetworkError):
    def __init__(self, message: str):
        self.message = message

    @classmethod
    def code(cls):
        return 4

    @property
    def detail(self):
        return self.message

    @classmethod
    def from_detail(cls, detail) -> Self:
        return cls(detail)

    def __str__(self):
        return f"Invalid Action: {self.message}"


class InvalidSessionError(BaseNetworkError):
    @classmethod
    def code(cls):
        return 5


class ServerError(BaseNetworkError):
    """An unexpected error happened when processing the request."""

    @classmethod
    def human_readable_name(cls) -> str:
        return "Internal Server Error"

    @classmethod
    def code(cls):
        return 6


class RequestTimeoutError(BaseNetworkError):
    def __init__(self, message: str):
        self.message = message

    @classmethod
    def code(cls):
        return 7

    @property
    def detail(self):
        return self.message

    @classmethod
    def from_detail(cls, detail) -> Self:
        return cls(detail)

    def __str__(self):
        return f"Request timed out: {self.message}"


class UserNotAuthorizedToUseServerError(BaseNetworkError):
    """When the user is not authorized to log in to the server. Used for the Beta Tester role enforcement."""

    @classmethod
    def code(cls):
        return 8


class UnsupportedClientError(BaseNetworkError):
    """When the version headers sent by the client does not match the versions from the server."""

    def __init__(self, message: str):
        self.message = message

    @classmethod
    def code(cls):
        return 9

    @property
    def detail(self):
        return self.message

    @classmethod
    def from_detail(cls, detail) -> Self:
        return cls(detail)

    def __str__(self):
        return f"Unsupported client: {self.message}"


class WorldDoesNotExistError(BaseNetworkError):
    """When the UUID of a request does not mention a world that exists"""

    @classmethod
    def code(cls):
        return 10


class WorldNotAssociatedError(BaseNetworkError):
    """When the World mentioned with a request is not associated with the user currently authenticated."""

    @classmethod
    def code(cls):
        return 11
