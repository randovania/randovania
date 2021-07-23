from typing import Optional, Type


class BaseNetworkError(Exception):

    @classmethod
    def code(cls):
        return NotImplementedError()

    @property
    def detail(self):
        return None

    @property
    def as_json(self):
        return {
            "error": {
                "code": self.code(),
                "detail": self.detail,
            }
        }

    @classmethod
    def from_detail(cls, detail) -> "BaseNetworkError":
        return cls()


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
    def from_detail(cls, detail) -> "InvalidAction":
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


def decode_error(data: dict) -> Optional[BaseNetworkError]:
    if "error" not in data:
        return None

    code = data["error"]["code"]
    detail = data["error"]["detail"]

    for cls in BaseNetworkError.__subclasses__():
        cls: Type[BaseNetworkError] = cls
        if code == cls.code():
            return cls.from_detail(detail)

    raise RuntimeError("Unknown error")
