import json
import logging
import re
import time
import sys
import os
from enum import Enum

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

ASYNC_RACE_PLAY_TIME_LIMIT_M = 60*5     # players have 4 hours max to beat the seed
ASYNC_RACE_SUBMIT_TIME_LIMIT_M = 30     # players have RTA + 30min to submit their time once finishing a seed to avoid DQ
ASYNC_RACE_SUBMIT_VOD_TIME_LIMIT_M = 90 # players have 90min after submitting their time to submit a link to a private VOD to avoid DQ

class AsyncRacerState(Enum):
    NOT_STARTED = 0
    RACING = 1
    SUBMITTED_TIME = 2
    SUBMITTED_VOD = 3
    DNF = 4

def async_race_state_to_string(x):
    if x == AsyncRacerState.NOT_STARTED:
        return "NOT_STARTED"
    elif x == AsyncRacerState.RACING:
        return "RACING"
    elif x == AsyncRacerState.SUBMITTED_TIME:
        return "SUBMITTED_TIME"
    elif x == AsyncRacerState.SUBMITTED_VOD:
        return "SUBMITTED_VOD"
    elif x == AsyncRacerState.DNF:
        return "DNF"

    raise Exception

def async_race_state_from_string(x):
    x = x.upper()
    for state in AsyncRacerState:
        if async_race_state_to_string(state) == x:
            return state
    raise Exception

ASYNC_RACE_USAGE = """*Sorry, I didn't understand that command.*

**Racer Usage**
```json
!asyncrace play <race_name>
// Start your side of an async race. Make sure you are ready before sending this command.
```
"""

ASYNC_RACE_USAGE_ADMIN = ASYNC_RACE_USAGE + """
**Admin Usage**
```json
!asyncrace list
// Lists all active races.

!asyncrace list <race_name>
// Lists the status of all participants in the specified race (restricted to #async-race-admin channel).

!asyncrace new <race_name> <permalink>
// Starts an empty race using the specified permalink.

!asyncrace add <race_name> <username1#1234> <username2#1234> ... 
// Adds the list of users to the specified race. This means that they have permission to use the "!asyncrace play" command.

!asyncrace remove <race_name> <username#1234> 
// Removes the user from th specified race.

!asyncrace reset_player <race_name> <username#1234>
// Gives the specified player a 2nd chance to complete a run in the specified race.

!asyncrace turnover <race_name> <permalink>
// Starts a new race with the same name and racers, but with a new permalink. Also announces the previous race's outcome in the results channel.

!asyncrace turnover_silent <race_name> <permalink>
// Same as above, but does not announce the outcome in results channel.

!asyncrace end <race_name>
// Ends the race and announces the outcome in the results channel.

!asyncrace end_silent <race_name>
// Ends the race without announcing the outcome.
```
"""

ASYNC_RACE_DM_USAGE = """*Sorry, I didn't understand that. Please use one of the following commands:*
```json
!finish hh::mm::ss
// Let the bot know you finished your run by submitting the RTA time. This cannot be undone.

!dnf
// Let the bot know you did not finish your run. This cannot be undone.

!vod <url>
// Submit an UNLISTED YouTube video of your run. This cannot be undone.
```
"""

ASYNC_RACE_PLAY_MESSAGE = """
**Hello Racer!**

*Please read the following carefully.*

You have limited time to record and play the seed included below. You have %d minutes from the sending of this message to setup your game, setup your recording software, and start a run. Upon completion of your seed, immediately return here to submit your time.

Your run may be be disqualified and async runner privelages may be restricted if you do any of the following:
    - Fail to submit your run in the allotted timeframe (DNF is fine, but the run still must be submitted)
    - Livestream your run
    - Upload your run publically
    - Share the permalink with anyone
    - Discuss or spoil the seed with anyone
    - Share your time with anyone

Once the race outcome is posted in `#async-racing-results`, the above restrictions no longer apply.

If you completed your run, submit your **RTA** time like so:
```
!finish 1:36:55
```

If you failed to complete your run, register as `DNF` like so:
```
!dnf
```

After sumbitting your time, you will have %d minutes to upload an unlisted YouTube video of your run.

Note that submission will automatically close after %d minutes.

Good Luck!

""" % (ASYNC_RACE_SUBMIT_TIME_LIMIT_M, ASYNC_RACE_SUBMIT_VOD_TIME_LIMIT_M, ASYNC_RACE_PLAY_TIME_LIMIT_M)

