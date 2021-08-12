import time
import sys
import os
import json
import logging
from enum import Enum

import discord

import randovania

ASYNC_RACE_SUBMIT_TIME_LIMIT_M = 30       # players have RTA + 30min to submit their time once finishing a seed to avoid DQ
ASYNC_RACE_SUBMIT_VOD_TIME_LIMIT_M = 60*4 # players have 4hr after submitting their time to submit a link to a private VOD to avoid DQ

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

    raise Exception("invalid racer state")

def async_race_state_from_string(x):
    x = x.upper()
    for state in AsyncRacerState:
        if async_race_state_to_string(state) == x:
            return state
    raise Exception("unhandled race state str")

ASYNC_RACE_USAGE = f"""*Sorry, I didn't understand that command.*

**Racer Usage**
```json
!asyncrace play <race_name>
// Start your side of an async race. Make sure you are ready before sending this command.
```
"""

ASYNC_RACE_USAGE_ADMIN =  f"""{ASYNC_RACE_USAGE}
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

ASYNC_RACE_DM_USAGE = f"""*Sorry, I didn't understand that. Please use one of the following commands:*
```json
!finish hh::mm::ss
// Let the bot know you finished your run by submitting the RTA time. This cannot be undone.

!dnf
// Let the bot know you did not finish your run. This cannot be undone.

!vod <url>
// Submit an UNLISTED YouTube video of your run. This cannot be undone.
```
"""

ASYNC_RACE_PLAY_MESSAGE = f"""
**Hello Racer!**

*Please read the following carefully.*

You have limited time to record and play the seed included below. You have {ASYNC_RACE_SUBMIT_TIME_LIMIT_M:d} minutes from the sending of this message to setup your game, setup your recording software, and start a run. Upon completion of your seed, immediately return here to submit your time.

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

After sumbitting your time, you will have {ASYNC_RACE_SUBMIT_VOD_TIME_LIMIT_M:d} minutes to upload an unlisted YouTube video of your run.

Good Luck!

"""

ASYNC_RACE_FINISH_MESSAGE = """Congratulations on completing your run in %s!

You now have %d minutes to upload an **UNLISTED** YouTube video of your run and submit the url here.

When you are ready, please submit the link like so:

