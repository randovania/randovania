from __future__ import annotations

import asyncio
import dataclasses
from pathlib import Path
from typing import TYPE_CHECKING

import aiohttp

from randovania.exporter.game_exporter import GameExporter, GameExportParams

if TYPE_CHECKING:
    from randovania.exporter.patch_data_factory import PatcherDataMeta
    from randovania.lib import status_update_lib


@dataclasses.dataclass(frozen=True)
class FactorioGameExportParams(GameExportParams):
    output_path: Path


async def download_file(url: str, path: Path) -> None:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            resp.raise_for_status()
            with path.open("wb") as fd:
                async for chunk in resp.content.iter_chunked(8192):
                    fd.write(chunk)


class FactorioGameExporter(GameExporter[FactorioGameExportParams]):
    _busy: bool = False

    @property
    def can_start_new_export(self) -> bool:
        """
        Checks if the exporter is busy right now
        """
        return self._busy

    @property
    def export_can_be_aborted(self) -> bool:
        """
        Checks if export_game can be aborted
        """
        return False

    def export_params_type(self) -> type[FactorioGameExportParams]:
        """
        Returns the type of the GameExportParams expected by this exporter.
        """
        return FactorioGameExportParams

    def _do_export_game(
        self,
        patch_data: dict,
        export_params: FactorioGameExportParams,
        progress_update: status_update_lib.ProgressUpdateCallable,
        randovania_meta: PatcherDataMeta,
    ) -> None:
        import factorio_randovania_mod

        export_params.output_path.mkdir(parents=True, exist_ok=True)

        assets_mod = factorio_randovania_mod.export_mod(
            patch_data,
            export_params.output_path,
        )
        if assets_mod is not None:
            assets_path, assets_url = assets_mod
            asyncio.run(download_file(assets_url, assets_path))