ASYNC_RACE_FINISH_MESSAGE = """Congratulations on completing your run in %s!

You now have %d minutes to upload an **UNLISTED** YouTube video of your run and submit the url here.

When you are ready, please submit the link like so:

```
!vod https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

"""

ASYNC_RACE_DATA_FILENAME = "async_race_data.json"

class AsyncRace:
    players = list()
    name = ""
    permalink = ""

    def __init__(self, name, permalink):
        self.name = name
        self.permalink = permalink
    
    def add_player(self, username):
        self.players.append(AsyncRacePlayer(username))
    
    def turnover(self, permalink):
        players = self.players
        self.players = list()
        for player in players:
            self.add_player(player.username)
            
        self.permalink = permalink
    
    def to_json(self):
        players = list()
        for player in self.players:
            players.append({
                "username":player.username,
                "state":async_race_state_to_string(player.state),
                "time":player.time,
                "vod_url":player.vod_url,
                "play_timestamp":player.play_timestamp,
                "time_timestamp":player.time_timestamp,
                "vod_timestamp":player.vod_timestamp,
            })

        race = {
            "name" : self.name,
            "permalink" : self.permalink,
            "players" : players
        }

        return json.dumps(race)

    @staticmethod
    def from_json(json_data):
        race = AsyncRace(json_data["name"], json_data["permalink"])
        for player_json in json_data["players"]:
            player = AsyncRacePlayer(player_json["username"])
            player.state = async_race_state_from_string(player_json["state"])
            player.time = player_json["time"]
            player.vod_url = player_json["vod_url"]
            player.play_timestamp = player_json["play_timestamp"]
            player.time_timestamp = player_json["time_timestamp"]
            player.vod_timestamp = player_json["vod_timestamp"]
            race.players.append(player)
        return race

class AsyncRacePlayer:
    username = ""
    state = AsyncRacerState.NOT_STARTED
    vod_url = ""
    play_timestamp = 0
    time_timestamp = 0
    vod_timestamp = 0
    time = 0 # race time in seconds

    def __init__(self, username):
        self.username = username
        self.state = AsyncRacerState.NOT_STARTED
        self.play_timestamp = 0
        self.time_timestamp = 0
        self.vod_timestamp = 0
        self.vod_url = ""
        self.time = 0

    def reset(self):
        self.__init__(self.username)

async_races = list()

def async_race_idx_from_name(name):
    i = 0
    for race in async_races:
        if race.name.lower() == name.lower():
            return i
        i = i + 1
    return None

def async_player_idx_from_name(idx, name):
    name = name.lower()
    i = 0
    for player in async_races[idx].players:
        if player.username.lower() == name:
            return i
        i = i + 1
    return None

def async_race_usage(is_async_race_admin):
    if is_async_race_admin:
        return ASYNC_RACE_USAGE_ADMIN
    return ASYNC_RACE_USAGE

def async_race_get_active_player(player_name):
    race_idx = 0
    for race in async_races:
        player_idx = 0
        for player in race.players:
            if player.username == player_name and (player.state == AsyncRacerState.RACING or player.state == AsyncRacerState.SUBMITTED_TIME):
                return (race_idx, player_idx)
            player_idx = player_idx + 1
        race_idx = race_idx + 1
    return (None, None)

def async_race_string_to_time(string):
    try:
        string = string.split(":")
        return int(string[0])*60*60 + int(string[1])*60 + int(string[2])
    except Exception:
        return None

