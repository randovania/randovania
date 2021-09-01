import functools
import math
from typing import List, Tuple, Dict

from discord import Embed
from discord.ext import commands
from discord_slash import SlashCommand, SlashContext, SlashCommandOptionType, ComponentContext, ButtonStyle
from discord_slash.utils import manage_commands, manage_components

from randovania.game_description import default_database, pretty_print
from randovania.game_description.game_description import GameDescription
from randovania.game_description.world.area import Area
from randovania.game_description.world.world import World
from randovania.games.game import RandovaniaGame
from randovania.lib import enum_lib
from randovania.server.discord.bot import RandovaniaBot

SplitWorld = Tuple[World, str, List[Area]]


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

                    world_options.append((world, "{} ({}-{})".format(name, areas_part[0].name[:2],
                                                                     areas_part[-1].name[:2]), areas_part))
            else:
                world_options.append((world, name, areas))

    world_options.sort(key=lambda it: it[1])
    return world_options


class DatabaseCommandCog(commands.Cog):
    _split_worlds: Dict[RandovaniaGame, List[SplitWorld]]

    def __init__(self, configuration: dict, bot: commands.Bot):
        self.configuration = configuration
        self.slash = SlashCommand(bot)
        self._split_worlds = {}
        self._on_database_component_listener = {}

    @commands.Cog.listener()
    async def on_ready(self):
        self.slash.add_slash_command(
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
                add_id(f"{game.value}_world_{i}", self.on_database_area_selected, game=game, split_world=split_world)

        self.slash.add_component_callback(
            self.on_database_component,
            components=list(self._on_database_component_listener.keys()),
            use_callback_name=False,
        )

        await self.slash.sync_all_commands()

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
        await ctx.edit_origin(
            embed=embed,
            components=[
                action_row,
                back_row,
            ],
        )

    async def on_database_area_selected(self, ctx: ComponentContext, game: RandovaniaGame, split_world: SplitWorld):
        option_selected = ctx.selected_options[0]

        valid_items = [
            area
            for i, area in enumerate(split_world[2])
            if f"area_{i}" == option_selected
        ]
        if not valid_items:
            return await ctx.edit_origin(
                components=[], embeds=[],
                content=f"Invalid selected option, unable to find given area '{option_selected}'."
            )

        area = valid_items[0]
        db = default_database.game_description_for(game)

        rows = []

        def append(*args):
            rows.append("    ".join(args))

        pretty_print.pretty_print_area(db, area, append)
        rows.pop(0)
        rows.pop(0)
        await ctx.send(
            embed=Embed(title=db.world_list.area_name(area),
                        description="```\n{}\n```".format("\n".join(rows))),
        )


def setup(bot: RandovaniaBot):
    bot.add_cog(DatabaseCommandCog(bot.configuration, bot))