```
!vod https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

"""

ASYNC_RACE_DATA_FILENAME = "async_race_data.json"

class AsyncRace:
    players: list
    name: str
    permalink: str
    def __init__(self, name: str, permalink: str):
        self.players = list()
        self.name = name
        self.permalink = permalink
    
    def add_player(self, username: str):
        self.players.append(AsyncRacePlayer(username))
    
    def turnover(self, permalink: str):
        for i, _ in enumerate(self.players):
            self.players[i].reset()

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
                "dnf":player.dnf,
            })

        race = {
            "name" : self.name,
            "permalink" : self.permalink,
            "players" : players
        }

        return race

    @staticmethod
    def from_json(json_data: dict):
        race = AsyncRace(json_data["name"], json_data["permalink"])
        for player_json in json_data["players"]:
            player = AsyncRacePlayer(player_json["username"])
            player.state = async_race_state_from_string(player_json["state"])
            player.time = player_json["time"]
            player.vod_url = player_json["vod_url"]
            player.play_timestamp = player_json["play_timestamp"]
            player.time_timestamp = player_json["time_timestamp"]
            player.vod_timestamp = player_json["vod_timestamp"]
            player.dnf = player_json["dnf"]
            race.players.append(player)
        return race

class AsyncRacePlayer:
    username: str
    state: AsyncRacerState
    vod_url: str
    time: int
    play_timestamp: int
    time_timestamp: int
    vod_timestamp: int
    dnf: bool

    def __init__(self, username: str):
        self.username = username
        self.state = AsyncRacerState.NOT_STARTED
        self.vod_url = None
        self.time = None
        self.play_timestamp = None
        self.time_timestamp = None
        self.vod_timestamp = None
        self.dnf = False

    def reset(self):
        self.__init__(self.username)

    def is_active(self):
        return self.state == AsyncRacerState.RACING or self.state == AsyncRacerState.SUBMITTED_TIME

async_races = list()

def async_race_idx_from_name(name: str):
    for i, race in enumerate(async_races):
        if race.name.lower() == name.lower():
            return i
    return None

def async_player_idx_from_name(idx, name: str):
    name = name.lower()
    for i, player in enumerate(async_races[idx].players):
        if player.username.lower() == name:
            return i
    return None

def async_race_usage(is_async_race_admin: bool):
    if not is_async_race_admin is None and is_async_race_admin:
        return ASYNC_RACE_USAGE_ADMIN
    return ASYNC_RACE_USAGE

def async_race_get_active_player(player_name: str):
    for race_idx, race in enumerate(async_races):
        for player_idx, player in enumerate(race.players):
            if player.username == player_name and player.is_active():
                return (race_idx, player_idx)
    return None, None

def async_race_string_to_time(string: str):
    try:
        string = string.split(":")
        return int(string[0])*60*60 + int(string[1])*60 + int(string[2])
    except Exception:
        return None

def format_seconds_to_hhmmss(seconds: int):
    hours = seconds // (60*60)
    seconds %= (60*60)
    minutes = seconds // 60
    seconds %= 60
    return "%02i:%02i:%02i" % (hours, minutes, seconds)

def results_sort(x: AsyncRacePlayer):
    if x.dnf:
        return 999999999999
    return x.time

async_racing_results_channel = None
async def async_race_announce_results(race: AsyncRace):
    global async_racing_results_channel
    if async_racing_results_channel is None:
        return

    if len(race.players) == 0:
        return

    # sort by time
    players = sorted(race.players, key=results_sort, reverse=True)
    
    title = "%s Results" % race.name
    embed = discord.Embed(title=title, description="Thanks for playing!", color=0x00ff00)
    for player in players:
        name = player.username.split("#")[0]

        time = "DNF"
        if not player.time is None:
            time = format_seconds_to_hhmmss(player.time)

        if not player.vod_url is None:
            vod = "[%s](%s)" % (time, player.vod_url)
        else:
            vod = time

        embed.add_field(name=name, value=vod, inline=False)
    await async_racing_results_channel.send(embed=embed)

    # notify admin of ill-play
    ill_play = list()
    for player in race.players:
        if player.state == AsyncRacerState.NOT_STARTED:
            ill_play.append("%s never started their run." % player.username)
        elif player.state == AsyncRacerState.SUBMITTED_TIME:
            ill_play.append("%s completed a run, but did not submit a VoD." % player.username)
        elif player.dnf and player.vod_url is None:
            ill_play.append("%s forfeit, but did not submit a VoD." % player.username)
        
        if (not player.time_timestamp is None) and (not player.play_timestamp is None) and (not player.time is None):
            diff = (player.time_timestamp - player.play_timestamp) - (ASYNC_RACE_SUBMIT_TIME_LIMIT_M*60 + player.time)
            if diff > 0:
                ill_play.append("%s Submitted their time %d minutes late." % (player.username, (diff/60)))
        
        if (not player.vod_timestamp is None) and (not player.time_timestamp is None):
            diff =  (player.vod_timestamp - player.time_timestamp) - ASYNC_RACE_SUBMIT_VOD_TIME_LIMIT_M*60
            if diff > 0:
                ill_play.append("%s Submitted their VoD %d minutes late." % (player.username, (diff/60)))

    if len(ill_play) != 0:
        await async_race_admin_msg(async_race_admin_ping() + (", %s finished with the following ill-play:" % race.name) + "\n".join(ill_play))

async_racing_admin_channel = None
async def async_race_admin_msg(msg: str):
    global async_racing_admin_channel
    if async_racing_admin_channel is None:
        return
    await async_racing_admin_channel.send(msg)

async_race_admin_roll_id = None
def async_race_set_admin_roll_id(id: int):
    global async_race_admin_roll_id
    if id is None:
        return
    async_race_admin_roll_id = id

def async_race_admin_ping():
    if async_race_admin_roll_id is None:
        return "Async Race Admins,"
    return "<@&%d>" % async_race_admin_roll_id

def async_race_get_admin_channel():
    global async_racing_admin_channel
    return async_racing_admin_channel

def async_race_set_admin_channel(channel: discord.TextChannel):
    global async_racing_admin_channel
    if channel is None:
        return
    async_racing_admin_channel = channel

def async_race_get_results_channel():
    global async_racing_results_channel
    return async_racing_results_channel

def async_race_set_results_channel(channel: discord.TextChannel):
    global async_racing_results_channel
    if channel is None:
        return
    async_racing_results_channel = channel

def read_state_from_disk():
    global async_races
    try:
        if os.path.exists(ASYNC_RACE_DATA_FILENAME):
            with open(ASYNC_RACE_DATA_FILENAME, "r") as f:
                text = f.read()
                races = json.loads(text)
                for race in races:
                    async_races.append(AsyncRace.from_json(race))
    except Exception as e:
        logging.exception(f"Exception when handling disk read: {e}")

async def async_race_dm_cmd(message: discord.Message):
    global async_races
    content = message.content.lower()
    author_name = message.author.name + "#" + message.author.discriminator
    if not content.startswith("!"):
        return

    try:
        (race_idx, player_idx) = async_race_get_active_player(author_name)
        if race_idx is None:
            await message.author.send("*You aren't in any active race currently.*")
            return
        
        race_name = async_races[race_idx].name
        player_name = author_name
        
        state = async_races[race_idx].players[player_idx].state
        command = content.split(" ")

        if not async_races[race_idx].players[player_idx].vod_url is None:
            await message.author.send("*Your race is complete. Please wait for results to be announced in #async-racing-results before discussing the seed.*")
            return

        if command[0] == "!finish":
            if state == AsyncRacerState.RACING:
                t = async_race_string_to_time(command[1])
                async_races[race_idx].players[player_idx].state = AsyncRacerState.SUBMITTED_TIME
                async_races[race_idx].players[player_idx].time = t
                async_races[race_idx].players[player_idx].time_timestamp = time.time()
                diff = (async_races[race_idx].players[player_idx].time_timestamp - async_races[race_idx].players[player_idx].play_timestamp) - (ASYNC_RACE_SUBMIT_TIME_LIMIT_M*60 + t)
                await message.author.send(ASYNC_RACE_FINISH_MESSAGE % (format_seconds_to_hhmmss(t), ASYNC_RACE_SUBMIT_VOD_TIME_LIMIT_M))
                if diff > 0:
                    await message.author.send("**Warning: You have submitted your time %d minutes late. While this does not automatically disqualify your run, the race organizer has been notified of this infraction.**" % (diff/60))
                    await async_race_admin_msg("%s, *%s finished their run of '%s' in ||%s||, but they submitted the time %d minutes late!*" % (async_race_admin_ping(), player_name, race_name, format_seconds_to_hhmmss(t), (diff/60)))
                else:
                    await async_race_admin_msg("*%s finished their run of '%s' in ||%s||.*" % (player_name, race_name, format_seconds_to_hhmmss(t)))
            else:
                await message.author.send("*You already submitted your time for this seed. Use the `!vod <url>` command to submit your vod.*")
                return
        elif command[0] == "!dnf":
            if state == AsyncRacerState.RACING or state == AsyncRacerState.SUBMITTED_TIME:
                async_races[race_idx].players[player_idx].state = AsyncRacerState.SUBMITTED_TIME
                async_races[race_idx].players[player_idx].time = None
                async_races[race_idx].players[player_idx].dnf = True
                async_races[race_idx].players[player_idx].time_timestamp = time.time()
                await message.author.send("*Thanks for letting me know. You are highly encouraged to still upload and submit a vod of your failed run using the `!vod <url>` command. Multiple DNFs without video proof can look like cheating.*")
                await async_race_admin_msg("*%s forfeit their run of '%s'.*" % (player_name, race_name))
            else:
                raise Exception("Player tried to DNF from a unhandled state")
        elif command[0] == "!vod":
            if state != AsyncRacerState.SUBMITTED_TIME:
                await message.author.send("*Please submit your time first with the `!finish hh:mm:ss` command first.*")
                return
            else:
                vod_url = message.content.split(" ")[1] # this is case sensitive because youtube links are case sensitive
                async_races[race_idx].players[player_idx].state = AsyncRacerState.SUBMITTED_VOD
                async_races[race_idx].players[player_idx].vod_url = vod_url
                async_races[race_idx].players[player_idx].vod_timestamp = time.time()
                diff = (async_races[race_idx].players[player_idx].vod_timestamp - async_races[race_idx].players[player_idx].time_timestamp) - ASYNC_RACE_SUBMIT_VOD_TIME_LIMIT_M*60
                await message.author.send("*Your run has been recorded. Please wait for results to be announced in #async-racing-results before discussing the seed or making your VOD public.*")
                if diff > 0:
                    await message.author.send("**Warning: You have submitted your VOD %d minutes late. While this does not automatically disqualify your run, the race organizer has been notified of this infraction.**" % (diff/60))
                    await async_race_admin_msg("*%s, %s was %d minutes late submitting their VOD for '%s'.*" % (async_race_admin_ping(), player_name, (diff/60), race_name))
                else: 
                    await async_race_admin_msg("*%s submitted the vod of their run for '%s':*\n`%s`" % (player_name, race_name, vod_url))

            is_race_done = True
            for player in async_races[race_idx].players:
                if player.state != AsyncRacerState.SUBMITTED_VOD:
                    is_race_done = False
                    break
            if is_race_done:
                await async_race_admin_msg("*%s, All racers in '%s' have completed their run. Close submissions and announce results with `!asyncrace end %s`, or announce results and start a new race with the same players using `!asyncrace turnover %s <permalink>`*" % (async_race_admin_ping(), race_name, race_name, race_name))
        else:
            raise Exception(f"unknown dm command: {command[0]}")
    except Exception as e:
        logging.exception(f"Exception when handling direct message: {e}")
        await message.author.send(ASYNC_RACE_DM_USAGE)
        return

    async_race_update_disk()

async def async_race_guild_cmd(message: discord.Message):
    global async_races
    global async_race_admin_roll_id
    content = message.content.lower()
    author_name = message.author.name + "#" + message.author.discriminator
    if not content.startswith("!asyncrace"):
        return

    channel = message.channel
    if async_race_admin_roll_id is None:
        is_async_race_admin = False
    else:    
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
            for i, race in enumerate(async_races):
                if i != race_idx:
                    for player in race.players:
                        if player.username == player_name and (player.state == AsyncRacerState.RACING or player.state == AsyncRacerState.SUBMITTED_TIME):
                            await channel.send("*You have an unfinished race for '%s'! Go do that first!*" % race.name)
                            return
            
            state = async_races[race_idx].players[player_idx].state
            if state == AsyncRacerState.NOT_STARTED:
                await channel.send("*Starting your race... Please check your DMs.*")
            elif state == AsyncRacerState.RACING or state == AsyncRacerState.SUBMITTED_TIME:
                await channel.send("*You are supposed to be racing right now. Please check your DMs for a message from the bot, if you do not see a DM, please contact the race organizer ASAP to avoid penalization.*")
                return
            elif state == AsyncRacerState.SUBMITTED_VOD:
                await channel.send("*You already completed this seed! Good job!. Please wait for results to be posted in #async-racing-results.*")
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
                    if player.dnf:
                        out_message = out_message + " - DNF"
                    elif not player.time is None:
                        out_message = out_message + " - ||%s||" % format_seconds_to_hhmmss(player.time)
                    if not player.vod_url is None:
                        out_message = out_message + " - `%s`" % player.vod_url
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
            await channel.send("*Successfully updated '%s'. Players may now play the new seed with `!asyncrace play`.*" % race_name)
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
            raise Exception(f"unknown guild command: {command[0]}")
    except Exception as e:
        logging.exception(f"Exception when handling !asyncrace command: {e}")
        await channel.send(async_race_usage(is_async_race_admin))
        return

    async_race_update_disk()

async def async_race_cmd(message: discord.Message, guild: int):
    if message.guild is None:
        await async_race_dm_cmd(message)
    elif message.guild.id == guild:
        await async_race_guild_cmd(message)

def async_race_update_disk():
    with open(ASYNC_RACE_DATA_FILENAME, "w") as f:
        races = list()
        for race in async_races:
            races.append(race.to_json())
        f.write(json.dumps(races))
