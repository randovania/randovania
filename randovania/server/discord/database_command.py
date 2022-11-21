import dataclasses
import io
import logging
import math
import shutil
import tempfile
from pathlib import Path

import PIL.Image
import discord
import graphviz
from PIL import ImageDraw
from discord import Embed
from discord.ext.commands import Converter, Context

from randovania.game_description import default_database, pretty_print
from randovania.game_description.game_description import GameDescription
from randovania.game_description.world.area import Area
from randovania.game_description.world.node import NodeLocation, Node
from randovania.game_description.world.world import World
from randovania.games.game import RandovaniaGame
from randovania.lib import enum_lib
from randovania.server.discord.bot import RandovaniaBot
from randovania.server.discord.randovania_cog import RandovaniaCog


@dataclasses.dataclass()
class AreaWidget:
    area: Area
    command_id: str
    view: discord.ui.View = None


@dataclasses.dataclass()
class SplitWorld:
    world: World
    name: str
    areas: list[AreaWidget]
    command_id: str
    view: discord.ui.View = None


def render_area_with_graphviz(area: Area) -> io.BytesIO | None:
    dot = graphviz.Digraph(comment=area.name)
    for node in area.nodes:
        if node.is_derived_node:
            continue
        dot.node(node.name)

    known_edges = set()
    for source, target in area.connections.items():
        if source.is_derived_node:
            continue

        for target_node, requirement in target.items():
            if target_node.is_derived_node:
                continue

            direction = None
            if source in area.connections.get(target_node):
                direction = "both"
                known_edges.add((target_node.name, source.name))

            if (source.name, target_node.name) not in known_edges:
                dot.edge(source.name, target_node.name, dir=direction)
                known_edges.add((source.name, target_node.name))

    output_dir = tempfile.mkdtemp()
    try:
        p = Path(dot.render(directory=output_dir, format="png", cleanup=True))
        return io.BytesIO(p.read_bytes())

    except graphviz.backend.ExecutableNotFound as e:
        logging.info("Unable to render graph for %s: %s", area.name, str(e))
        return None
    finally:
        shutil.rmtree(output_dir)


def render_area_with_pillow(area: Area, data_path: Path) -> io.BytesIO | None:
    image_path = data_path.joinpath("assets", "maps", f"{area.map_name}.png")
    if not image_path.exists():
        return None

    with PIL.Image.open(image_path) as im:
        assert isinstance(im, PIL.Image.Image)

        def location_to_pos(loc: NodeLocation):
            return loc.x, im.height - loc.y

        draw = ImageDraw.Draw(im)

        def draw_connections_from(source_node: Node):
            for target_node, requirement in area.connections[source_node].items():
                if target_node.is_derived_node:
                    continue

                source = location_to_pos(source_node.location)
                target = location_to_pos(target_node.location)

                if sum((a - b) ** 2 for a, b in zip(source, target)) < 4:
                    continue

                draw.line(source + target, width=2, fill=(255, 255, 255, 255))
                draw.line(source + target, width=1, fill=(0, 0, 0, 255))

        for node in area.nodes:
            if not node.is_derived_node:
                draw_connections_from(node)

        for node in area.nodes:
            if node.location is None or node.is_derived_node:
                continue

            p = location_to_pos(node.location)
            draw.ellipse((p[0] - 5, p[1] - 5, p[0] + 5, p[1] + 5), fill=(255, 255, 255, 255), width=5)
            draw.ellipse((p[0] - 5, p[1] - 5, p[0] + 5, p[1] + 5), fill=(0, 0, 0, 255), width=4)
            draw.text((p[0] - draw.textlength(node.name) / 2, p[1] + 15), node.name, stroke_width=2,
                      stroke_fill=(255, 255, 255, 255))
            draw.text((p[0] - draw.textlength(node.name) / 2, p[1] + 15), node.name, stroke_width=1,
                      stroke_fill=(0, 0, 0, 255))

        result = io.BytesIO()
        im.save(result, "PNG")

    result.seek(0)
    return result


