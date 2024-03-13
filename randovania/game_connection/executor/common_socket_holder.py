import dataclasses
from asyncio import StreamReader, StreamWriter


@dataclasses.dataclass()
class CommonSocketHolder:
    reader: StreamReader
    writer: StreamWriter
    api_version: int
