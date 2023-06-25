from typing import Self


class BaseNetworkError(Exception):

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
            ret_cls: type[BaseNetworkError] = ret_cls
            if code == ret_cls.code():
                return ret_cls.from_detail(detail)

        raise RuntimeError("Unknown error")

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.detail == other.detail


class NotLoggedIn(BaseNetworkError):
    @classmethod
    def code(cls):
        return 1


class WrongPassword(BaseNetworkError):
    @classmethod
    def code(cls):
        return 2


class NotAuthorizedForAction(BaseNetworkError):
    @classmethod
    def code(cls):
        return 3


class InvalidAction(BaseNetworkError):
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


class InvalidSession(BaseNetworkError):
    @classmethod
    def code(cls):
        return 5


class ServerError(BaseNetworkError):
    @classmethod
    def code(cls):
        return 6


class RequestTimeout(BaseNetworkError):
    def __init__(self, message: str):
        self.message = message

    @classmethod
    def code(cls):
        return 7

    @property
    def detail(self):
        return self.message

    @classmethod
    def from_detail(cls, detail) -> "RequestTimeout":
        return cls(detail)

    def __str__(self):
        return f"Request timed out: {self.message}"


class UserNotAuthorized(BaseNetworkError):
    """When the user is not authorized to log in to the server."""

    @classmethod
    def code(cls):
        return 8


class UnsupportedClient(BaseNetworkError):
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
    @classmethod
    def code(cls):
        return 10


class WorldNotAssociatedError(BaseNetworkError):
    @classmethod
    def code(cls):
        return 11