async def create_split_worlds(db: GameDescription) -> list[SplitWorld]:
    world_options = []

    def create_id():
        return f"{db.game.value}_world_{len(world_options)}"

    def create_areas(a):
        return [
            AreaWidget(
                it, f"{create_id()}_area_{i}"
            )
            for i, it in enumerate(a)
        ]

    for world in db.world_list.worlds:
        for is_dark_world in [False, True]:
            if is_dark_world and world.dark_name is None:
                continue

            areas = sorted(
                (
                    area for area in world.areas
                    if area.in_dark_aether == is_dark_world and area.nodes
                ),
                key=lambda it: it.name,
            )
            name = world.correct_name(is_dark_world)
            if len(areas) > 25:
                per_part = math.ceil(len(areas) / math.ceil(len(areas) / 25))

                while areas:
                    areas_part = areas[:per_part]
                    del areas[:per_part]

                    world_options.append(SplitWorld(
                        world, "{} ({}-{})".format(name, areas_part[0].name[:2],
                                                   areas_part[-1].name[:2]),
                        create_areas(areas_part),
                        create_id(),
                    ))
            else:
                world_options.append(SplitWorld(world, name, create_areas(areas), create_id()))

    world_options.sort(key=lambda it: it.name)
    return world_options


class EnumConverter(Converter):
    async def convert(self, ctx: Context, argument: str):
        return RandovaniaGame(argument)


_GameChoices = discord.Option(
    str,
    description="The game's database to check.",
    choices=[
        discord.OptionChoice(name=game.long_name, value=game.value)
        for game in enum_lib.iterate_enum(RandovaniaGame)
    ]
)
_GameChoices.converter = EnumConverter()
_GameChoices._raw_type = RandovaniaGame


class SelectNodesItem(discord.ui.Select):
    def __init__(self, game: RandovaniaGame, area: AreaWidget):
        self.game = game
        self.area = area

        options = [
            discord.SelectOption(label=node.name)
            for node in self.valid_nodes()
        ]

        super().__init__(
            custom_id=area.command_id,
            placeholder="Choose the nodes",
            options=options,
            max_values=min(10, len(options)),
        )

    def valid_nodes(self):
        return [node for node in sorted(self.area.area.nodes, key=lambda it: it.name)
                if not node.is_derived_node]

    def _describe_selected_connections(self, original_content: str):
        db = default_database.game_description_for(self.game)

        def snipped_message(n: str) -> str:
            return f"\n{n}: *Skipped*\n"

        body_by_node = {}
        embeds = []

        for node in sorted(self.area.area.nodes, key=lambda it: it.name):
            if node.name not in self.values:
                continue

            name = node.name
            if node.heal:
                name += " (Heals)"
            if self.area.area.default_node == node.name:
                name += "; Spawn Point"

            body = pretty_print.pretty_print_node_type(node, db.world_list) + "\n"

            node_bodies = []

            for target_node, requirement in db.world_list.area_connections_from(node):
                if target_node.is_derived_node:
                    continue

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
        space_left = 6000 - len(original_content)
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

        return embeds

    async def callback(self, interaction: discord.Interaction):
        r = interaction.response
        assert isinstance(r, discord.InteractionResponse)

        await r.defer()
        original_response = await interaction.original_response()

        try:
            embeds = self._describe_selected_connections(original_response.content)
        except Exception as e:
            logging.exception("Error updating visible nodes of %s: %s", self.area.area.name, str(self.values))
            embeds = [discord.Embed(
                title="Error describing area",
                description=str(e),
            )]

        logging.info("Updating visible nodes of %s: %s", self.area.area.name, str(self.values))
        await original_response.edit(
            embeds=embeds,
        )


