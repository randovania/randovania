import functools
import logging
import math
from pathlib import Path
from typing import List, Dict, Optional, NamedTuple

import discord
import graphviz
from discord import Embed
from discord.ext import commands
from discord_slash import SlashContext, SlashCommandOptionType, ComponentContext, ButtonStyle
from discord_slash.utils import manage_commands, manage_components

from randovania.game_description import default_database, pretty_print
from randovania.game_description.game_description import GameDescription
from randovania.game_description.world.area import Area
from randovania.game_description.world.world import World
from randovania.games.game import RandovaniaGame
from randovania.lib import enum_lib
from randovania.server.discord.bot import RandovaniaBot


class SplitWorld(NamedTuple):
    world: World
    name: str
    areas: List[Area]


def render_area_with_graphviz(area: Area) -> Optional[Path]:
    dot = graphviz.Digraph(comment=area.name)
    for node in area.nodes:
        dot.node(node.name)

    known_edges = set()
    for source, target in area.connections.items():
        for target_node, requirement in target.items():
            direction = None
            if source in area.connections.get(target_node):
                direction = "both"
                known_edges.add((target_node.name, source.name))

            if (source.name, target_node.name) not in known_edges:
                dot.edge(source.name, target_node.name, dir=direction)
                known_edges.add((source.name, target_node.name))

    try:
        return Path(dot.render(format="png", cleanup=True))
    except graphviz.backend.ExecutableNotFound as e:
        logging.info("Unable to render graph for %s: %s", area.name, str(e))
        return None


async def create_split_worlds(db: GameDescription) -> List[SplitWorld]:
    world_options = []

    for world in db.world_list.worlds:
        for is_dark_world in [False, True]:
            if is_dark_world and world.dark_name is None:
                continue

            areas = sorted([area for area in world.areas if area.in_dark_aether == is_dark_world],
                           key=lambda it: it.name)
            name = world.correct_name(is_dark_world)
            if len(areas) > 25:
                per_part = math.ceil(len(areas) / math.ceil(len(areas) / 25))

                while areas:
                    areas_part = areas[:per_part]
                    del areas[:per_part]

                    world_options.append(SplitWorld(world, "{} ({}-{})".format(name, areas_part[0].name[:2],
                                                                               areas_part[-1].name[:2]), areas_part))
            else:
                world_options.append(SplitWorld(world, name, areas))

    world_options.sort(key=lambda it: it[1])
    return world_options


