#!/usr/bin/python3
# coding=utf-8
import sys
import threading
import time
import asyncio
import pydle
import json
import random
import logging.handlers
from os.path import dirname



formatter = logging.Formatter('[%(asctime)s][%(name)s][%(levelname)s] %(message)s')
logger = logging.getLogger('musicConversations')
logger.setLevel(logging.DEBUG)
logger.propagate = False
fh = logging.handlers.TimedRotatingFileHandler('debug.log', when='midnight', encoding='utf-8')
fh.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

pool = pydle.ClientPool()
current_milli_time = lambda: int(round(time.time() * 1000))

logger.info("Loading up....")

channelname = None
logins = None
inputfile = None
sentences = None
# read config values from file (db login etc)
try:
    f = open("musicconversations.cfg", "r")
    lines = f.readlines()
    for line in lines:
        if not line.startswith('#') and not line.startswith("\n"):
            name, value = line.split("=", maxsplit=1)
            value = str(value).strip("\n")
            logger.info("Reading config value '%s' = '<redacted>'", name)
            if name == "channel":
                channelname = value
            if name == "users":
                logins = json.loads(value)
            if name == "sentences":
                sentences = json.loads(value)
            if name == "inputfile":
                inputfile = value
            if name == "debug":
                if value == "True":
                    ch.setLevel(logging.DEBUG)
                    logger.warning("Debug console logging enabled, this may be spammy.")
    if channelname is None:
        logger.error("Channel Name not set. Please add it to the config file, with 'channel=<name>'")
        sys.exit(1)
    f.close()
except Exception:
    logger.error("Error reading config file (musicconversations.cfg), aborting.")
    logger.error(sys.exc_info())
    sys.exit(1)

logger.debug("Going to log in with the following users:")
for user in logins:
    logger.debug("%s", user['name'])

# From https://github.com/Shizmob/pydle/issues/35
class PrivMessageTagSupport(pydle.features.ircv3.TaggedMessageSupport):
    async def on_raw_privmsg(self, message):
        """ PRIVMSG command. """
        nick, metadata = self._parse_user(message.source)
        tags = message.tags
        target, message = message.params

        self._sync_user(nick, metadata)

        await self.on_message(target, nick, message, tags)
        if self.is_channel(target):
            await self.on_channel_message(target, nick, message, tags)
        else:
            await self.on_private_message(nick, message, tags)


# End Github code
BotClass = pydle.featurize(pydle.Client, PrivMessageTagSupport)

# From https://stackoverflow.com/a/3540315/3153319
def random_line(afile):
    line = next(afile)
    for num, aline in enumerate(afile, 2):
      if random.randrange(num): continue
      line = aline
    return line
# End SO code

