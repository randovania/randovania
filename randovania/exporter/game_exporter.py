import dataclasses
import hashlib
import json
import typing
from pathlib import Path
from typing import TYPE_CHECKING

import sentry_sdk

from randovania.lib import status_update_lib
from randovania.lib.background_task import AbortBackgroundTask
from randovania.patching.patchers.exceptions import UnableToExportError

if TYPE_CHECKING:
    from randovania.exporter.patch_data_factory import PatcherDataMeta


@dataclasses.dataclass(frozen=True)
class GameExportParams:
    spoiler_output: Path | None

    def calculate_input_hash(self) -> dict[str, str | None]:
        """
        Hashes all input files. Different keys are for different paths, like different input for cross-game models.
        """
        return {}


class GameExporter:
    @property
    def is_busy(self) -> bool:
        """
        Checks if the exporter is busy right now
        """
        raise NotImplementedError

    @property
    def export_can_be_aborted(self) -> bool:
        """
        Checks if export_game can be aborted
        """
        raise NotImplementedError

    def export_params_type(self) -> type[GameExportParams]:
        """
        Returns the type of the GameExportParams expected by this exporter.
        """
        raise NotImplementedError

    def _before_export(self):
        pass

    def _do_export_game(
        self,
        patch_data: dict,
        export_params: GameExportParams,
        progress_update: status_update_lib.ProgressUpdateCallable,
    ) -> None:
        raise NotImplementedError

    def _after_export(self):
        pass

    def export_game(
        self,
        patch_data: dict,
        export_params: GameExportParams,
        progress_update: status_update_lib.ProgressUpdateCallable,
    ):
        meta_data: PatcherDataMeta = patch_data.pop("_randovania_meta")
        with sentry_sdk.isolation_scope() as scope:
            scope.add_attachment(
                json.dumps(patch_data).encode("utf-8"),
                filename="patcher.json",
                content_type="application/json",
                add_to_transactions=True,
            )
            with scope.start_transaction(op="task", name="export_game") as span:
                span.set_tag("exporter", type(self).__name__)
                span.set_tag("layout_was_user_modified", meta_data["layout_was_user_modified"])

                self._before_export()
                try:
                    self._do_export_game(patch_data, export_params, progress_update)
                    scope.set_tag("exception", None)
                except (AbortBackgroundTask, UnableToExportError) as e:
                    scope.set_tag("exception", type(e).__name__)
                    raise

                except Exception as e:
                    scope.set_tag("exception", type(e).__name__)
                    input_hash = export_params.calculate_input_hash()
                    scope.capture_exception(
                        e,
                        contexts={
                            "input_hash": input_hash,
                        },
                    )
                    # TODO: compare `input_hash` with known good values and if different,
                    # wrap into a "User Error" exception
                    raise

                finally:
                    self._after_export()


def _hash_file_internal(path: Path) -> typing.Any:
    sha = hashlib.sha1()

    with path.open("rb") as f:
        while True:
            data = f.read(65536)
            if not data:
                break
            sha.update(data)

    return sha


def input_hash_for_file(path: Path | None) -> str | None:
    """
    Calculates the sha256 of a given file.
    """
    if path is None:
        return None

    sha = _hash_file_internal(path)
    return f"sha1:{sha.hexdigest()}"


def input_hash_for_directory(path: Path) -> str:
    """
    Calculates the sha256 of every file in a directory, then the sha256 of the combined result.
    """
    sha = hashlib.sha1()

    for f in path.rglob("*"):
        if f.is_file():
            sha.update(_hash_file_internal(f).digest())

    return f"sha1:{sha.hexdigest()}"