def format_seconds_to_hhmmss(seconds):
    hours = seconds // (60*60)
    seconds %= (60*60)
    minutes = seconds // 60
    seconds %= 60
    return "%02i:%02i:%02i" % (hours, minutes, seconds)

def results_sort(x: AsyncRacePlayer):
    return x.time

async_racing_results_channel = None
async def async_race_announce_results(race):
    global async_racing_results_channel

    if len(race.players) == 0:
        return

    # sort by time
    players = sorted(race.players, key=results_sort, reverse=True)
    
    title = "%s Results" % race.name
    embed = discord.Embed(title=title, description="Thanks for playing!", color=0x00ff00)
    for player in players:
        time = "DNF"
        if player.time != DNF and player.time != 0:
            time = format_seconds_to_hhmmss(player.time)

        name = player.username.split("#")[0]
        if player.vod_url != "":
            vod = "[%s](%s)" % (time, player.vod_url)
        else:
            vod = "DNF"

        embed.add_field(name=name, value=vod, inline=False)
    await async_racing_results_channel.send(embed=embed)

async_racing_admin_channel = None
async def async_race_admin_msg(msg):
    global async_racing_admin_channel
    await async_racing_admin_channel.send(msg)

DNF = 99999999999
async_race_admin_roll_id = None
def async_race_admin_ping():
    return "<@&%d>" % async_race_admin_roll_id

