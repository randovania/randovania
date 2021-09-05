import json
import logging
import re

import discord
from discord.ext import commands

import randovania
from randovania.gui.lib import preset_describer
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.permalink import Permalink
from randovania.layout.preset_migration import VersionedPreset
from randovania.server.discord.bot import RandovaniaBot

possible_links_re = re.compile(r'([A-Za-z0-9-_]{8,})')


async def look_for_permalinks(message: discord.Message):
    embed = None
    multiple_permalinks = False

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
            for category, items in preset_describer.describe(preset):
                embed.add_field(name=category, value="\n".join(items), inline=True)

    if embed is not None:
        content = None
        if multiple_permalinks:
            content = "Multiple permalinks found, using only the first."
        await message.reply(content=content, embed=embed, mention_author=False)


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
    for category, items in preset_describer.describe(preset):
        embed.add_field(name=category, value="\n".join(items), inline=True)
    await message.reply(embed=embed, mention_author=False)


async def reply_for_layout_description(message: discord.Message, description: LayoutDescription):
    embed = discord.Embed(
        title="Spoiler file for Randovania {}".format(description.version),
    )

    if description.permalink.player_count == 1:
        preset = description.get_preset(0)
        embed.description = "{}, with preset {}".format(preset.game.long_name, preset.name)
        for category, items in preset_describer.describe(preset):
            embed.add_field(name=category, value="\n".join(items), inline=True)
    else:
        games = {preset.game.long_name for preset in description.permalink.presets.values()}
        game_names = sorted(games)

        last_game = game_names.pop()
        games_text = ", ".join(game_names)
        if games_text:
            games_text += " and "
        games_text += last_game

        embed.description = "{} player multiworld for {}".format(
            description.permalink.player_count,
            games_text,
        )

    await message.reply(embed=embed, mention_author=False)


class PermalinkLookupCog(commands.Cog):
    def __init__(self, configuration: dict, bot: commands.Bot):
        self.configuration = configuration
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return

        if message.guild.id != self.configuration["guild"]:
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

        channel: discord.TextChannel = message.channel
        if self.configuration["channel_name_filter"] in channel.name:
            await look_for_permalinks(message)


def setup(bot: RandovaniaBot):
    bot.add_cog(PermalinkLookupCog(bot.configuration, bot))
