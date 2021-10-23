import io
import json
import logging
import re

import discord
from discord.ext import commands
from discord_slash import ComponentContext, ButtonStyle
from discord_slash.utils import manage_components

import randovania
from randovania.gui.lib import preset_describer
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.permalink import Permalink
from randovania.layout.preset import Preset
from randovania.layout.preset_migration import VersionedPreset
from randovania.server.discord.bot import RandovaniaBot

possible_links_re = re.compile(r'([A-Za-z0-9-_]{8,})')


def _add_preset_description_to_embed(embed: discord.Embed, preset: Preset):
    for category, items in preset_describer.describe(preset):
        embed.add_field(name=category, value="\n".join(items), inline=True)


async def look_for_permalinks(message: discord.Message):
    embed = None
    multiple_permalinks = False
    components = []

    for word in possible_links_re.finditer(message.content):
        try:
            permalink = Permalink.from_str(word.group(1))
        except ValueError:
            continue

        if embed is not None:
            multiple_permalinks = True
            continue

        embed = discord.Embed(title=f"`{word.group(1)}`",
                              description="{} player multiworld permalink".format(permalink.player_count))

        if permalink.player_count == 1:
            preset = permalink.get_preset(0)
            embed.description = "{} permalink for Randovania {}".format(preset.game.long_name,
                                                                        randovania.VERSION)
            _add_preset_description_to_embed(embed, preset)

        components.append(manage_components.create_actionrow(manage_components.create_button(
            style=ButtonStyle.secondary,
            label="Attach presets",
            custom_id="attach_presets_of_permalink",
        )))

    if embed is not None:
        content = None
        if multiple_permalinks:
            content = "Multiple permalinks found, using only the first."
        await message.reply(content=content, embed=embed, components=components, mention_author=False)


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
        title="Spoiler file for Randovania {}".format(description.version),
    )

    if description.permalink.player_count == 1:
        preset = description.get_preset(0)
        embed.description = "{}, with preset {}".format(preset.game.long_name, preset.name)
        _add_preset_description_to_embed(embed, preset)
    else:
        games = {preset.game.long_name for preset in description.permalink.presets.values()}
        game_names = sorted(games)

        last_game = game_names.pop()
        games_text = ", ".join(game_names)
        if games_text:
            games_text += " and "
        games_text += last_game

        embed.description = "{} player multiworld for {}.\nSeed Hash: {}\nPermalink: {}".format(
            description.permalink.player_count,
            games_text,
            description.shareable_word_hash,
            description.permalink.as_base64_str,
        )

    await message.reply(embed=embed, mention_author=False)


class PermalinkLookupCog(commands.Cog):
    def __init__(self, configuration: dict, bot: RandovaniaBot):
        self.configuration = configuration
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.slash.add_component_callback(
            self.on_request_presets,
            components=["attach_presets_of_permalink"],
            use_callback_name=False,
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return

        if message.guild is not None and message.guild.id != self.configuration["guild"]:
            return

        for attachment in message.attachments:
            filename: str = attachment.filename
            if filename.endswith(VersionedPreset.file_extension()):
                data = await attachment.read()
                versioned_preset = VersionedPreset(json.loads(data.decode("utf-8")))
                await reply_for_preset(message, versioned_preset)

            elif filename.endswith(LayoutDescription.file_extension()):
                data = await attachment.read()
                description = LayoutDescription.from_json_dict(json.loads(data.decode("utf-8")))
                await reply_for_layout_description(message, description)

        await look_for_permalinks(message)

    async def on_request_presets(self, ctx: ComponentContext):
        try:
            title = ctx.origin_message.embeds[0].title
            # Trim leading and trailing `s
            permalink = Permalink.from_str(title[1:-1])

        except (IndexError, ValueError) as e:
            logging.exception("Unable to find permalink on message that sent attach_presets_of_permalink")
            permalink = None

        files = []

        if permalink is not None:
            for player, preset in permalink.presets.items():
                data = io.BytesIO()
                VersionedPreset.with_preset(preset).save_to_io(data)
                data.seek(0)
                files.append(
                    discord.File(data, filename=f"Player {player + 1}'s Preset.{VersionedPreset.file_extension()}")
                )

        await ctx.edit_origin(
            components=[],
            files=files,
        )


def setup(bot: RandovaniaBot):
    bot.add_cog(PermalinkLookupCog(bot.configuration, bot))
