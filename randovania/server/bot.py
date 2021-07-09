import json
import logging
import re

import discord

import randovania
from randovania.games.game import RandovaniaGame
from randovania.gui.lib import preset_describer
from randovania.layout.permalink import Permalink
from randovania.layout.preset_migration import VersionedPreset

_PRETTY_GAME_NAME = {
    RandovaniaGame.METROID_PRIME: "Metroid Prime 1",
    RandovaniaGame.METROID_PRIME_ECHOES: "Metroid Prime 2: Echoes",
    RandovaniaGame.METROID_PRIME_CORRUPTION: "Metroid Prime 3: Corruption",
}
possible_links_re = re.compile(r'([A-Za-z0-9-_]{8,})')


async def look_for_permalinks(message: str, channel: discord.TextChannel):
    for word in possible_links_re.finditer(message):
        try:
            permalink = Permalink.from_str(word.group(1))
        except ValueError:
            continue

        embed = discord.Embed(title=word.group(1),
                              description="{} player multiworld permalink".format(permalink.player_count))

        if permalink.player_count == 1:
            preset = permalink.get_preset(0)
            embed.description = "{} permalink for Randovania {}".format(_PRETTY_GAME_NAME[preset.game],
                                                                        randovania.VERSION)
            for category, items in preset_describer.describe(preset):
                embed.add_field(name=category, value="\n".join(items), inline=True)

        await channel.send(embed=embed)


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
    await message.reply(embed=embed)


class Bot(discord.Client):
    def __init__(self, configuration: dict):
        super().__init__()
        self.configuration = configuration

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return

        if message.guild.id != self.configuration["guild"]:
            return

        for attachment in message.attachments:
            filename: str = attachment.filename
            if filename.endswith(VersionedPreset.file_extension()):
                data = await attachment.read()
                versioned_preset = VersionedPreset(json.loads(data.decode("utf-8")))
                await reply_for_preset(message, versioned_preset)

        channel: discord.TextChannel = message.channel
        if self.configuration["channel_name_filter"] in channel.name:
            await look_for_permalinks(message.content, channel)


def run():
    configuration = randovania.get_configuration()["discord_bot"]

    client = Bot(configuration)
    client.run(configuration["token"])
