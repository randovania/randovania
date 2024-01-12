from __future__ import annotations

import configparser
import dataclasses
import shutil
import typing
from pathlib import Path
from typing import TYPE_CHECKING

from randovania.exporter.game_exporter import GameExporter, GameExportParams

if TYPE_CHECKING:
    from randovania.lib import status_update_lib


@dataclasses.dataclass(frozen=True)
class FactorioGameExportParams(GameExportParams):
    pass
    # input_path: Path
    # output_path: Path


def wrap_array_pretty(data: list) -> str:
    return "{\n" + ",\n".join(wrap(item, "    ") for item in data) + "}\n"


def wrap(data: typing.Any, indent: str = "") -> str:
    if isinstance(data, list):
        return "{" + ", ".join(wrap(item, indent) for item in data) + "}"

    if isinstance(data, dict):
        return (
            "{\n"
            + "\n".join(f"{indent}    {key} = {wrap(value, f'{indent}    ')}," for key, value in data.items())
            + f"\n{indent}}}"
        )

    if isinstance(data, bool):
        return "true" if data else "false"

    if data is None:
        return "nil"

    if isinstance(data, str):
        return f'"{data}"'

    return str(data)


class FactorioGameExporter(GameExporter):
    _busy: bool = False

    @property
    def is_busy(self) -> bool:
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

    def export_params_type(self) -> type[GameExportParams]:
        """
        Returns the type of the GameExportParams expected by this exporter.
        """
        return FactorioGameExportParams

    def _do_export_game(
        self,
        patch_data: dict,
        export_params: GameExportParams,
        progress_update: status_update_lib.ProgressUpdateCallable,
    ) -> None:
        assert isinstance(export_params, FactorioGameExportParams)
        template_path = Path(r"C:\Users\henri\programming\factorio-randovania-mod\lua_src")
        output_folder = Path(r"F:\Factorio_1.1.91-rdv-mod\mods")

        output_path = output_folder.joinpath("randovania-layout")
        shutil.rmtree(output_path, ignore_errors=True)

        locale = configparser.ConfigParser()
        locale.read(
            [
                template_path.joinpath("locale/en/strings.cfg"),
            ]
        )

        tech_tree_lua = []
        local_unlock_lines = ["return {"]
        for tech_name, tech in patch_data["technologies"].items():
            locale["technology-name"][tech_name] = tech["locale_name"]
            locale["technology-description"][tech_name] = tech["description"]
            tech_tree_lua.append(
                {
                    "name": tech_name,
                    "icon": tech["icon"],
                    "costs": {
                        "count": tech["cost"]["count"],
                        "time": tech["cost"]["time"],
                        "ingredients": [[it, 1] for it in tech["cost"]["ingredients"]],
                    },
                    "prerequisites": tech["prerequisites"] if tech["prerequisites"] else None,
                }
            )
            if tech["unlocks"]:
                local_unlock_lines.append(f'["{tech_name}"] = {wrap(tech["unlocks"])},')

        local_unlock_lines.append("}")

        shutil.copytree(template_path, output_path)
        output_path.joinpath("generated", "tech-tree.lua").write_text("return " + wrap_array_pretty(tech_tree_lua))
        output_path.joinpath("generated", "local-unlocks.lua").write_text("\n".join(local_unlock_lines))
        output_path.joinpath("generated", "starting-tech.lua").write_text(
            "return " + wrap_array_pretty(patch_data["starting_tech"])
        )
        with output_path.joinpath("locale/en/strings.cfg").open("w") as f:
            locale.write(f, space_around_delimiters=False)
