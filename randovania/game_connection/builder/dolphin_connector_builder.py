from __future__ import annotations

from subprocess import Popen, TimeoutExpired
from typing import TYPE_CHECKING

from randovania.game_connection.builder.prime_connector_builder import PrimeConnectorBuilder
from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice
from randovania.game_connection.executor.dolphin_executor import DolphinExecutor

if TYPE_CHECKING:
    from randovania.game_connection.executor.memory_operation import MemoryOperationExecutor


class DolphinConnectorBuilder(PrimeConnectorBuilder):
    dolphin_cmd: str
    dolphin_comm: str
    dolphin_child_process: Popen | None

    def __init__(self, dolphin_cmd: str = "", dolphin_comm: str = ""):
        super().__init__()
        self.dolphin_cmd = dolphin_cmd
        self.dolphin_comm = dolphin_comm
        self.dolphin_child_process = None

    @property
    def pretty_text(self) -> str:
        name = super().pretty_text

        # If dolphin_comm is set, display both the program being run (if applicable)
        # and the commname we will search for in the connector description.
        if self.dolphin_comm:
            if self.dolphin_cmd:
                return f"{name}: run '{self.dolphin_cmd}', attach to '{self.dolphin_comm}'"
            else:
                return f"{name}: attach to already-running '{self.dolphin_comm}'"

        # Otherwise just display the program we're running (again, if any) and
        # rely on pyDME's compiled-in defaults for autodetection.
        elif self.dolphin_cmd:
            return f"{name}: run '{self.dolphin_cmd}', then autodetect"
        else:
            return f"{name}: autodetect using defaults"

    @property
    def connector_builder_choice(self) -> ConnectorBuilderChoice:
        return ConnectorBuilderChoice.DOLPHIN

    def start_dolphin(self) -> None:
        if not self.dolphin_cmd:
            return

        if self.dolphin_child_process is None:
            self.logger.info(f"Dolphin not running, attempting to start it: {self.dolphin_cmd}")
            self.dolphin_child_process = Popen(self.dolphin_cmd, shell=True)

        elif self.dolphin_child_process.poll() is not None:
            self.logger.info(f"Dolphin has exited, restarting it: {self.dolphin_cmd}")
            self.dolphin_child_process = Popen(self.dolphin_cmd, shell=True)

    def stop_dolphin(self) -> None:
        if self.dolphin_child_process is not None:
            self.logger.info("Shutting down child Dolphin process.")
            # Send TERM twice, since the first one just opens a
            # "are you sure you want to exit?" popup.
            self.dolphin_child_process.terminate()
            self.dolphin_child_process.terminate()
            try:
                self.dolphin_child_process.wait(timeout=1)
            except TimeoutExpired:
                self.dolphin_child_process.kill()
            self.dolphin_child_process = None

    def create_executor(self) -> MemoryOperationExecutor:
        return DolphinExecutor(self.dolphin_comm)

    def configuration_params(self) -> dict:
        return {
            "dolphin_cmd": self.dolphin_cmd,
            "dolphin_comm": self.dolphin_comm,
        }