class SelectAreaItem(discord.ui.Select):
    def __init__(self, game: RandovaniaGame, split_world: SplitWorld):
        self.game = game
        self.split_world = split_world

        options = [
            discord.SelectOption(
                label=area.area.name,
                value=area.command_id,
            )
            for area in split_world.areas
        ]
        super().__init__(
            custom_id=split_world.command_id,
            placeholder="Choose the room",
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        r = interaction.response
        assert isinstance(r, discord.InteractionResponse)
        option_selected = self.values[0]

        valid_items = [
            area for area in self.split_world.areas
            if area.command_id == option_selected
        ]
        if not valid_items:
            await r.defer()
            return await interaction.edit_original_response(
                view=None, embeds=[],
                content=f"Invalid selected option, unable to find given world subset '{option_selected}'."
            )
        area = valid_items[0]

        db = default_database.game_description_for(self.game)
        title = f"{self.game.long_name}: {db.world_list.area_name(area.area)}"

        files = []

        area_image = render_area_with_pillow(area.area, self.game.data_path)
        if area_image is not None:
            files.append(discord.File(area_image, filename=f"{area.area.name}_image.png"))

        area_graph = render_area_with_graphviz(area.area)
        if area_graph is not None:
            files.append(discord.File(area_graph, filename=f"{area.area.name}_graph.png"))

        logging.info("Responding to area for %s with %d attachments.", area.area.name, len(files))
        await r.send_message(
            content=f"**{title}**\nRequested by {interaction.user.display_name}.",
            files=files,
            view=area.view,
        )


class SelectSplitWorldItem(discord.ui.Select):
    def __init__(self, game: RandovaniaGame, split_worlds: list[SplitWorld]):
        self.game = game
        self.split_worlds = split_worlds

        options = [
            discord.SelectOption(label=split_world.name, value=split_world.command_id)
            for split_world in split_worlds
        ]

        super().__init__(
            custom_id=f"{game.value}_world",
            placeholder="Choose your region",
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        r = interaction.response
        assert isinstance(r, discord.InteractionResponse)

        # defer is needed to be able to edit the original message.
        await r.defer()

        option_selected = self.values[0]

        valid_items = [
            it
            for it in self.split_worlds
            if it.command_id == option_selected
        ]
        if not valid_items:
            return await interaction.edit_original_response(
                view=None, embeds=[],
                content=f"Invalid selected option, unable to find given world subset '{option_selected}'."
            )
        split_world = valid_items[0]

        embed = Embed(title=f"{self.game.long_name} Database",
                      description=f"Choose the room in {split_world.name} to visualize.")

        logging.info("Responding to area selection for section %s with %d options.",
                     split_world.name, len(split_world.areas))
        return await interaction.edit_original_response(
            embed=embed,
            view=split_world.view,
        )


class BackToGameButton(discord.ui.Button):
    def __init__(self, game: RandovaniaGame, response_view: discord.ui.View):
        self.game = game
        self.response_view = response_view

        super().__init__(
            label="Back",
            custom_id=f"back_to_{game.value}",
        )

    async def callback(self, interaction: discord.Interaction):
        # defer is needed to be able to edit the original message.
        await interaction.response.defer()
        return await interaction.edit_original_response(
            embed=Embed(title=f"{self.game.long_name} Database", description="Choose the world subset to visualize."),
            view=self.response_view,
        )


class DatabaseCommandCog(RandovaniaCog):
    _split_worlds: dict[RandovaniaGame, list[SplitWorld]]
    _select_split_world_view: dict[RandovaniaGame, discord.ui.View]

    def __init__(self, configuration: dict, bot: RandovaniaBot):
        self.configuration = configuration
        self.bot = bot
        self._split_worlds = {}
        self._select_split_world_view = {}
        self._on_database_component_listener = {}

    @discord.commands.slash_command(name="database")
    async def database_inspect(self, context: discord.ApplicationContext, game: _GameChoices):
        """Consult the Randovania's logic database for one specific room."""
        assert isinstance(game, RandovaniaGame)

        embed = Embed(title=f"{game.long_name} Database", description="Choose the world subset to visualize.")
        view = self._select_split_world_view[game]
        logging.info("Responding requesting list of worlds for game %s.", game.long_name)

        await context.respond(embed=embed, view=view, ephemeral=True)

    async def add_commands(self):
        for game in enum_lib.iterate_enum(RandovaniaGame):
            db = default_database.game_description_for(game)
            world_options = await create_split_worlds(db)
            self._split_worlds[game] = world_options

            view = discord.ui.View(
                SelectSplitWorldItem(game, world_options),
                timeout=None,
            )
            self.bot.add_view(view)
            self._select_split_world_view[game] = view

            for split_world in world_options:
                split_world.view = discord.ui.View(
                    SelectAreaItem(game, split_world),
                    BackToGameButton(game, view),
                    timeout=None,
                )
                self.bot.add_view(split_world.view)
                for area in split_world.areas:
                    area.view = discord.ui.View(
                        SelectNodesItem(game, area),
                        timeout=None,
                    )
                    self.bot.add_view(area.view)


def setup(bot: RandovaniaBot):
    bot.add_cog(DatabaseCommandCog(bot.configuration, bot))