async def async_race_cmd(message: discord.Message, guild):
    global async_races
    global async_race_admin_roll_id
    content = message.content.lower()
    author_name = message.author.name + "#" + message.author.discriminator
    if not content.startswith("!"):
        return

    # handle DMs to the bot
    if message.guild is None:
        try:
            (race_idx, player_idx) = async_race_get_active_player(author_name)
            if race_idx is None:
                await message.author.send("*You aren't in any active race currently.*")
                return
            
            race_name = async_races[race_idx].name
            player_name = author_name
            
            state = async_races[race_idx].players[player_idx].state
            command = content.split(" ")

            if async_races[race_idx].players[player_idx].vod_url != "":
                await message.author.send("*Your race is complete. Please wait for results to be announced in #async-racing-results before discussing the seed.*")
                return

            if command[0] == "!finish":
                if state == AsyncRacerState.RACING:
                    t = async_race_string_to_time(command[1])
                    async_races[race_idx].players[player_idx].state = AsyncRacerState.SUBMITTED_TIME
                    async_races[race_idx].players[player_idx].time = t
                    async_races[race_idx].players[player_idx].time_timestamp = time.time()
                    time_diff = async_races[race_idx].players[player_idx].time_timestamp - async_races[race_idx].players[player_idx].play_timestamp
                    await message.author.send(ASYNC_RACE_FINISH_MESSAGE % (format_seconds_to_hhmmss(t), ASYNC_RACE_SUBMIT_VOD_TIME_LIMIT_M))
                    if time_diff > ASYNC_RACE_PLAY_TIME_LIMIT_M*60 + t:
                        await message.author.send("**Warning: You have submitted your time %d minutes late. While this does not automatically disqualify your run, the race organizer has been notified of this infraction.**" % (time_diff - ASYNC_RACE_PLAY_TIME_LIMIT_M*60 + t))
                        await async_race_admin_msg("%s, *%s finished their run of '%s' in ||%s||, but they submitted the time %s late!*" % (async_race_admin_ping(), player_name, race_name, format_seconds_to_hhmmss(t), (time_diff - ASYNC_RACE_PLAY_TIME_LIMIT_M*60 + t)))
                    else:
                        await async_race_admin_msg("*%s finished their run of '%s' in ||%s||.*" % (player_name, race_name, format_seconds_to_hhmmss(t)))
                else:
                    await message.author.send("*You already submitted your time for this seed. Use the `!vod <url>` command to submit your vod.*")
                    return
            elif command[0] == "!dnf":
                if state == AsyncRacerState.RACING or state == AsyncRacerState.SUBMITTED_TIME:
                    async_races[race_idx].players[player_idx].state = AsyncRacerState.SUBMITTED_TIME
                    async_races[race_idx].players[player_idx].time = DNF
                    async_races[race_idx].players[player_idx].time_timestamp = time.time()
                    await message.author.send("*Thanks for letting me know. You are highly encouraged to still upload and submit a vod of your failed run using the `!vod <url>` command. Multiple DNFs without video proof can look like cheating.*")
                    await async_race_admin_msg("*%s forfeit their run of '%s'.*" % (player_name, race_name))
                else:
                    raise Exception
            elif command[0] == "!vod":
                if state != AsyncRacerState.SUBMITTED_TIME:
                    await message.author.send("*Please submit your time first with the `!finish hh:mm:ss` commands.*")
                    return
                else:
                    vod_url = message.content.split(" ")[1] # this is case sensitive because youtube links are case sensitive
                    if async_races[race_idx].players[player_idx].time == DNF:
                        async_races[race_idx].players[player_idx].state = AsyncRacerState.DNF
                    else:
                        async_races[race_idx].players[player_idx].state = AsyncRacerState.SUBMITTED_VOD
                    async_races[race_idx].players[player_idx].vod_url = vod_url
                    async_races[race_idx].players[player_idx].vod_timestamp = time.time()
                    time_diff = async_races[race_idx].players[player_idx].vod_timestamp - async_races[race_idx].players[player_idx].time_timestamp
                    await message.author.send("*Your run has been recorded. Please wait for results to be announced in #async-racing-results before discussing the seed or making your VOD public.*")
                    if time_diff > ASYNC_RACE_SUBMIT_VOD_TIME_LIMIT_M*60:
                        await message.author.send("**Warning: You have submitted your VOD %d minutes late. While this does not automatically disqualify your run, the race organizer has been notified of this infraction.**" % (time_diff - ASYNC_RACE_SUBMIT_VOD_TIME_LIMIT_M*60))
                        await async_race_admin_msg("*%s, %s was %d minutes late submitting their VOD for '%s'.*" % (async_race_admin_ping(), player_name, time_diff - ASYNC_RACE_SUBMIT_VOD_TIME_LIMIT_M*60, race_name))
                    else: 
                        await async_race_admin_msg("*%s submitted the vod of their run for '%s':*\n`%s`" % (player_name, race_name, vod_url))
                
                is_race_done = True
                for player in async_races[race_idx].players:
                    if player.vod_url == "":
                        is_race_done = False
                        break
                if is_race_done:
                    await async_race_admin_msg("*%s, All racers in '%s' have completed their run. Close submissions and announce results with `!asyncrace end %s`, or announce results and start a new race with the same players using `!asyncrace turnover %s <permalink>`*" % (async_race_admin_ping(), race_name, race_name, race_name))
            else:
                raise Exception
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            print(e)
            await message.author.send(ASYNC_RACE_DM_USAGE)
            return
    # handle server messages to the bot
    else:
        if message.guild.id != guild:
            return

        if not content.startswith("!asyncrace"):
            return

        channel = message.channel
        is_async_race_admin = async_race_admin_roll_id in [role.id for role in message.author.roles]
        command = content.split(" ")[1:]
        if len(command) == 0:
            await channel.send(async_race_usage(is_async_race_admin))
            return

        try:
            race_name = None
            if len(command) >= 2:
                race_name = command[1]

            if command[0] == "play":
                race_name = command[1]
                player_name = author_name.lower()
                race_idx = async_race_idx_from_name(race_name)
                if race_idx is None:
                    await channel.send("*No race with the name '%s' exists.*" % race_name)
                    return
                
                player_idx = async_player_idx_from_name(race_idx, player_name)
                if player_idx is None:
                    await channel.send("*You do not have permission to participate in '%s'. Please contact this race's organizer for more information.*" % race_name)
                    await async_race_admin_msg("*%s tried to play in '%s', but is not a member of that race.*" % (player_name, race_name))
                    return

                # check for other unfinished races 
                i = 0
                for race in async_races:
                    if i != race_idx:
                        for player in race.players:
                            if player.username == player_name and (player.state == AsyncRacerState.RACING or player.state == AsyncRacerState.SUBMITTED_TIME):
                                await channel.send("*You have an unfinished race for '%s'! Go do that first!*" % race.name)
                                return
                    i = i + 1
                
                state = async_races[race_idx].players[player_idx].state
                if state == AsyncRacerState.NOT_STARTED:
                    await channel.send("*Starting your race... Please check your DMs.*")
                elif state == AsyncRacerState.RACING or state == AsyncRacerState.SUBMITTED_TIME:
                    await channel.send("*You are supposed to be racing right now. Please check your DMs for a message from the bot, if you do not see a DM, please contact the race organizer ASAP to avoid penalization.*")
                    return
                elif state == AsyncRacerState.SUBMITTED_VOD:
                    await channel.send("*You already completed this seed! Good job!. Please wait for results to be posted in #async-racing-results.*")
                    return
                elif state == AsyncRacerState.DNF:
                    await channel.send("*You already had a chance to complete this seed, and did not finish. If this was unintentional, please contact the race organizer for more information.*")
                    return

                await message.author.send(ASYNC_RACE_PLAY_MESSAGE + "\n**Permalink** - ||%s||" % async_races[race_idx].permalink)
                async_races[race_idx].players[player_idx].play_timestamp = time.time()
                async_races[race_idx].players[player_idx].state = AsyncRacerState.RACING

                await async_race_admin_msg("*%s started their run for '%s'.*" % (player_name, race_name))

            elif command[0] == "list":
                out_message = ""
                if race_name == None:
                    if len(async_races) == 0:
                        out_message = "*There are no active races.*"
                    else:
                        out_message = "*There are %d active race(s):*```" % len(async_races)
                        for race in async_races:
                            out_message = out_message + "\n    %s - %d racer(s)" % (race.name, len(race.players))
                        out_message = out_message + "```"
                else:
                    idx = async_race_idx_from_name(race_name)
                    if idx is None:
                        await channel.send("*No race with the name '%s' exists.*" % race_name)
                        return
                    race = async_races[idx]
                    out_message = "*'%s' has %d racer(s):*" % (race_name, len(race.players))
                    out_message = out_message + "\nPermalink - ||%s||" % race.permalink
                    for player in race.players:
                        out_message = out_message + "\n    %s - %s" % (player.username, async_race_state_to_string(player.state))
                await channel.send(out_message)

                return # don't update disk because nothing changed
            elif command[0] == "new":
                # check for existing races with this name
                race_name = command[1]
                permalink = command[2]
                if not async_race_idx_from_name(race_name) is None:
                    await channel.send("*A race with the name '%s' already exists.*" % race_name)
                    return
                
                # add to races list
                async_races.append(AsyncRace(race_name, permalink))
                
                await channel.send("*Successfully added race '%s'. Add players with `!asyncrace add`.*" % race_name)

            elif command[0] == "add":
                race_name = command[1]
                idx = async_race_idx_from_name(race_name)
                if idx is None:
                    await channel.send("*No race with the name '%s' exists.*" % race_name)
                    return

                racers = command[2:]
                # check if all names are valid discord handle
                for racer in racers:
                    if racer[-1].isnumeric() and racer[-2].isnumeric() and racer[-3].isnumeric() and racer[-4].isnumeric() and racer[-5] == '#':
                        pass
                    else:
                        await channel.send("*Racer name must be valid discord name (e.g. toasterparty#9244).*")
                        return
                    
                    if not async_player_idx_from_name(idx, racer) is None:
                        await channel.send("*Racer %s is already part of '%s'.*" % (racer, race_name))
                        return
                
                for racer in racers:
                    async_races[idx].add_player(racer)

                await channel.send("*Successfully added %d racer(s) to '%s'.*" % (len(racers), race_name))

            elif command[0] == "remove":
                race_name = command[1]
                player_name = command[2]
                race_idx = async_race_idx_from_name(race_name)
                if race_idx is None:
                    await channel.send("*No race with the name '%s' exists.*" % race_name)
                    return
                
                player_idx = async_player_idx_from_name(race_idx, player_name)
                if player_idx is None:
                    await channel.send("*Player %s does not exist in '%s'.*" % (player_name, race_name))
                    return
                
                del async_races[race_idx].players[player_idx]

                await channel.send("*Successfully removed %s from '%s'*" % (player_name, race_name))

            elif command[0] == "reset_player":
                race_name = command[1]
                player_name = command[2]
                race_idx = async_race_idx_from_name(race_name)
                if race_idx is None:
                    await channel.send("*No race with the name '%s' exists.*" % race_name)
                    return

                player_idx = async_player_idx_from_name(race_idx, player_name)

                if player_idx is None:
                    await channel.send("*Player %s does not exist in '%s'.*" % (player_name, race_name))
                    return
                
                async_races[race_idx].players[player_idx].reset()

                await channel.send("*Successfully reset %s's race state in '%s'.*" % (player_name, race_name))

            elif command[0] == "turnover" or command[0] == "turnover_silent":
                race_name = command[1]
                permalink = command[2]
                race_idx = async_race_idx_from_name(race_name)
                if race_idx is None:
                    await channel.send("*No race with the name '%s' exists.*" % race_name)
                    return
                
                if command[0] == "turnover":
                    await async_race_announce_results(async_races[race_idx])

                async_races[race_idx].turnover(permalink)      
                await channel.send("*Successfully updated '%s'. Players may now play the new seed with `!asyncrace add`.*" % race_name)
            elif command[0] == "end" or command[0] == "end_silent":
                race_name = command[1]
                race_idx = async_race_idx_from_name(race_name)
                if race_idx is None:
                    await channel.send("*No race with the name '%s' exists.*" % race_name)
                    return
                
                if command[0] == "end":
                    await async_race_announce_results(async_races[race_idx])

                del async_races[race_idx]

                await channel.send("*Successfully ended '%s'.*" % race_name)
            else:
                raise Exception
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno, e)
            await channel.send(async_race_usage(is_async_race_admin))
            return # don't update disk because nothing changed
    # end guild handling

    # Update race states on disk
    with open(ASYNC_RACE_DATA_FILENAME, "w") as f:
        d = "["
        first = True
        for race in async_races:
            if not first:
                d = d + ","
            d = d + race.to_json()
            if first:
                first = False
        d = d + "]"
        f.write(d)

