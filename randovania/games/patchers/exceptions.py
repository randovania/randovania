import traceback
from typing import Optional


class ExportFailure(Exception):
    def __init__(self, reason: str, output: Optional[str]):
        super().__init__(reason)
        self.output = output

    def detailed_text(self) -> str:
        result = []
        if self.output is not None:
            result.append(self.output)
        if self.__traceback__ is not None:
            result.extend(traceback.format_tb(self.__traceback__))
        return "\n".join(result)