class MusicConversationBot(BotClass):
    config = {}
    mychannel = ""

    def __init__(self, config, channel):
        super().__init__(config["username"])
        self.config = config
        self.mychannel = channel

    async def on_unknown(self, message):
        if str(message).find("WHISPER") > -1:
            await self.on_whisper(message)
            return
        if str(message).find("CLEARCHAT") > -1:
            await self.on_clearchat(message)
            return
        if str(message).find("HOSTTARGET") > -1:
            await self.on_hosttarget(message)
            return
        if str(message).find("USERSTATE") > -1:
            await self.on_userstate(message)
            return
        if str(message).find("ROOMSTATE") > -1:
            await self.on_roomstate(message)
            return
        if str(message).find("USERNOTICE") > -1:
            logger.debug("USERNOTICE - probably a sub: %s", str(message))
            return
        super().on_unknown(message)

    async def on_whisper(self, message):
        logger.debug("got whisper: %s", message)
        return
    async def on_hosttarget(self, message):
        logger.debug("got hosttarget: %s", message)
        return
    async def on_roomstate(self, message):
        logger.debug("got roomstate: %s", message)
        return
    async def on_userstate(self, message):
        logger.debug("got userstate: %s", message)
        return
    async def on_raw_421(self, message):
        # print("Got raw 421:" + str(message))
        # Ignore twitch not knowing WHOIS
        if str(message).find("WHOIS") > -1:
            return
        super().on_raw_421(message)

    async def on_clearchat(self, message):
        # print("Got clear chat message: " + str(message))
        nick, metadata = self._parse_user(message.source)
        tags = message.tags
        params = message.params
        logger.debug(
            "nick: {nick}; metadata: {metadata}; params: {params}; tags: {tags}".format(nick=nick, metadata=metadata,
                                                                                        params=params, tags=tags))
        if len(params) == 1:
            logger.info("Chat in %s has been cleared by a moderator.", params[0])
            return
        u = params[1]
        chan = params[0]
        reason = "" if "ban-reason" not in tags else str(tags["ban-reason"]).replace("\\s", " ")
        if "ban-duration" in tags.keys():
            duration = tags["ban-duration"]
            logger.warning("%s got timed out for %s seconds in %s for: %s", u, duration, chan, reason)
        else:
            logger.warning("%s got permanently banned from %s. Reason: %s", u, chan, reason)
        return

    async def on_capability_twitch_tv_membership_available(self, nothing=None):
        logger.debug("WE HAS TWITCH MEMBERSHIP AVAILABLE!")
        return True

    async def on_capability_twitch_tv_membership_enabled(self, nothing=None):
        logger.debug("WE HAS TWITCH MEMBERSHIP ENABLED!")
        return

    async def on_capability_twitch_tv_tags_available(self, nothing=None):
        logger.debug("WE HAS TAGS AVAILABLE!")
        return True

    async def on_capability_twitch_tv_tags_enabled(self, nothing=None):
        logger.debug("WE HAS TAGS ENABLED!")
        return

    async def on_capability_twitch_tv_commands_available(self, nothing=None):
        logger.debug("WE HAS COMMANDS AVAILABLE!")
        return True

    async def on_capability_twitch_tv_commands_enabled(self, nothing=None):
        logger.debug("WE HAS COMMANDS ENABLED!")
        return

    def start(self, password):
        self.pw = password
        logger.debug("Connecting...")
        pool.connect(self, "irc.twitch.tv", 6667, tls=False, password=password)

    async def on_connect(self):
        logger.info("%s Connected!", self.config["username"])
        await super().on_connect()
        logger.debug("Joining %s...", self.mychannel)
        await self.join(self.mychannel)

    async def doChat(self, message):
        await super().message(self.mychannel, message)

    async def on_disconnect(self, expected):
        logger.error("Disconnected, reconnecting. Was it expected? %s", str(expected))
        pool.connect(self, "irc.twitch.tv", 6667, tls=False, password=self.pw, reconnect=True)


    async def on_message(self, target, nick, message, tags=None):
        logger.debug("got message: %s", message)
        return

    async def on_channel_message(self, target, nick, message, tags=None):
        await super().on_channel_message(target, nick, message)
        return


bots = []

for login in logins:
    instance = MusicConversationBot({"username": login["name"]}, '#' + channelname)
    instance.start(login['token'])
    bots.append(instance)

thread = threading.Thread(target=pool.handle_forever)
thread.start()


from watchgod import awatch

async def processFileChanges():
        async for changes in awatch(dirname(inputfile)):
            for change in changes:
                if (change[1] == inputfile):
                    newInput = ""
                    with open(inputfile) as f:
                        newInput = f.readline()
                    logger.info("A new Input got detected: %s", newInput)
                    inputsentences = None
                    for setting in sentences:
                        if newInput in setting['inputs']:
                            inputsentences = setting['sentences']
                            break
                    if inputsentences != None:
                        for instance in bots:
                            await instance.doChat(random.choice(inputsentences))
                    else:
                        logger.debug("No sentences configured for %s", newInput)


logger.info("All loaded up and running!")

loop = asyncio.get_event_loop()
loop.run_until_complete(processFileChanges())