class DatabaseCommandCog(commands.Cog):
    _split_worlds: Dict[RandovaniaGame, List[SplitWorld]]

    def __init__(self, configuration: dict, bot: RandovaniaBot):
        self.configuration = configuration
        self.bot = bot
        self._split_worlds = {}
        self._on_database_component_listener = {}

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.slash.add_slash_command(
            self.database_command,
            name="database-inspect",
            description="Consult the Randovania's logic database for one specific room.",
            guild_ids=[self.configuration["guild"]],
            options=[
                manage_commands.create_option(
                    "game", "The game's database to check.",
                    option_type=SlashCommandOptionType.STRING,
                    required=True,
                    choices=[manage_commands.create_choice(game.value, game.long_name)
                             for game in enum_lib.iterate_enum(RandovaniaGame)]
                )
            ],
        )

        def add_id(custom_id: str, call, **kwargs):
            self._on_database_component_listener[custom_id] = functools.partial(call, **kwargs)

        for game in enum_lib.iterate_enum(RandovaniaGame):
            db = default_database.game_description_for(game)
            world_options = await create_split_worlds(db)
            self._split_worlds[game] = world_options

            add_id(f"{game.value}_world", self.on_database_world_selected, game=game)
            add_id(f"back_to_{game.value}", self.on_database_back_to_game, game=game)

            for i, split_world in enumerate(world_options):
                add_id(f"{game.value}_world_{i}", self.on_database_area_selected, game=game, split_world=split_world,
                       world_id=i)
                for j, area in enumerate(split_world.areas):
                    add_id(f"{game.value}_world_{i}_area_{j}", self.on_area_node_selection, game=game, area=area)

        self.bot.slash.add_component_callback(
            self.on_database_component,
            components=list(self._on_database_component_listener.keys()),
            use_callback_name=False,
        )

        await self.bot.slash.sync_all_commands()

    def _message_components_for_game(self, game: RandovaniaGame):
        options = []
        for i, (world, world_name, areas) in enumerate(self._split_worlds[game]):
            custom_id = f"{game.value}_world_{i}"
            options.append(manage_components.create_select_option(world_name, value=custom_id))

        action_row = manage_components.create_actionrow(manage_components.create_select(
            options=options,
            custom_id=f"{game.value}_world",
            placeholder="Choose your region",
        ))
        embed = Embed(title=f"{game.long_name} Database", description="Choose the world subset to visualize.")
        logging.info("Responding requesting list of worlds for game %s.", game.long_name)
        return embed, [action_row],

    async def database_command(self, ctx: SlashContext, game: str):
        game = RandovaniaGame(game)
        embed, components = self._message_components_for_game(game)
        await ctx.send(embed=embed, components=components, hidden=True)

    async def on_database_component(self, ctx: ComponentContext):
        await self._on_database_component_listener[ctx.custom_id](ctx)

    async def on_database_back_to_game(self, ctx: ComponentContext, game: RandovaniaGame):
        embed, components = self._message_components_for_game(game)
        await ctx.edit_origin(embed=embed, components=components, hidden=True)

    async def on_database_world_selected(self, ctx: ComponentContext, game: RandovaniaGame):
        option_selected = ctx.selected_options[0]

        valid_items = [
            it
            for i, it in enumerate(self._split_worlds[game])
            if f"{game.value}_world_{i}" == option_selected
        ]
        if not valid_items:
            return await ctx.edit_origin(
                components=[], embeds=[],
                content=f"Invalid selected option, unable to find given world subset '{option_selected}'."
            )
        index = self._split_worlds[game].index(valid_items[0])
        world, world_name, areas = valid_items[0]

        select = manage_components.create_select(
            options=[
                manage_components.create_select_option(area.name, value=f"area_{i}")
                for i, area in sorted(enumerate(areas), key=lambda it: it[1].name)
            ],
            custom_id=f"{game.value}_world_{index}",
            placeholder="Choose the room",
        )
        action_row = manage_components.create_actionrow(select)
        back_row = manage_components.create_actionrow(manage_components.create_button(
            style=ButtonStyle.secondary,
            label="Back",
            custom_id=f"back_to_{game.value}",
        ))

        embed = Embed(title=f"{game.long_name} Database",
                      description=f"Choose the room in {world_name} to visualize.")
        logging.info("Responding to area selection for section %s with %d options.", world_name, len(areas))
        await ctx.edit_origin(
            embed=embed,
            components=[
                action_row,
                back_row,
            ],
        )

    async def on_database_area_selected(self, ctx: ComponentContext, game: RandovaniaGame, split_world: SplitWorld,
                                        world_id: int):
        option_selected = ctx.selected_options[0]

        valid_items = [
            area
            for i, area in enumerate(split_world.areas)
            if f"area_{i}" == option_selected
        ]
        if not valid_items:
            return await ctx.edit_origin(
                components=[], embeds=[],
                content=f"Invalid selected option, unable to find given area '{option_selected}'."
            )

        area = valid_items[0]
        db = default_database.game_description_for(game)

        title = "{}: {}".format(game.long_name, db.world_list.area_name(area))

        select = manage_components.create_select(
            options=[
                manage_components.create_select_option(node.name, value=node.name)
                for i, node in sorted(enumerate(area.nodes), key=lambda it: it[1].name)
            ],
            max_values=min(10, len(area.nodes)),
            custom_id=f"{game.value}_world_{world_id}_{option_selected}",
            placeholder="Choose the room",
        )
        action_row = manage_components.create_actionrow(select)

        files = []

        image_path = render_area_with_graphviz(area)
        if image_path is not None:
            files.append(discord.File(image_path))

        logging.info("Responding to area for %s with %d attachments.", area.name, len(files))
        await ctx.send(
            content=f"**{title}**\nRequested by {ctx.author.display_name}.",
            files=files,
            components=[
                action_row,
            ],
        )

        if image_path is not None:
            image_path.unlink()

    async def on_area_node_selection(self, ctx: ComponentContext, game: RandovaniaGame, area: Area):
        db = default_database.game_description_for(game)

        def snipped_message(n: str) -> str:
            return f"\n{n}: *Skipped*\n"

        body_by_node = {}
        embeds = []

        for node in sorted(area.nodes, key=lambda it: it.name):
            if node.name not in ctx.selected_options:
                continue

            name = node.name
            if node.heal:
                name += " (Heals)"
            if area.default_node == node.name:
                name += "; Spawn Point"

            body = pretty_print.pretty_print_node_type(node, db.world_list) + "\n"

            node_bodies = []

            for target_node, requirement in db.world_list.area_connections_from(node):
                extra_lines = []
                for level, text in pretty_print.pretty_print_requirement(requirement.simplify()):
                    extra_lines.append("{}{}".format("  " * level, text))

                inner = "\n".join(extra_lines)
                new_entry = f"\n{target_node.name}:\n```\n{inner}\n```"
                node_bodies.append([target_node.name, new_entry])

            space_left = 4096 - len(body)
            for node_name, _ in node_bodies:
                space_left -= len(snipped_message(node_name))

            node_bodies.sort(key=lambda it: len(it[1]))
            for node_i, (node_name, node_entry) in enumerate(node_bodies):
                snipped = snipped_message(node_name)
                space_left += len(snipped)
                if len(node_entry) <= space_left:
                    space_left -= len(node_entry)
                else:
                    node_bodies[node_i][1] = snipped

            node_bodies.sort(key=lambda it: it[0])
            for _, node_entry in node_bodies:
                body += node_entry

            body_by_node[name] = body

        snipped = "*(message too long, skipped)*"
        space_left = 6000 - len(ctx.origin_message.content)
        for name, body in body_by_node.items():
            space_left -= len(name) + len(snipped)

        for name, body in sorted(body_by_node.items(), key=lambda it: len(it[1])):
            space_left += len(snipped)
            if len(body) <= space_left:
                space_left -= len(body)
            else:
                body_by_node[name] = snipped

        for name, body in body_by_node.items():
            embeds.append(discord.Embed(
                title=name,
                description=body,
            ))

        logging.info("Updating visible nodes of %s: %s", area.name, str(ctx.selected_options))
        await ctx.edit_origin(
            embeds=embeds,
        )


def setup(bot: RandovaniaBot):
    bot.add_cog(DatabaseCommandCog(bot.configuration, bot))
