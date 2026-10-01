from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Protocol

from randovania.game_description.db.pickup_node import PickupNode

if TYPE_CHECKING:
    from pathlib import Path

    from randovania.game_description.game_description import GameDescription


class LuaConverter(Protocol):
    """Renders a Python value as a lua literal. Provided by each game's randomizer package."""

    def __call__(self, data: Any, wrap_strings: bool = False, /) -> str: ...


# FIXME: This is a copy of ODR's implementation just that the first param is a path instead of a name
# for a file within ODR's template folder
def replace_lua_template(
    file: Path, replacement: dict[str, Any], lua_convert: LuaConverter, wrap_strings: bool = False
) -> str:
    code = file.read_text()
    for key, content in replacement.items():
        # Replace `TEMPLATE("key")`-style replacements
        code = code.replace(f'TEMPLATE("{key}")', lua_convert(content, wrap_strings))
        # Replace `T__key__T`-style replacements
        code = code.replace(f"T__{key}__T", lua_convert(content, wrap_strings))

    unknown_templates = re.findall(r'TEMPLATE\("([^"]+)"\)', code)
    unknown_templates.extend(re.findall(r"T__(\w+)__T", code))

    if unknown_templates:
        raise ValueError("The following templates were left unfulfilled: " + str(unknown_templates))

    return code


def get_bootstrapper_for(
    game: GameDescription,
    lua_convert: LuaConverter,
    *,
    node_key_fallback: str,
    append_bootstrap_flag: bool,
) -> list[str]:
    """
    Builds the lua code that prepares a Mercury game for multiworld.

    `node_key_fallback` is the `extra` key identifying a pickup node when it has no `actor_name`.
    """
    all_code = []
    bootstrap_path = game.game.data_path.joinpath("assets", "lua")
    replacements = {
        "num_pickup_nodes": game.region_list.num_pickup_nodes,
        "inventory": "{{{}}}".format(
            ",".join(
                repr(r.extra["item_id"])
                for r in game.get_resource_database_view().get_all_items()
                if "item_id" in r.extra
            )
        ),
    }

    for i in range(4):
        bootstrap_part = bootstrap_path.joinpath(f"bootstrap_part_{i}.lua")
        all_code.append(replace_lua_template(bootstrap_part, replacements, lua_convert))

    locations_lua = bootstrap_path.joinpath("bootstrap_locations.lua")
    for world in game.region_list.regions:
        entries = []

        for node in world.all_nodes:
            if isinstance(node, PickupNode):
                if "actor_name" in node.extra:
                    key = node.extra["actor_name"]
                else:
                    key = node.extra[node_key_fallback]
                entries.append(f"{key}={node.pickup_index.index + 1}")

        if not entries:
            continue

        replacements["pairs"] = "{}".format(",".join(entries))
        replacements["location"] = "{}".format(repr(world.extra["scenario_id"] + "_"))
        code = replace_lua_template(locations_lua, replacements, lua_convert)
        all_code.append(code)

    if append_bootstrap_flag:
        all_code.append("RL.Bootstrap=true")

    return all_code
