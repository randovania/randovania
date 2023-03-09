import traceback


class ExportFailure(Exception):
    def __init__(self, reason: str, output: str | None):
        super().__init__(reason)
        self.output = output

    def detailed_text(self) -> str:
        result = []
        if self.output is not None:
            result.append(self.output)
        return "\n".join(result)