class Bot(discord.Client):
    def __init__(self, configuration: dict):
        global async_race_admin_roll_id
        super().__init__()
        self.configuration = configuration
        async_race_admin_roll_id = self.configuration["async_racing_admin_roll_id"]

    async def on_message(self, message: discord.Message):
        global async_racing_admin_channel
        global async_racing_results_channel
        if async_racing_admin_channel is None:
            async_racing_admin_channel = self.get_channel(self.configuration["async_racing_admin_channel_id"])
        if async_racing_results_channel is None:
            async_racing_results_channel = self.get_channel(self.configuration["async_racing_results_channel_id"])

        if message.author == self.user:
            return

        await async_race_cmd(message, self.configuration["guild"])

        if message.guild is None:
            return # message is a dm to the bot

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
    # read state from disk if it exists
    global async_races
    try:
        if os.path.exists(ASYNC_RACE_DATA_FILENAME):
            with open(ASYNC_RACE_DATA_FILENAME, "r") as f:
                json_string = f.read()
                races = json.loads(json_string)
                for race in races:
                    async_races.append(AsyncRace.from_json(race))
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        async_races = list()
        print(exc_type, fname, exc_tb.tb_lineno)
        print(e)

    configuration = randovania.get_configuration()["discord_bot"]

    client = Bot(configuration)
    client.run(configuration["token"])
