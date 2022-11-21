import asyncio
import base64
import io
import json
import logging
import math
import random
import re
import subprocess
import time
import typing
from typing import Callable

import discord
from discord.ui import Button

import randovania
from randovania.generator import generator
from randovania.layout import preset_describer, layout_description
from randovania.layout.generator_parameters import GeneratorParameters
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.permalink import Permalink, UnsupportedPermalink
from randovania.layout.preset import Preset
from randovania.layout.versioned_preset import VersionedPreset
from randovania.resolver.exceptions import GenerationFailure
from randovania.server.discord.bot import RandovaniaBot
from randovania.server.discord.randovania_cog import RandovaniaCog

possible_links_re = re.compile(r'([A-Za-z0-9-_]{8,})')
_MAXIMUM_PRESETS_FOR_GENERATION = 4


def _add_preset_description_to_embed(embed: discord.Embed, preset: Preset):
    for category, items in preset_describer.describe(preset):
        embed.add_field(name=category, value="\n".join(items), inline=True)


def _git_describe(randovania_version: bytes) -> str:
    return subprocess.run(
        ["git", "describe", "--tags", randovania_version.hex()],
        check=True, capture_output=True, text=True,
    ).stdout.strip()


def get_version(original_permalink: str, randovania_version: bytes) -> str | None:
    try:
        version_raw = _git_describe(randovania_version)
        version_split = version_raw.split("-")

        is_dev_version = randovania.is_dev_version()

        if len(version_split) > 1:
            # dev version
            if not is_dev_version:
                logging.info("Skipping permalink %s from dev version %s", original_permalink,
                             version_raw)
                return None

            major, minor, revision = version_split[0][1:].split(".")
            version = f"{major}.{int(minor) + 1}.0.dev{version_split[1]}"
        else:
            if is_dev_version:
                logging.info("Skipping permalink %s from stable version %s", original_permalink,
                             version_raw)
                return None
            # Exclude starting `v`
            version = version_split[0][1:]

    except FileNotFoundError:
        return f"(Unknown version: {randovania_version.hex()})"

    except subprocess.CalledProcessError as e:
        logging.info("Unable to describe permalink commit %s: %s", randovania_version.hex(), str(e))
        return None

    return version


async def look_for_permalinks(message: discord.Message):
    embed = None
    multiple_permalinks = False
    view = None

    for word in possible_links_re.finditer(message.content):
        try:
            permalink = Permalink.from_str(word.group(1))
            randovania_version = permalink.randovania_version
            games = [preset.game for preset in permalink.parameters.presets]
            seed_hash = permalink.seed_hash
            error_message = None

        except UnsupportedPermalink as e:
            permalink = None
            randovania_version = e.randovania_version
            games = e.games
            seed_hash = e.seed_hash
            error_message = f"\n\nPermalink incompatible with Randovania {randovania.VERSION}"
            if e.__cause__ is not None:
                error_message += f"\n{e.__cause__}"

        except (ValueError, UnsupportedPermalink):
            # TODO: handle the incorrect version permalink
            continue

        version = get_version(word.group(1), randovania_version)
        if version is None:
            continue

        if embed is not None:
            multiple_permalinks = True
            continue

        if seed_hash is not None:
            pretty_hash = "Seed Hash: {} ({})".format(
                layout_description.shareable_word_hash(seed_hash, games),
                base64.b32encode(seed_hash).decode(),
            )
        else:
            pretty_hash = "Unknown seed hash"

        player_count = len(games)
        embed = discord.Embed(title=f"`{word.group(1)}`",
                              description=f"{player_count} player multiworld permalink")

        if player_count == 1:
            embed.description = f"{games[0].long_name} permalink"
            if permalink is not None:
                _add_preset_description_to_embed(embed, permalink.parameters.get_preset(0))

        embed.description += f" for Randovania {version}\n{pretty_hash}"

        if permalink is not None:
            view = RequestPresetsView()
        else:
            embed.description += error_message

    if embed is not None:
        content = None
        if multiple_permalinks:
            content = "Multiple permalinks found, using only the first."
        await message.reply(content=content, embed=embed, view=view, mention_author=False)


async def reply_for_preset(message: discord.Message, versioned_preset: VersionedPreset):
    try:
        preset = versioned_preset.get_preset()
    except ValueError as e:
        logging.info("Invalid preset '{}' from {}: {}".format(versioned_preset.name,
                                                              message.author.display_name,
                                                              e))
        return

    embed = discord.Embed(title=preset.name,
                          description=preset.description)
    _add_preset_description_to_embed(embed, preset)
    await message.reply(embed=embed, mention_author=False)


async def reply_for_layout_description(message: discord.Message, description: LayoutDescription):
    embed = discord.Embed(
        title=f"Spoiler file for Randovania {description.randovania_version_text}",
    )

    if description.player_count == 1:
        preset = description.get_preset(0)
        embed.description = "{}, with preset {}.\nSeed Hash: {}\nPermalink: {}".format(
            preset.game.long_name, preset.name,
            description.shareable_word_hash,
            description.permalink.as_base64_str,
        )
        _add_preset_description_to_embed(embed, preset)
    else:
        games = {preset.game.long_name for preset in description.all_presets}
        game_names = sorted(games)

        last_game = game_names.pop()
        games_text = ", ".join(game_names)
        if games_text:
            games_text += " and "
        games_text += last_game

        embed.description = "{} player multiworld for {}.\nSeed Hash: {}\nPermalink: {}".format(
            description.player_count,
            games_text,
            description.shareable_word_hash,
            description.permalink.as_base64_str,
        )

    await message.reply(embed=embed, mention_author=False)


class RequestPresetsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Attach presets",
        style=discord.ButtonStyle.secondary,
        custom_id="attach_presets_of_permalink",
    )
    async def button_callback(self, button: Button, interaction: discord.Interaction):
        try:
            title = (await interaction.original_response()).embeds[0].title
            # Trim leading and trailing `s
            permalink = Permalink.from_str(title[1:-1])

        except (IndexError, ValueError, UnsupportedPermalink) as e:
            logging.exception("Unable to find permalink on message that sent attach_presets_of_permalink")
            permalink = None

        files = []

        if permalink is not None:
            for player, preset in enumerate(permalink.parameters.presets):
                data = io.BytesIO()
                VersionedPreset.with_preset(preset).save_to_io(data)
                data.seek(0)
                files.append(
                    discord.File(data, filename=f"Player {player + 1}'s Preset.{VersionedPreset.file_extension()}")
                )

        await interaction.edit_original_response(
            view=None,
            files=files,
        )


T = typing.TypeVar("T")


async def _try_get(message: discord.Message, attachment: discord.Attachment, decoder: Callable[[dict], T]) -> T | None:
    try:
        data = await attachment.read()
        return decoder(json.loads(data.decode("utf-8")))
    except Exception as e:
        logging.exception(f"Unable to process {attachment.filename} from {message}")
        await message.reply(
            embed=discord.Embed(
                title=f"Unable to process {attachment.filename}",
                description=str(e),
            ),
            mention_author=False
        )
        return None


async def _get_presets_from_message(message: discord.Message):
    for attachment in message.attachments:
        filename: str = attachment.filename
        if filename.endswith(VersionedPreset.file_extension()):
            result = await _try_get(message, attachment, VersionedPreset)
            if result is not None:
                yield result


async def _get_layouts_from_message(message: discord.Message):
    for attachment in message.attachments:
        filename: str = attachment.filename
        if filename.endswith(LayoutDescription.file_extension()):
            result = await _try_get(message, attachment, LayoutDescription.from_json_dict)
            if result is not None:
                yield result


class PermalinkLookupCog(RandovaniaCog):
    def __init__(self, configuration: dict, bot: RandovaniaBot):
        self.configuration = configuration
        self.bot = bot

    async def add_commands(self):
        self.bot.add_view(RequestPresetsView())

    @discord.commands.message_command(
        name="Generate new game",
        default_member_permissions=discord.Permissions(
            administrator=True,
        ),
    )
    async def generate_game(self, context: discord.ApplicationContext, message: discord.Message):
        """Generates a game with all presets in the given message."""
        presets = [preset.get_preset() async for preset in _get_presets_from_message(message)]
        if not presets:
            return await context.respond(content="No presets found in message.", ephemeral=True)

        if len(presets) > _MAXIMUM_PRESETS_FOR_GENERATION:
            return await context.respond(
                content=f"Found {len(presets)}, can only generate up to {_MAXIMUM_PRESETS_FOR_GENERATION}.",
                ephemeral=True)

        response: discord.Interaction = await context.respond(
            content=f"Generating game with {len(presets)} players...",
            ephemeral=True
        )

        content = ""
        files = []
        embeds = []
        start_time = time.time()

        try:
            layout: LayoutDescription = await asyncio.wait_for(
                generator.generate_and_validate_description(
                    generator_params=GeneratorParameters(
                        seed_number=random.randint(0, 2 ** 31),
                        spoiler=True,
                        presets=presets,
                    ),
                    status_update=None,
                    validate_after_generation=False,
                    timeout=60
                ),
                timeout=60,
            )
            content = f"Hash: {layout.shareable_word_hash}. Generated in "
            files = [
                discord.File(
                    io.BytesIO(json.dumps(layout.as_json(), indent=4, separators=(',', ': ')).encode("utf-8")),
                    filename=f"{layout.shareable_word_hash}.{LayoutDescription.file_extension()}"
                )
            ]
        except GenerationFailure as e:
            embeds = [discord.Embed(
                title="Unable to generate a game",
                description=str(e.source),
            )]
        except asyncio.TimeoutError:
            content = "Timeout after "
        except Exception as e:
            return await response.edit_original_response(
                content=f"Unexpected error when generating: {e} ({type(e)})",
            )

        delta = time.time() - start_time
        delta_str = f"{math.floor(delta)} seconds."
        if content:
            content += delta_str
        else:
            content += f"Took {delta_str}"

        try:
            await message.reply(
                content=f"{content}\nRequested by {context.user.display_name}.",
                files=files, embeds=embeds, mention_author=False)
        except discord.errors.Forbidden:
            return await response.edit_original_response(content=content, files=files, embeds=embeds)

    @discord.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return

        async for preset in _get_presets_from_message(message):
            await reply_for_preset(message, preset)

        async for description in _get_layouts_from_message(message):
            await reply_for_layout_description(message, description)

        await look_for_permalinks(message)


def setup(bot: RandovaniaBot):
    bot.add_cog(PermalinkLookupCog(bot.configuration, bot))
