import dataclasses
from asyncio import StreamReader, StreamWriter


@dataclasses.dataclass()
class CommonSocketHolder:
    reader: StreamReader
    writer: StreamWriter
    api_version: int


@dataclasses.dataclass()
class RequestNumberSocketHolder(CommonSocketHolder):
    """For protocols where the game echoes back a rolling request number to match responses to requests."""

    request_number: int
